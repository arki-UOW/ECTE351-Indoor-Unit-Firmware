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
        if not isinstance(mode, str):
            return False

        normalized = mode.strip().upper().replace("-", "_").replace(" ", "_")
        if normalized not in ALLOWED_MODES:
            return False

        self.mode = normalized
        self.manual_override = normalized == MANUAL

        if normalized == PURGE:
            self.ventilation_request = True
        elif normalized != MANUAL:
            self.ventilation_request = False

        return True

    def set_manual_ventilation(self, enabled):
        if self.mode != MANUAL or not isinstance(enabled, bool):
            return False
        self.ventilation_request = enabled
        return True

    def decide(self, environment_state, data):
        self.system_condition = environment_state

        action_needed = environment_state in ("ACTION_REQUIRED", "MOULD_RISK")

        if self.mode == PURGE:
            self.ventilation_request = True
        elif self.mode == MANUAL:
            # Keep the explicit dashboard/manual request.
            pass
        else:
            # Until mode-specific thresholds are formally defined, all automatic
            # modes retain the same safety response to confirmed action states.
            self.ventilation_request = bool(action_needed)

        return {
            "mode": self.mode,
            "environment_state": environment_state,
            "ventilation_request": self.ventilation_request,
            "manual_override": self.manual_override,
        }
