import time


class BlinkDetector:
    def __init__(self, ear_threshold=0.21):
        self.ear_threshold = ear_threshold

        self.eye_closed = False
        self.blink_count = 0
        self._closed_since = None

    def update(self, ear):
        now = time.time()
        blink = False

        if ear < self.ear_threshold:

            if not self.eye_closed:
                self.eye_closed = True
                self._closed_since = now

        else:

            if self.eye_closed:
                self.blink_count += 1
                blink = True

            self.eye_closed = False
            self._closed_since = None

        if self.eye_closed:
            closed_duration = now - self._closed_since
            eye_state = "CLOSED"
        else:
            closed_duration = 0.0
            eye_state = "OPEN"

        return {
            "eye_state": eye_state,
            "blink": blink,
            "blink_count": self.blink_count,
            "closed_duration_sec": round(closed_duration, 2),
        }