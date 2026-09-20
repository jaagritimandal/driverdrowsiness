import time


class ClosureDetector:
    def __init__(
        self,
        ear_threshold=0.21,
        closure_threshold_seconds=1.5,
    ):
        self.ear_threshold = ear_threshold
        self.closure_threshold_seconds = closure_threshold_seconds

        self._closed_since = None

    def update(self, ear):
        now = time.time()

        if ear < self.ear_threshold:

            if self._closed_since is None:
                self._closed_since = now

            duration = now - self._closed_since

            prolonged_closure = (
                duration >= self.closure_threshold_seconds
            )

            return {
                "eye_closed": True,
                "closure_duration_sec": round(duration, 2),
                "prolonged_closure": prolonged_closure,
            }

        else:

            self._closed_since = None

            return {
                "eye_closed": False,
                "closure_duration_sec": 0.0,
                "prolonged_closure": False,
            }