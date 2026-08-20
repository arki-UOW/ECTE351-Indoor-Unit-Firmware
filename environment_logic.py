"""Environmental-condition evaluation for the indoor unit."""

NORMAL = "NORMAL"
WARNING = "WARNING"
ACTION_REQUIRED = "ACTION_REQUIRED"


class EnvironmentLogic:
    def evaluate(self, data, validity):
        """Return the current environmental state.

        Thresholds and hysteresis will be filled in once the agreed project
        values are confirmed. Until then, missing critical data must never
        produce an unsafe ventilation request.
        """
        critical = ("temperature_c", "humidity_pct", "co2_ppm")
        if any(not validity.get(key, False) for key in critical):
            return WARNING

        return NORMAL
