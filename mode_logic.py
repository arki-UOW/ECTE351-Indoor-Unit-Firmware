"""Operating-mode and ventilation-decision logic."""

AUTO = "AUTO"
MANUAL = "MANUAL"
SLEEP = "SLEEP"
WORK = "WORK"
ENERGY_SAVING = "ENERGY_SAVING"
PURGE = "PURGE"


class ModeLogic:
    def __init__(self):
        self.mode = AUTO

    def set_mode(self, mode):
        allowed = {AUTO, MANUAL, SLEEP, WORK, ENERGY_SAVING, PURGE}
        if mode not in allowed:
            return False
        self.mode = mode
        return True

    def decide(self, environment_state, data):
        """Return a safe placeholder command for the outdoor controller."""
        return {
            "mode": self.mode,
            "environment_state": environment_state,
            "ventilation_request": False,
        }
