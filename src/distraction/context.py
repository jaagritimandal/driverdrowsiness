"""
context_engine.py

Combines motion context with gaze and phone signals into the
contextual states defined in the milestone task division:

    stationary + looking sideways  -> potentially normal
    moving + sustained gaze away   -> distraction indicator
    moving + phone visible         -> phone-use indicator

For the 20% milestone there's no real vehicle telemetry, so "moving"
is a mocked/manual input (toggle key in the demo script) standing in
for a future speed/motion sensor. This is documented as a known
placeholder, not a finished sensor integration.

Output of this module is what Person 3's Risk Engine consumes as the
"Person 2" side of the indicator table.

Author: Person 2 (Distraction & Context module)
"""

from enum import Enum


class ContextState(Enum):
    NORMAL = "NORMAL"
    POTENTIALLY_NORMAL = "POTENTIALLY_NORMAL"       # stationary + looking away
    DISTRACTION_INDICATOR = "DISTRACTION_INDICATOR"  # moving + sustained gaze away
    PHONE_USE_INDICATOR = "PHONE_USE_INDICATOR"       # moving + phone visible
    FACE_NOT_VISIBLE = "FACE_NOT_VISIBLE"             # head turned far enough away
                                                       # that pose can't be estimated
                                                       # at all -- this IS a distraction
                                                       # signal, not a gap in coverage


class ContextEngine:
    def evaluate(self, is_moving: bool, gaze_state: dict, phone_state: dict) -> dict:
        """
        is_moving: bool, mocked driving-state input for this milestone
        gaze_state: dict from GazeEstimator.update(). May include
            "face_lost_sustained": True when the face/pose has been
            undetectable for a sustained period (see run_demo.py's
            FaceLossTracker) -- e.g. the driver turned far enough away
            that MediaPipe/solvePnP can no longer produce a pose at all.
            A profile turn is a MORE extreme distraction than a measurable
            yaw angle, not an absence of one, so this takes priority over
            every other state (mirrors the "no-face grace period" pattern
            used in comparable driver-monitoring projects).
        phone_state: dict from PhoneDetector.detect()

        Returns a dict with the resolved ContextState and the raw
        signals that produced it (useful for the on-screen overlay and
        for Person 3's integration logging).
        """
        looking_away = gaze_state.get("looking_away", False)
        sustained_away = gaze_state.get("sustained_away", False)
        face_lost_sustained = gaze_state.get("face_lost_sustained", False)
        phone_visible = phone_state.get("phone_visible", False)

        if face_lost_sustained:
            state = ContextState.FACE_NOT_VISIBLE
        elif is_moving and phone_visible:
            state = ContextState.PHONE_USE_INDICATOR
        elif is_moving and sustained_away:
            state = ContextState.DISTRACTION_INDICATOR
        elif not is_moving and looking_away:
            state = ContextState.POTENTIALLY_NORMAL
        else:
            state = ContextState.NORMAL

        return {
            "context_state": state.value,
            "is_moving": is_moving,
            "looking_away": looking_away,
            "sustained_away": sustained_away,
            "face_lost_sustained": face_lost_sustained,
            "phone_visible": phone_visible,
        }