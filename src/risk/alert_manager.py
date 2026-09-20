import pygame


class AlertManager:
    def __init__(self):
        pygame.mixer.init()

    def update(self, risk_level):
        if risk_level == "NORMAL":
            return "NO_ALERT"

        if risk_level == "LOW":
            return "VISUAL_WARNING"

        if risk_level == "MEDIUM":
            return "WARNING"

        if risk_level == "HIGH":
            self._beep()
            return "CRITICAL_ALERT"

        return "NO_ALERT"

    def _beep(self):
        try:
            frequency = 1000
            duration = 300

            sample_rate = 44100
            samples = int(
                sample_rate * duration / 1000
            )

            import numpy as np

            wave = (
                np.sin(
                    2 * np.pi *
                    frequency *
                    np.arange(samples) /
                    sample_rate
                )
                * 32767
            ).astype(np.int16)

            stereo = np.column_stack(
                (wave, wave)
            )

            sound = pygame.sndarray.make_sound(
                stereo
            )

            sound.play()

        except Exception:
            pass