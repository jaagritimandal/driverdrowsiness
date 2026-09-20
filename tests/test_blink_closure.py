import cv2
import time

from src.face.face_landmarks import FaceLandmarks
from src.eyes.eye_state import get_eye_landmarks
from src.eyes.ear import calculate_ear
from src.eyes.blink_detector import BlinkDetector
from src.drowsiness.closure_detector import ClosureDetector


MODEL_PATH = "models/face_landmarker.task"

cap = cv2.VideoCapture(0)

detector = FaceLandmarks(MODEL_PATH)
blink_detector = BlinkDetector()
closure_detector = ClosureDetector()

start_time = time.time()

while True:
    ret, frame = cap.read()

    if not ret:
        print("Could not access webcam.")
        break

    timestamp_ms = int(
        (time.time() - start_time) * 1000
    )

    face_landmarks = detector.detect(
        frame,
        timestamp_ms
    )

    if face_landmarks:

        left_eye, right_eye = get_eye_landmarks(
            face_landmarks
        )

        left_ear = calculate_ear(left_eye)
        right_ear = calculate_ear(right_eye)

        average_ear = (
            left_ear + right_ear
        ) / 2

        blink_state = blink_detector.update(
            average_ear
        )

        closure_state = closure_detector.update(
            average_ear
        )

        cv2.putText(
            frame,
            f"EAR: {average_ear:.2f}",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"Eye: {blink_state['eye_state']}",
            (20, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"Blink count: {blink_state['blink_count']}",
            (20, 105),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"Closure: {closure_state['closure_duration_sec']:.2f}s",
            (20, 140),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"Prolonged: {closure_state['prolonged_closure']}",
            (20, 175),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255)
            if closure_state["prolonged_closure"]
            else (0, 255, 0),
            2
        )

    else:

        cv2.putText(
            frame,
            "No face detected",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 0, 255),
            2
        )

    cv2.imshow(
        "Blink + Drowsiness Test",
        frame
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()