"""Sensor integration layer for the ECTE351 indoor unit.

The firmware-side interface contract is now defined. Physical wiring, driver
installation and live bus validation are performed during the hardware
integration stage.
"""

import config


SENSOR_INTERFACES = {
    "bme680": {
        "interface": "I2C",
        "address": config.BME680_I2C_ADDRESS,
    },
    "sgp40": {
        "interface": "I2C",
        "address": config.SGP40_I2C_ADDRESS,
    },
    "scd30": {
        "interface": "I2C",
        "address": config.SCD30_I2C_ADDRESS,
    },
    "mlx90614": {
        "interface": "I2C",
        "address": config.MLX90614_I2C_ADDRESS,
    },
    "mmwave": {
        "interface": "UART + digital OUT",
        "uart_id": config.MMWAVE_UART_ID,
        "tx_pin": config.MMWAVE_UART_TX_PIN,
        "rx_pin": config.MMWAVE_UART_RX_PIN,
        "out_pin": config.MMWAVE_OUT_PIN,
        "baudrate": config.MMWAVE_UART_BAUDRATE,
    },
}


class SensorManager:
    def __init__(self):
        self.initialized = False
        self.health = {}

    def interface_map(self):
        """Return a copy of the firmware-side sensor interface contract."""
        result = {}
        for name, details in SENSOR_INTERFACES.items():
            result[name] = dict(details)
        return result

    def initialize(self):
        # Driver initialisation is intentionally deferred until Omar's physical
        # wiring is available for live hardware validation.
        self.initialized = True
        return True

    def read_all(self):
        # Placeholder values remain None until real hardware is wired and tested.
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
