# Person 2 — Distraction & Context Module

## What's here

```
src/
├── head_pose/head_pose_estimator.py   # pitch/yaw/roll via solvePnP
├── gaze/gaze_estimator.py             # sustained "looking away" state
├── phone/phone_detector.py            # YOLOv8n cell-phone detection
├── context/context_engine.py          # combines signals into a context state
└── context/run_distraction_demo.py    # live webcam demo, standalone
tests/
└── test_head_pose.py
```

Run the demo: `python -m src.context.run_distraction_demo`
(needs `models/face_landmarker.task`, same model Person 1's module uses)

Run the test: `python -m tests.test_head_pose`

## Why head pose is a useful distraction proxy

Sustained head rotation away from the road (checking a phone, reaching
for something, turning to a passenger) is one of the more reliable,
camera-only correlates of visual inattention, and it's cheap to compute
from the same facial landmarks already being extracted for EAR/MAR —
no extra model needed beyond the six-point solvePnP fit.

## Why gaze alone isn't enough

Head pose captures where the head is pointed, not where the eyes are
looking — a driver can hold their head straight and still glance
sideways with just their eyes, or turn their head slightly while
staying visually on the road. It also can't detect cognitive
distraction at all (drivers who are "looking" at the road but not
processing it). That's why this module only produces an *indicator*,
not a verdict — Person 3's Risk Engine combines it with the other
signals rather than treating gaze as ground truth.

## YOLO model/component selection

YOLOv8n (nano), pretrained on COCO, filtered to class 67 ("cell
phone"). Chosen over larger YOLOv8 variants purely for inference
speed — this has to run in real time alongside face landmarking and
head-pose estimation on the same frame, and nano is the fastest
tradeoff in the family. No custom training was needed since "cell
phone" is already a COCO class.

## Initial contextual rules

| Motion (mocked) | Gaze                | Phone visible | State                  |
|------------------|----------------------|----------------|-------------------------|
| Stationary       | Looking away          | —              | POTENTIALLY_NORMAL      |
| Moving           | Sustained gaze away    | —              | DISTRACTION_INDICATOR   |
| Moving           | —                      | Yes            | PHONE_USE_INDICATOR     |
| otherwise        | —                      | —              | NORMAL                  |

`sustained gaze away` requires yaw/pitch past threshold for a minimum
held duration (default 1s) so a brief mirror check doesn't trigger a
false positive.

## Known placeholders (to flag at review, not hide)

- **"Moving" is a manual toggle**, not real vehicle telemetry — there's
  no speed/motion sensor integrated yet. The context engine's interface
  already takes `is_moving` as a bool, so swapping in a real signal
  later doesn't change the rest of the pipeline.
- **Head-pose thresholds (25° yaw, 20° pitch) are initial guesses**,
  not experimentally calibrated per the same caveat Person 1 noted for
  EAR/MAR thresholds.
- **This demo runs its own Face Landmarker instance** rather than
  consuming Person 1's landmark stream directly — fine for an
  independent 20% deliverable, but Person 3 will want to unify this
  into one shared landmark pipeline during integration.
