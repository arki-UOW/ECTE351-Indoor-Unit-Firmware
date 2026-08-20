"""Sensor integration layer.

Hardware-specific drivers and pin assignments will be added after the final
indoor-unit wiring is confirmed. The application uses this module as the
single interface to all raw sensor readings.
"""


class SensorManager:
    def __init__(self):
        self.initialized = False
        self.health = {}

    def initialize(self):
        # TODO: initialise BME680, SGP40, SCD30, MLX90614 and motion sensor.
        self.initialized = True
        return True

    def read_all(self):
        # Placeholder values are deliberately None until real hardware is wired.
        return {
            "temperature_c": None,
            "humidity_pct": None,
            "pressure_hpa": None,
            "voc_index": None,
            "co2_ppm": None,
            "surface_temperature_c": None,
            "occupied": None,
        }

    def get_health(self):
        return dict(self.health)
