import cv2
import time

from src.face.face_landmarks import FaceLandmarks
from src.distraction.eye_gaze import (
    get_eye_gaze,
    LEFT_IRIS,
    RIGHT_IRIS,
)
MODEL_PATH = "models/face_landmarker.task"

cap = cv2.VideoCapture(0)

detector = FaceLandmarks(MODEL_PATH)

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

        gaze_state = get_eye_gaze(
            face_landmarks
        )

        gaze = gaze_state["gaze"]

        cv2.putText(
            frame,
            f"Gaze: {gaze}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"Left ratio: {gaze_state['left_ratio']}",
            (20, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"Right ratio: {gaze_state['right_ratio']}",
            (20, 105),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

        h, w, _ = frame.shape

        for index in [*LEFT_IRIS, *RIGHT_IRIS]:
            landmark = face_landmarks[index]

            x = int(landmark.x * w)
            y = int(landmark.y * h)

            cv2.circle(
                frame,
                (x, y),
                3,
                (255, 0, 0),
                -1
            )

    else:

        cv2.putText(
            frame,
            "No face detected",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 0, 255),
            2
        )

    cv2.imshow(
        "Eye Gaze Test",
        frame
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()