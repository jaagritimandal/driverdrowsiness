import time


class GazeEstimator:
    def __init__(
        self,
        yaw_threshold_deg: float = 25.0,
        pitch_threshold_deg: float = 20.0,
        forward_yaw_threshold_deg: float = 18.0,
        forward_pitch_threshold_deg: float = 12.0,
        forward_confirm_seconds: float = 0.5,
        sustained_seconds: float = 4.0,
        face_lost_seconds: float = 1.5,
    ):
        self.yaw_threshold_deg = yaw_threshold_deg
        self.pitch_threshold_deg = pitch_threshold_deg

        self.forward_yaw_threshold_deg = forward_yaw_threshold_deg
        self.forward_pitch_threshold_deg = forward_pitch_threshold_deg

        self.forward_confirm_seconds = forward_confirm_seconds
        self.sustained_seconds = sustained_seconds
        self.face_lost_seconds = face_lost_seconds

        self._away_since = None
        self._forward_since = None
        self._face_lost_since = None

    def update(self, pitch: float, yaw: float):
        self._face_lost_since = None

        now = time.time()

        start_away = (
            abs(yaw) > self.yaw_threshold_deg
            or abs(pitch) > self.pitch_threshold_deg
        )

        confirmed_forward = (
            abs(yaw) < self.forward_yaw_threshold_deg
            and abs(pitch) < self.forward_pitch_threshold_deg
        )

        # ---------------------------------
        # Currently looking away
        # ---------------------------------
        if self._away_since is not None:

            # Only start the "forward confirmation"
            # timer when the pose actually looks forward.
            if confirmed_forward:
                if self._forward_since is None:
                    self._forward_since = now

                forward_duration = now - self._forward_since

                # Reset only after being forward
                # continuously for the required time.
                if forward_duration >= self.forward_confirm_seconds:
                    self._away_since = None
                    self._forward_since = None
            else:
                # One noisy frame that is not forward
                # cancels the forward confirmation.
                self._forward_since = None

        # ---------------------------------
        # Currently looking forward
        # ---------------------------------
        else:

            if start_away:
                self._away_since = now
                self._forward_since = None

        # ---------------------------------
        # Calculate current state
        # ---------------------------------
        if self._away_since is not None:
            away_duration = now - self._away_since
            looking_away = True
        else:
            away_duration = 0.0
            looking_away = False

        sustained_away = away_duration >= self.sustained_seconds

        return {
            "looking_away": looking_away,
            "sustained_away": sustained_away,
            "away_duration_sec": round(away_duration, 2),
            "face_lost_sustained": False,
            "pitch": round(pitch, 1),
            "yaw": round(yaw, 1),
        }

    def mark_face_lost(self):
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