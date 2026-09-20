import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

from src.face.face_landmarks import FaceLandmarks
from src.eyes.eye_state import get_eye_landmarks
from src.eyes.ear import calculate_ear
from src.eyes.blink_detector import BlinkDetector
from src.drowsiness.closure_detector import ClosureDetector
from src.mouth.mouth_state import get_mouth_landmarks
from src.mouth.mar import calculate_mar

from src.distraction.head_pose import HeadPoseEstimator
from src.distraction.gaze import GazeEstimator
from src.distraction.context import ContextEngine

from src.risk.risk_engine import RiskEngine


MODEL_PATH = "models/face_landmarker.task"


class DriverMonitor:

    def __init__(self):

        self.cap = cv2.VideoCapture(0)

        if not self.cap.isOpened():
            raise RuntimeError(
                "Could not open webcam. Check camera index or permissions."
            )

        self.frame_width = int(
            self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        ) or 640

        self.frame_height = int(
            self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        ) or 480

        # Shared MediaPipe Face Landmarker
        base_options = mp_python.BaseOptions(
            model_asset_path=MODEL_PATH
        )

        options = mp_vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=mp_vision.RunningMode.VIDEO,
            num_faces=1,
        )

        self.landmarker = (
            mp_vision.FaceLandmarker
            .create_from_options(options)
        )

        # Person 1
        self.blink_detector = BlinkDetector()
        self.closure_detector = ClosureDetector()

        # Person 2
        self.pose_estimator = HeadPoseEstimator(
            self.frame_width,
            self.frame_height
        )

        self.gaze_estimator = GazeEstimator()
        self.context_engine = ContextEngine()

        # Person 3
        self.risk_engine = RiskEngine()

        # Mock driving state for milestone
        self.is_moving = False

        self.timestamp_ms = 0

    def process_frame(self, frame):

        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

        self.timestamp_ms += 33

        result = self.landmarker.detect_for_video(
            mp_image,
            self.timestamp_ms
        )

        # ------------------------------------------------
        # Default values
        # ------------------------------------------------

        eye_state = "OPEN"
        blink = False
        prolonged_closure = False
        closure_duration = 0.0
        mar = 0.0

        gaze_state = {
            "looking_away": False,
            "sustained_away": False,
            "face_lost_sustained": False,
            "away_duration_sec": 0.0,
        }

        phone_state = {
            "phone_visible": False,
            "confidence": 0.0,
            "box": None,
        }

        pose = None

        # ------------------------------------------------
        # Face detected
        # ------------------------------------------------

        if result.face_landmarks:

            landmarks = result.face_landmarks[0]

            # -------------------------
            # PERSON 1 - EYES
            # -------------------------

            left_eye, right_eye = get_eye_landmarks(
                landmarks
            )

            left_ear = calculate_ear(left_eye)
            right_ear = calculate_ear(right_eye)

            average_ear = (
                left_ear + right_ear
            ) / 2.0

            blink_result = self.blink_detector.update(
                average_ear
            )

            closure_result = self.closure_detector.update(
                average_ear
            )

            eye_state = blink_result["eye_state"]
            blink = blink_result["blink"]

            prolonged_closure = (
                closure_result["prolonged_closure"]
            )

            closure_duration = (
                closure_result["closure_duration_sec"]
            )

            # -------------------------
            # PERSON 1 - MOUTH
            # -------------------------

            mouth = get_mouth_landmarks(
                landmarks
            )

            mar = calculate_mar(mouth)

            # -------------------------
            # PERSON 2 - HEAD POSE
            # -------------------------

            pose = self.pose_estimator.estimate(
                landmarks
            )

            if pose is not None:

                pitch, yaw, roll = pose

                gaze_state = (
                    self.gaze_estimator.update(
                        pitch,
                        yaw
                    )
                )

            else:

                gaze_state = (
                    self.gaze_estimator.mark_face_lost()
                )

        else:

            gaze_state = (
                self.gaze_estimator.mark_face_lost()
            )

        # ------------------------------------------------
        # PERSON 2 - CONTEXT
        # ------------------------------------------------

        context_result = (
            self.context_engine.evaluate(
                self.is_moving,
                gaze_state,
                phone_state
            )
        )

        # ------------------------------------------------
        # PERSON 3 - RISK ENGINE
        # ------------------------------------------------

        risk_result = (
            self.risk_engine.calculate_risk(
                eye_state=eye_state,
                prolonged_closure=prolonged_closure,
                closure_duration=closure_duration,
                blink=blink,
                mar=mar,
                context_state=context_result[
                    "context_state"
                ],
                looking_away=context_result[
                    "looking_away"
                ],
                phone_visible=context_result[
                    "phone_visible"
                ],
            )
        )

        return {
            "eye_state": eye_state,
            "blink": blink,
            "prolonged_closure": prolonged_closure,
            "closure_duration": closure_duration,
            "ear": average_ear if result.face_landmarks else 0.0,
            "mar": mar,
            "pose": pose,
            "gaze": gaze_state,
            "context": context_result,
            "risk": risk_result,
            "phone": phone_state,
        }

    def draw_overlay(self, frame, data):

        y = 30

        lines = [
            f"Moving: {'ON' if self.is_moving else 'OFF'} [M]",
            f"EAR: {data['ear']:.2f}",
            f"Eye: {data['eye_state']}",
            f"Blink: {data['blink']}",
            f"Closure: {data['closure_duration']:.1f}s",
            f"Prolonged closure: {data['prolonged_closure']}",
            f"MAR: {data['mar']:.2f}",
        ]

        pose = data["pose"]

        if pose is not None:

            pitch, yaw, roll = pose

            lines.append(
                f"Pitch: {pitch:.1f}  "
                f"Yaw: {yaw:.1f}  "
                f"Roll: {roll:.1f}"
            )

        gaze = data["gaze"]

        lines.append(
            f"Looking away: {gaze['looking_away']}"
        )

        lines.append(
            f"Sustained away: {gaze['sustained_away']}"
        )

        lines.append(
            f"Context: "
            f"{data['context']['context_state']}"
        )

        lines.append(
            f"RISK: "
            f"{data['risk']['risk_score']:.1f}"
        )

        lines.append(
            f"LEVEL: "
            f"{data['risk']['risk_level']}"
        )

        for text in lines:

            cv2.putText(
                frame,
                text,
                (10, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )

            y += 27

        return frame

    def run(self):

        print(
            "Controls: "
            "M = toggle moving | "
            "Q = quit"
        )

        while True:

            ok, frame = self.cap.read()

            if not ok:
                break

            data = self.process_frame(frame)

            frame = self.draw_overlay(
                frame,
                data
            )

            cv2.imshow(
                "AI Driver Monitoring System",
                frame
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            elif key == ord("m"):
                self.is_moving = (
                    not self.is_moving
                )

        self.cap.release()
        self.landmarker.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":

    monitor = DriverMonitor()
    monitor.run()