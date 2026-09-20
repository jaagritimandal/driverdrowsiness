"""
phone_detector.py

Detects a visible phone in the camera frame using a pretrained YOLOv8n
model, filtered down to the COCO "cell phone" class.

Design choice (for documentation): YOLOv8n (nano) was chosen over
larger variants (s/m/l/x) purely for inference speed -- this needs to
run in real time alongside face landmarking and head-pose estimation
on the same frame, and nano is the lightest tradeoff of speed vs.
accuracy in the YOLOv8 family. No custom training was needed since
"cell phone" is already a COCO class the pretrained weights recognize.

This is intentionally a stretch-goal module per the milestone doc --
if it isn't ready, the rest of the pipeline (head pose + gaze) still
stands alone as the 20% deliverable.

Author: Person 2 (Distraction & Context module)
"""

from ultralytics import YOLO

COCO_CELL_PHONE_CLASS_ID = 67  # "cell phone" in the default COCO class list


class PhoneDetector:
    def __init__(self, model_name: str = "yolov8n.pt", confidence: float = 0.55):
        """
        model_name: pretrained YOLOv8 checkpoint. Downloads automatically
                    on first run via the ultralytics package.
        confidence: minimum detection confidence to count as "phone visible".
        """
        self.model = YOLO(model_name)
        self.confidence = confidence

    def detect(self, frame):
        """
        Runs inference on a single BGR frame (as returned by cv2.VideoCapture).
        Returns a dict: {"phone_visible": bool, "confidence": float, "box": (x1,y1,x2,y2) | None}
        """
        results = self.model(frame, verbose=False)[0]

        best_conf = 0.0
        best_box = None

        for box in results.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])

            if cls_id == COCO_CELL_PHONE_CLASS_ID and conf >= self.confidence:
                if conf > best_conf:
                    best_conf = conf
                    best_box = tuple(map(int, box.xyxy[0]))

        return {
            "phone_visible": best_box is not None,
            "confidence": round(best_conf, 2),
            "box": best_box,
        }