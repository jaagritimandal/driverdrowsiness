"""
run_distraction_demo.py

Person 2's standalone 20%-milestone demo:

    Camera -> Face Landmarker -> head pose -> gaze state
                                            -> (optional) phone detection
                                            -> context engine -> on-screen state

Runs independently of Person 1's pipeline (own Face Landmarker instance
on the same webcam feed), so it needs no code from them to demo. Person 3
can later swap this for a shared landmark stream during integration.

Controls:
    M - toggle "moving" (mocked driving-state input, since there's no
        real vehicle telemetry for this milestone)
    P - toggle phone detection on/off (it's the heaviest model; off by
        default so head-pose/gaze runs smoothly on modest hardware)
    Q - quit

Author: Person 2 (Distraction & Context module)
"""

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

from src.distraction.head_pose import HeadPoseEstimator
from src.distraction.gaze import GazeEstimator
from src.distraction.context import ContextEngine

MODEL_PATH = "models/face_landmarker.task"  # shared model, same as Person 1's module


def build_landmarker():
    base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
    options = mp_vision.FaceLandmarkerOptions(
        base_options=base_options,
        running_mode=mp_vision.RunningMode.VIDEO,
        num_faces=1,
    )
    return mp_vision.FaceLandmarker.create_from_options(options)


def draw_overlay(frame, pose, gaze_state, phone_state, context_result, is_moving, phone_enabled):
    lines = [
        f"Moving (mock): {'ON' if is_moving else 'OFF'}  [M to toggle]",
    ]

    if pose is not None:
        pitch, yaw, roll = pose
        lines.append(f"Pitch: {pitch:.1f}  Yaw: {yaw:.1f}  Roll: {roll:.1f}")
        lines.append(
            f"Looking away: {gaze_state['looking_away']} "
            f"(sustained: {gaze_state['sustained_away']}, "
            f"{gaze_state['away_duration_sec']}s)"
        )
    else:
        lines.append(
            f"Pose: NOT DETECTED "
            f"(face lost {gaze_state.get('face_lost_duration_sec', 0.0)}s, "
            f"sustained: {gaze_state.get('face_lost_sustained', False)})"
        )

    if phone_enabled:
        lines.append(f"Phone visible: {phone_state['phone_visible']} (conf {phone_state['confidence']})  [P to toggle off]")
    else:
        lines.append("Phone detection: OFF  [P to toggle on]")

    lines.append(f"Context state: {context_result['context_state']}")

    for i, text in enumerate(lines):
        cv2.putText(
            frame, text, (10, 30 + i * 28),
            cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2, cv2.LINE_AA,
        )

    if phone_state.get("box"):
        x1, y1, x2, y2 = phone_state["box"]
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

    return frame


def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Could not open webcam. Check camera index/permissions.")

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480

    landmarker = build_landmarker()
    pose_estimator = HeadPoseEstimator(frame_width, frame_height)
    gaze_estimator = GazeEstimator()
    context_engine = ContextEngine()

    phone_detector = None
    phone_enabled = False
    is_moving = False

    frame_timestamp_ms = 0

    print("Controls: M = toggle moving (mock) | P = toggle phone detection | Q = quit")

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        # NOTE: no horizontal flip here -- flipping before landmark detection
        # mirrors the face MediaPipe sees, which breaks the head-pose math
        # (landmark indices no longer match the unflipped 3D face model).
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        frame_timestamp_ms += 33  # ~30fps stand-in timestamp for VIDEO mode
        result = landmarker.detect_for_video(mp_image, frame_timestamp_ms)

        pose = None

        if result.face_landmarks:
            landmarks = result.face_landmarks[0]
            pose = pose_estimator.estimate(landmarks)

        if pose is not None:
            pitch, yaw, _roll = pose
            gaze_state = gaze_estimator.update(pitch, yaw)
        else:
            # No face landmarks, or solvePnP couldn't resolve a pose --
            # either way the driver has turned far enough away that we
            # can't measure an angle. That's not "nothing to report", it's
            # itself a distraction signal once it persists (see gaze.py).
            gaze_state = gaze_estimator.mark_face_lost()

        phone_state = {"phone_visible": False, "confidence": 0.0, "box": None}
        if phone_enabled:
            if phone_detector is None:
                from src.distraction.phone_detector import PhoneDetector
                phone_detector = PhoneDetector()
            phone_state = phone_detector.detect(frame)

        context_result = context_engine.evaluate(is_moving, gaze_state, phone_state)

        frame = draw_overlay(frame, pose, gaze_state, phone_state, context_result, is_moving, phone_enabled)
        cv2.imshow("Person 2 - Distraction & Context", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("m"):
            is_moving = not is_moving
        elif key == ord("p"):
            phone_enabled = not phone_enabled

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()