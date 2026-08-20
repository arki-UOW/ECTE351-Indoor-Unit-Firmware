"""Operating-mode and ventilation-decision logic."""

import config

AUTO = "AUTO"
MANUAL = "MANUAL"
SLEEP = "SLEEP"
WORK = "WORK"
ENERGY_SAVING = "ENERGY_SAVING"
PURGE = "PURGE"

ALLOWED_MODES = {AUTO, MANUAL, SLEEP, WORK, ENERGY_SAVING, PURGE}


class ModeLogic:
    def __init__(self):
        self.reset_defaults()

    def reset_defaults(self):
        """Restore deterministic safe state after boot/reset/recovery."""
        mode = config.DEFAULT_OPERATING_MODE
        self.mode = mode if mode in ALLOWED_MODES else AUTO
        self.manual_override = bool(config.DEFAULT_MANUAL_OVERRIDE)
        self.ventilation_request = bool(config.DEFAULT_VENTILATION_REQUEST)
        self.system_condition = config.DEFAULT_SYSTEM_CONDITION
        return self.status()

    def status(self):
        return {
            "mode": self.mode,
            "manual_override": self.manual_override,
            "ventilation_request": self.ventilation_request,
            "system_condition": self.system_condition,
        }

    def set_mode(self, mode):
        if mode not in ALLOWED_MODES:
            return False
        self.mode = mode
        return True

    def decide(self, environment_state, data):
        """Return a safe placeholder command for the outdoor controller."""
        self.system_condition = environment_state
        return {
            "mode": self.mode,
            "environment_state": environment_state,
            "ventilation_request": self.ventilation_request,
        }
