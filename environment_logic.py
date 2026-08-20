"""Environmental-condition evaluation for the indoor unit."""

import config

NORMAL = "NORMAL"
WARNING = "WARNING"
ACTION_REQUIRED = "ACTION_REQUIRED"
MOULD_RISK = "MOULD_RISK"


class EnvironmentLogic:
    def __init__(self):
        self.high_temperature_active = False
        self.high_humidity_active = False

    def _update_hysteresis(self, temperature, humidity):
        # Temperature: enter above 24 C; remain active until below 22 C.
        if self.high_temperature_active:
            if temperature < config.TEMPERATURE_HIGH_OFF_C:
                self.high_temperature_active = False
        elif temperature > config.TEMPERATURE_HIGH_ON_C:
            self.high_temperature_active = True

        # Humidity: enter above 60 %RH; remain active until below 55 %RH.
        if self.high_humidity_active:
            if humidity < config.HUMIDITY_HIGH_OFF_PCT:
                self.high_humidity_active = False
        elif humidity > config.HUMIDITY_HIGH_ON_PCT:
            self.high_humidity_active = True

    def evaluate(self, data, validity):
        """Return the current environmental state using confirmed project rules.

        Confirmed Autumn rules implemented here:
        - Temperature high condition activates above 24 C and clears below 22 C.
        - Humidity high/mould-risk condition activates above 60 %RH and clears
          below 55 %RH.
        - Occupied-space CO2 target is below 1000 ppm.
        - Low humidity below 40 %RH is a warning.

        VOC Index is validated and reported, but no numeric Autumn action
        threshold was found, so it does not independently change state.
        """
        critical = ("temperature_c", "humidity_pct", "co2_ppm", "occupied")
        if any(not validity.get(key, False) for key in critical):
            return WARNING

        temperature = data["temperature_c"]
        humidity = data["humidity_pct"]
        co2 = data["co2_ppm"]
        occupied = data["occupied"]

        self._update_hysteresis(temperature, humidity)

        # Mould-risk humidity has the highest environmental priority here.
        if self.high_humidity_active:
            return MOULD_RISK

        # Occupied high CO2 requires ventilation action.
        if occupied and co2 >= config.CO2_OCCUPIED_LIMIT_PPM:
            return ACTION_REQUIRED

        # Sustained high temperature is also an action-required condition.
        if self.high_temperature_active:
            return ACTION_REQUIRED

        # Low RH is outside the project target range but is not mould risk.
        if humidity < config.HUMIDITY_TARGET_MIN_PCT:
            return WARNING

        return NORMAL
