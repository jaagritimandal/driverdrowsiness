import cv2
import time

from src.face.face_landmarks import FaceLandmarks
from src.eyes.eye_state import get_eye_landmarks
from src.eyes.ear import calculate_ear

MODEL_PATH = "models/face_landmarker.task"

cap = cv2.VideoCapture(0)
detector = FaceLandmarks(MODEL_PATH)
start_time = time.time()

while True:
    ret, frame = cap.read()

    if not ret:
        print("Could not access webcam.")
        break

    timestamp_ms = int((time.time() - start_time) * 1000)

    face_landmarks = detector.detect(frame, timestamp_ms)

    if face_landmarks:
        left_eye, right_eye = get_eye_landmarks(face_landmarks)

        left_ear = calculate_ear(left_eye)
        right_ear = calculate_ear(right_eye)
        average_ear = (left_ear + right_ear) / 2

        cv2.putText(
            frame,
            f"Left EAR: {left_ear:.2f}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"Right EAR: {right_ear:.2f}",
            (20, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"Average EAR: {average_ear:.2f}",
            (20, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        h, w, _ = frame.shape

        # Draw left eye landmarks
        for landmark in left_eye:
            x = int(landmark.x * w)
            y = int(landmark.y * h)

            cv2.circle(
                frame,
                (x, y),
                4,
                (255, 0, 0),
                -1
            )

        # Draw right eye landmarks
        for landmark in right_eye:
            x = int(landmark.x * w)
            y = int(landmark.y * h)

            cv2.circle(
                frame,
                (x, y),
                4,
                (255, 0, 0),
                -1
            )

    else:
        cv2.putText(
            frame,
            "No face detected",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )

    cv2.imshow("EAR Test", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
