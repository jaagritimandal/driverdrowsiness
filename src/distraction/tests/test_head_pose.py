"""
test_head_pose.py

Sanity check for HeadPoseEstimator using synthetic landmark points that
approximate a face looking straight at the camera. Not a substitute for
live webcam testing -- just confirms solvePnP runs and returns a pose
near (0, 0, 0) for a frontal face.

Run with: python -m tests.test_head_pose
"""

import numpy as np
import cv2

from src.distraction.head_pose import (
    HeadPoseEstimator,
    MODEL_POINTS_3D,
    NOSE_TIP,
    CHIN,
    LEFT_EYE_LEFT_CORNER,
    RIGHT_EYE_RIGHT_CORNER,
    LEFT_MOUTH_CORNER,
    RIGHT_MOUTH_CORNER,
)

LANDMARK_ORDER = [
    NOSE_TIP, CHIN, LEFT_EYE_LEFT_CORNER,
    RIGHT_EYE_RIGHT_CORNER, LEFT_MOUTH_CORNER, RIGHT_MOUTH_CORNER,
]


class FakeLandmark:
    """Mimics the .x/.y attributes MediaPipe landmark objects expose."""
    def __init__(self, x, y):
        self.x = x
        self.y = y


def build_frontal_face_landmarks(frame_width=640, frame_height=480):
    """
    Builds a 468-length landmark list with only the 6 indices used by
    HeadPoseEstimator set. Rather than hand-guessing normalized
    coordinates (which can accidentally create a coplanar point set
    that solvePnP resolves ambiguously -- a known PnP failure mode),
    this projects the estimator's own 3D model points through a
    straight-on camera to get image points that are geometrically
    consistent with a true frontal pose.
    """
    focal_length = frame_width
    center = (frame_width / 2, frame_height / 2)
    camera_matrix = np.array([
        [focal_length, 0, center[0]],
        [0, focal_length, center[1]],
        [0, 0, 1],
    ], dtype=np.float64)
    dist_coeffs = np.zeros((4, 1))

    # Identity rotation, pushed back along Z so the model is in front
    # of the camera -- i.e. a perfectly frontal face.
    rotation_vector = np.zeros((3, 1))
    translation_vector = np.array([[0.0], [0.0], [600.0]])

    image_points, _ = cv2.projectPoints(
        MODEL_POINTS_3D, rotation_vector, translation_vector,
        camera_matrix, dist_coeffs,
    )
    image_points = image_points.reshape(-1, 2)

    landmarks = [FakeLandmark(0.0, 0.0) for _ in range(468)]
    for idx, (x, y) in zip(LANDMARK_ORDER, image_points):
        landmarks[idx] = FakeLandmark(x / frame_width, y / frame_height)
    return landmarks


def test_frontal_face_pose_near_zero():
    estimator = HeadPoseEstimator(frame_width=640, frame_height=480)
    landmarks = build_frontal_face_landmarks()

    pose = estimator.estimate(landmarks)
    assert pose is not None, "solvePnP failed to return a pose"

    pitch, yaw, roll = pose
    print(f"Frontal face pose -> pitch: {pitch:.1f}, yaw: {yaw:.1f}, roll: {roll:.1f}")

    # Loose bounds -- this is a synthetic/approximate face, not a
    # calibrated ground truth, so we just check it's in a sane range
    # for a roughly-frontal face rather than asserting near-exact zero.
    assert abs(yaw) < 30, f"Unexpected yaw for frontal face: {yaw}"
    assert abs(roll) < 30, f"Unexpected roll for frontal face: {roll}"


if __name__ == "__main__":
    test_frontal_face_pose_near_zero()
    print("test_head_pose passed.")
