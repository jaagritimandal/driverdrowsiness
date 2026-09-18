import cv2
import time

from src.face.face_landmarks import FaceLandmarks
from src.mouth.mouth_state import get_mouth_landmarks
from src.mouth.mar import calculate_mar


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
        mouth = get_mouth_landmarks(face_landmarks)

        mar = calculate_mar(mouth)

        cv2.putText(
            frame,
            f"MAR: {mar:.2f}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 255, 0),
            2
        )

        for landmark in mouth:
            h, w, _ = frame.shape

            x = int(landmark.x * w)
            y = int(landmark.y * h)

            cv2.circle(frame, (x, y), 3, (255, 0, 0), -1)

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

    cv2.imshow("MAR Test", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()