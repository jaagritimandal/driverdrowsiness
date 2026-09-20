"""
gaze_estimator.py

Derives a basic gaze/attention state from head pose (yaw/pitch).

This is deliberately NOT eye-gaze tracking (iris position) for the 20%
milestone -- head orientation is used as a proxy for visual attention,
which is a standard first-pass approach: sustained yaw away from
forward implies the driver is not looking at the road.

Limitation to document: head pose alone can't distinguish "eyes still
on road, head slightly turned" from genuine visual distraction, and it
says nothing about cognitive/mental distraction. That's why gaze alone
isn't a complete distraction signal -- it's one indicator the
Risk Engine (Person 3) combines with others.

Author: Person 2 (Distraction & Context module)
"""

import time


class GazeEstimator:
    """
    Tracks whether the driver is "looking away" based on head yaw/pitch
    thresholds sustained over time (to avoid flagging brief, normal
    glances like checking mirrors).
    """

    def __init__(
        self,
        yaw_threshold_deg: float = 25.0,
        pitch_threshold_deg: float = 20.0,
        sustained_seconds: float = 4.0,
        face_lost_seconds: float = 1.5,
    ):
        # Thresholds cross-checked against comparable open driver-monitoring
        # projects: 25 deg yaw / 20 deg pitch is a widely used pair.
        # sustained_seconds=4.0 (per your request): a side-mirror check is a
        # normal, frequent glance and shouldn't trip an alert -- it typically
        # resolves well under 4s, so only a genuinely sustained look-away
        # crosses this and gets flagged.
        self.yaw_threshold_deg = yaw_threshold_deg
        self.pitch_threshold_deg = pitch_threshold_deg
        self.sustained_seconds = sustained_seconds
        self.face_lost_seconds = face_lost_seconds

        self._away_since = None       # timestamp when "away" started, or None
        self._face_lost_since = None  # timestamp when pose first became undetectable

    def update(self, pitch: float, yaw: float):
        """
        Call once per frame the pose WAS successfully estimated.
        Returns a dict describing the current gaze state.
        """
        self._face_lost_since = None  # pose is back -- clear any face-loss timer

        is_away_now = (
            abs(yaw) > self.yaw_threshold_deg
            or abs(pitch) > self.pitch_threshold_deg
        )

        now = time.time()

        if is_away_now:
            if self._away_since is None:
                self._away_since = now
            away_duration = now - self._away_since
        else:
            self._away_since = None
            away_duration = 0.0

        sustained_away = away_duration >= self.sustained_seconds

        return {
            "looking_away": is_away_now,
            "sustained_away": sustained_away,
            "away_duration_sec": round(away_duration, 2),
            "face_lost_sustained": False,
            "pitch": round(pitch, 1),
            "yaw": round(yaw, 1),
        }

    def mark_face_lost(self):
        """
        Call once per frame the face/pose could NOT be detected (e.g. the
        driver turned far enough away that MediaPipe/solvePnP couldn't
        produce a pose at all -- see run_demo.py). A brief detection drop
        (motion blur, a blink) shouldn't alarm, but a SUSTAINED loss is
        itself a strong distraction signal -- often stronger than a
        measurable yaw angle, since it means the driver turned even
        further than the pose model can track.

        Also clears the stale "looking away" timer so it doesn't keep
        counting silently while nothing is actually being measured.
        """
        self._away_since = None

        now = time.time()
        if self._face_lost_since is None:
            self._face_lost_since = now
        lost_duration = now - self._face_lost_since
        face_lost_sustained = lost_duration >= self.face_lost_seconds

        return {
            "looking_away": True,
            "sustained_away": False,
            "away_duration_sec": 0.0,
            "face_lost_sustained": face_lost_sustained,
            "face_lost_duration_sec": round(lost_duration, 2),
            "pitch": None,
            "yaw": None,
        }