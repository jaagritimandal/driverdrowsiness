import cv2
import time

from face.face_landmarks import FaceLandmarks


MODEL_PATH = "models/face_landmarker.task"

cap = cv2.VideoCapture(0)

detector = FaceLandmarks(MODEL_PATH)

start_time = time.time()

while True:
    ret, frame = cap.read()

    if not ret:
        break

    timestamp_ms = int((time.time() - start_time) * 1000)

    face_landmarks = detector.detect(frame, timestamp_ms)

    if face_landmarks:
        h, w, _ = frame.shape

        for landmark in face_landmarks:
            x = int(landmark.x * w)
            y = int(landmark.y * h)

            cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)

        cv2.putText(
            frame,
            "Face detected",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

    else:
        cv2.putText(
            frame,
            "No face detected",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2
        )

    cv2.imshow("Driver Face Landmarks", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()