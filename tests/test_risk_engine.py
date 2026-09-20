import time

from src.risk.risk_engine import RiskEngine


engine = RiskEngine()


print("\n--- NORMAL DRIVER ---")

result = engine.calculate_risk(
    eye_state="OPEN",
    prolonged_closure=False,
    closure_duration=0.0,
    blink=False,
    mar=0.30,
    context_state="NORMAL",
    looking_away=False,
    phone_visible=False,
)

print(result)


print("\n--- LOOKING AWAY ---")

result = engine.calculate_risk(
    eye_state="OPEN",
    prolonged_closure=False,
    closure_duration=0.0,
    blink=False,
    mar=0.30,
    context_state="DISTRACTION_INDICATOR",
    looking_away=True,
    phone_visible=False,
)

print(result)


print("\n--- PROLONGED EYE CLOSURE ---")

result = engine.calculate_risk(
    eye_state="CLOSED",
    prolonged_closure=True,
    closure_duration=2.5,
    blink=False,
    mar=0.30,
    context_state="DISTRACTION_INDICATOR",
    looking_away=True,
    phone_visible=False,
)

print(result)


print("\n--- RECOVERY ---")

time.sleep(2)

result = engine.calculate_risk(
    eye_state="OPEN",
    prolonged_closure=False,
    closure_duration=0.0,
    blink=False,
    mar=0.30,
    context_state="NORMAL",
    looking_away=False,
    phone_visible=False,
)

print(result)