import cv2
import mediapipe as mp


class FaceLandmarks:
    def __init__(self, model_path):
        self.base_options = mp.tasks.BaseOptions(
            model_asset_path=model_path
        )

        self.options = mp.tasks.vision.FaceLandmarkerOptions(
            base_options=self.base_options,
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )

        self.detector = mp.tasks.vision.FaceLandmarker.create_from_options(
            self.options
        )

    def detect(self, frame, timestamp_ms):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

        result = self.detector.detect_for_video(
            mp_image,
            timestamp_ms
        )

        if result.face_landmarks:
            return result.face_landmarks[0]

        return None