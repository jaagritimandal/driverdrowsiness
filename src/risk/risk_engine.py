import time


class RiskEngine:
    def __init__(self, smoothing=0.25, recovery_rate=12.0):
        self.risk_score = 0.0
        self.smoothing = smoothing
        self.recovery_rate = recovery_rate
        self._last_update = time.time()

    def calculate_risk(
        self,
        eye_state,
        prolonged_closure,
        closure_duration,
        blink,
        mar,
        context_state,
        looking_away,
        phone_visible,
    ):
        now = time.time()
        elapsed = now - self._last_update
        self._last_update = now

        target_risk = 0.0

        if eye_state == "CLOSED":
            target_risk += 15

        if prolonged_closure:
            target_risk += 30

        if closure_duration >= 2.0:
            target_risk += 10

        if mar >= 0.60:
            target_risk += 10

        if looking_away:
            target_risk += 10

        if context_state == "DISTRACTION_INDICATOR":
            target_risk += 15

        if phone_visible:
            target_risk += 20

        if context_state == "PHONE_USE_INDICATOR":
            target_risk += 20

        target_risk = min(target_risk, 100.0)

        if target_risk > self.risk_score:
            self.risk_score += (
                target_risk - self.risk_score
            ) * self.smoothing
        else:
            self.risk_score -= self.recovery_rate * elapsed

        self.risk_score = max(0.0, min(100.0, self.risk_score))

        if self.risk_score < 25:
            level = "NORMAL"
        elif self.risk_score < 50:
            level = "LOW"
        elif self.risk_score < 75:
            level = "MEDIUM"
        else:
            level = "HIGH"

        return {
            "risk_score": round(self.risk_score, 1),
            "risk_level": level,
        }