"""Environmental-condition evaluation for the indoor unit."""

import config

NORMAL = "NORMAL"
WARNING = "WARNING"
ACTION_REQUIRED = "ACTION_REQUIRED"
MOULD_RISK = "MOULD_RISK"


class EnvironmentLogic:
    def evaluate(self, data, validity):
        """Return the current environmental state using confirmed project rules.

        Confirmed Autumn targets:
        - CO2 below 1000 ppm during occupied periods.
        - Relative humidity between 40 and 60 %RH for mould-risk reduction.

        Temperature and VOC action thresholds are intentionally not invented;
        those values can be added once the team confirms the agreed thresholds.
        """
        critical = ("temperature_c", "humidity_pct", "co2_ppm", "occupied")
        if any(not validity.get(key, False) for key in critical):
            return WARNING

        humidity = data["humidity_pct"]
        co2 = data["co2_ppm"]
        occupied = data["occupied"]

        # Humidity above the confirmed 60 %RH target is treated as mould risk.
        if humidity > config.HUMIDITY_TARGET_MAX_PCT:
            return MOULD_RISK

        # During occupancy, breaching the confirmed CO2 limit requires action.
        if occupied and co2 >= config.CO2_OCCUPIED_LIMIT_PPM:
            return ACTION_REQUIRED

        # Low humidity is outside the confirmed target but is not a mould risk.
        if humidity < config.HUMIDITY_TARGET_MIN_PCT:
            return WARNING

        return NORMAL
