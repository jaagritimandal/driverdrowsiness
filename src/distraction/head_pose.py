"""
head_pose_estimator.py

Estimates head pose (pitch, yaw, roll) from MediaPipe Face Landmarker
output using OpenCV's solvePnP against a generic 3D face model.

Consumes the same landmark output as face/face_landmarks.py (Person 1's
module) so this can be dropped straight into the shared pipeline:

    Camera -> Face Landmarker -> landmarks -> HeadPoseEstimator -> pitch/yaw/roll

Author: Person 2 (Distraction & Context module)
"""

import numpy as np
import cv2

# --- Landmark indices used from the 468-point MediaPipe face mesh ---
# These six points correspond to a stable subset of facial geometry that
# maps well onto a generic 3D face model for solvePnP.
NOSE_TIP = 1
CHIN = 152
LEFT_EYE_LEFT_CORNER = 263   # subject's own left eye (appears on image-right in a non-mirrored frame)
RIGHT_EYE_RIGHT_CORNER = 33  # subject's own right eye (appears on image-left)
LEFT_MOUTH_CORNER = 291
RIGHT_MOUTH_CORNER = 61

LANDMARK_INDICES = [
    NOSE_TIP,
    CHIN,
    LEFT_EYE_LEFT_CORNER,
    RIGHT_EYE_RIGHT_CORNER,
    LEFT_MOUTH_CORNER,
    RIGHT_MOUTH_CORNER,
]

# Generic 3D face model points (in an arbitrary head-centered coordinate
# system, units are irrelevant since only relative geometry matters for
# solvePnP). Values are a commonly used approximation of average face
# geometry -- fine for a prototype; not a calibrated/personalized model.
#
# BUGFIX: the eye/mouth corner X-signs were mirrored relative to where
# those landmarks actually project in an unflipped frame (e.g. landmark 263,
# "subject's own left eye" -- which the comments below correctly note
# appears on image-RIGHT -- was assigned a NEGATIVE (image-left) X). A real
# face's landmarks don't match a horizontally-mirrored 3D model, and
# solvePnP was compensating for that mismatch with an unstable ~180 deg
# roll, which is exactly the "Roll: -176.1" style readings seen on real
# camera footage even after the pitch/yaw/roll axis-label fix. Verified by
# reproducing that ~180 deg roll from a synthetic, correctly-built face
# solved against this mirrored model, and confirming it disappears once the
# X-signs below match the landmark comments.
MODEL_POINTS_3D = np.array([
    (0.0, 0.0, 0.0),          # Nose tip
    (0.0, -330.0, -65.0),     # Chin
    (225.0, 170.0, -135.0),   # Left eye left corner   (263, lands image-right)
    (-225.0, 170.0, -135.0),  # Right eye right corner (33,  lands image-left)
    (150.0, -150.0, -125.0),  # Left mouth corner      (291, lands image-right)
    (-150.0, -150.0, -125.0), # Right mouth corner     (61,  lands image-left)
], dtype=np.float64)


class HeadPoseEstimator:
    """
    Estimates head pitch/yaw/roll from face landmarks, frame by frame.

    Usage:
        estimator = HeadPoseEstimator(frame_width, frame_height)
        pitch, yaw, roll = estimator.estimate(landmarks)
    """

    def __init__(self, frame_width: int, frame_height: int):
        self.frame_width = frame_width
        self.frame_height = frame_height

        # Approximate camera intrinsics. Good enough for a prototype;
        # a proper calibration would replace this with measured values.
        focal_length = frame_width
        center = (frame_width / 2, frame_height / 2)
        self.camera_matrix = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1],
        ], dtype=np.float64)

        # Assume no lens distortion.
        self.dist_coeffs = np.zeros((4, 1))

    def _extract_image_points(self, landmarks):
        """
        landmarks: list/array of (x, y) or (x, y, z) normalized [0,1]
        coordinates as returned by MediaPipe Face Landmarker, indexed
        the same way face/face_landmarks.py exposes them.
        """
        points = []
        for idx in LANDMARK_INDICES:
            lm = landmarks[idx]
            x = lm.x * self.frame_width if hasattr(lm, "x") else lm[0] * self.frame_width
            y = lm.y * self.frame_height if hasattr(lm, "y") else lm[1] * self.frame_height
            points.append((x, y))
        return np.array(points, dtype=np.float64)

    def estimate(self, landmarks):
        """
        Returns (pitch, yaw, roll) in degrees, or None if solvePnP fails.
        """
        image_points = self._extract_image_points(landmarks)

        # solvePnP's default ITERATIVE solver can lock onto a flipped
        # (mirror-image) solution for near-planar point sets like a face --
        # same 2D projection, wrong 3D orientation. Get a rough initial
        # guess with EPnP, then refine it with ITERATIVE.
        success_initial, rvec_initial, tvec_initial = cv2.solvePnP(
            MODEL_POINTS_3D,
            image_points,
            self.camera_matrix,
            self.dist_coeffs,
            flags=cv2.SOLVEPNP_EPNP,
        )

        if not success_initial:
            return None

        rotation_vector, translation_vector = self._refine_disambiguated(
            image_points, rvec_initial, tvec_initial
        )
        if rotation_vector is None:
            return None

        rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
        pitch, yaw, roll = self._rotation_matrix_to_euler(rotation_matrix)

        # Final sanity check: a driver's head can't rotate past ~90 deg on
        # any axis and still have MediaPipe report landmarks for it at all
        # (confirmed empirically -- pose estimation reports "not detected"
        # well before that). So a reading beyond +-90 here isn't a real
        # head position, it's the near-planar PnP ambiguity slipping past
        # the disambiguation above (observed on real camera footage: e.g.
        # pitch reported as -169 while looking down at a phone in the lap,
        # a real pitch of roughly 10-15 deg). Unwrap it back into range --
        # this is a no-op for every angle that's already physically valid.
        pitch, yaw, roll = (self._unwrap_to_physical_range(a) for a in (pitch, yaw, roll))

        return pitch, yaw, roll

    def _refine_disambiguated(self, image_points, rvec_initial, tvec_initial):
        """
        Refines the EPnP guess with ITERATIVE, AND separately refines a
        second candidate seeded 180 deg away about the local X axis from
        that same guess. Near-planar point sets like a face can have two
        locally-optimal solvePnP solutions with very similar reprojection
        error on paper, but only one is geometrically real -- picking
        whichever candidate actually fits the real 2D landmarks better
        (lower reprojection error) is the standard way to resolve this,
        rather than trusting a single refine to have landed on the right
        one.
        """
        success_a, rvec_a, tvec_a = cv2.solvePnP(
            MODEL_POINTS_3D, image_points, self.camera_matrix, self.dist_coeffs,
            rvec=rvec_initial, tvec=tvec_initial,
            useExtrinsicGuess=True, flags=cv2.SOLVEPNP_ITERATIVE,
        )

        R_initial, _ = cv2.Rodrigues(rvec_initial)
        flip_about_x = np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1]], dtype=np.float64)
        rvec_alt_seed, _ = cv2.Rodrigues(flip_about_x @ R_initial)
        success_b, rvec_b, tvec_b = cv2.solvePnP(
            MODEL_POINTS_3D, image_points, self.camera_matrix, self.dist_coeffs,
            rvec=rvec_alt_seed, tvec=tvec_initial,
            useExtrinsicGuess=True, flags=cv2.SOLVEPNP_ITERATIVE,
        )

        candidates = []
        if success_a:
            candidates.append((self._reprojection_error(image_points, rvec_a, tvec_a), rvec_a, tvec_a))
        if success_b:
            candidates.append((self._reprojection_error(image_points, rvec_b, tvec_b), rvec_b, tvec_b))

        if not candidates:
            return None, None

        candidates.sort(key=lambda c: c[0])
        _, best_rvec, best_tvec = candidates[0]
        return best_rvec, best_tvec

    def _reprojection_error(self, image_points, rvec, tvec):
        projected, _ = cv2.projectPoints(
            MODEL_POINTS_3D, rvec, tvec, self.camera_matrix, self.dist_coeffs
        )
        return float(np.mean(np.linalg.norm(projected.reshape(-1, 2) - image_points, axis=1)))

    @staticmethod
    def _unwrap_to_physical_range(angle_deg):
        if angle_deg > 90:
            return angle_deg - 180
        if angle_deg < -90:
            return angle_deg + 180
        return angle_deg

    @staticmethod
    def _rotation_matrix_to_euler(R):
        """
        Converts a rotation matrix to pitch/yaw/roll in degrees.

        BUGFIX: the three components extracted from R correspond to rotation
        about the X, Y and Z axes respectively (the standard OpenCV
        rotation-matrix-to-Euler decomposition). In head-pose terms that
        maps to PITCH (X), YAW (Y), ROLL (Z) -- the previous version of this
        function returned them mislabeled as (pitch=Y, yaw=Z, roll=X), which
        silently fed the wrong angle into every downstream threshold check.
        Verified against synthetic landmarks built from known, ground-truth
        rotations before and after this fix.
        """
        sy = np.sqrt(R[0, 0] ** 2 + R[1, 0] ** 2)
        singular = sy < 1e-6

        if not singular:
            yaw = np.arctan2(-R[2, 0], sy)
            roll = np.arctan2(R[1, 0], R[0, 0])
            pitch = np.arctan2(R[2, 1], R[2, 2])
        else:
            yaw = np.arctan2(-R[2, 0], sy)
            roll = 0
            pitch = np.arctan2(-R[1, 2], R[1, 1])

        return (np.degrees(pitch), np.degrees(yaw), np.degrees(roll))