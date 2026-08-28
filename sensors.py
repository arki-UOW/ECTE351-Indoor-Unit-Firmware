"""Live sensor integration for the ECTE351 indoor unit."""

import time

try:
    import struct
except ImportError:
    import ustruct as struct

from machine import I2C, Pin

import config
from bme680_driver import BME680_I2C


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
        "interface": "digital OUT + reserved UART",
        "uart_id": config.MMWAVE_UART_ID,
        "tx_pin": config.MMWAVE_UART_TX_PIN,
        "rx_pin": config.MMWAVE_UART_RX_PIN,
        "out_pin": config.MMWAVE_OUT_PIN,
        "baudrate": config.MMWAVE_UART_BAUDRATE,
        "uart_enabled": config.MMWAVE_UART_ENABLED,
    },
}

_SCD30_CMD_START_CONTINUOUS = 0x0010
_SCD30_CMD_DATA_READY = 0x0202
_SCD30_CMD_READ_MEASUREMENT = 0x0300
_SCD30_CMD_SET_INTERVAL = 0x4600

_MLX_AMBIENT_REG = 0x06
_MLX_OBJECT_REG = 0x07

_SGP40_MEASURE_RAW = bytes([0x26, 0x0F])


def _crc8(data):
    crc = 0xFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x31) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


def _sensirion_word(value):
    msb = (value >> 8) & 0xFF
    lsb = value & 0xFF
    return bytes([msb, lsb, _crc8(bytes([msb, lsb]))])


class SensorManager:
    def __init__(self):
        self.i2c = None
        self.mmwave_out = None
        self.bme680 = None
        self.initialized = False
        self.health = {
            "bme680": "INITIALISING",
            "sgp40": "INITIALISING",
            "scd30": "INITIALISING",
            "mlx90614": "INITIALISING",
            "mmwave": "INITIALISING",
            "mmwave_uart": "NOT_CONNECTED",
        }
        self.detected_addresses = []
        self.last_errors = {}
        self.last_scd30 = None

    def interface_map(self):
        return {name: dict(details) for name, details in SENSOR_INTERFACES.items()}

    def _set_error(self, sensor, error):
        self.health[sensor] = "FAULT"
        self.last_errors[sensor] = str(error)
        print("[SENSOR][{}] ERROR: {}".format(sensor.upper(), error))

    def _set_ok(self, sensor):
        self.health[sensor] = "VALID"
        self.last_errors.pop(sensor, None)

    def scan_bus(self, verbose=True):
        try:
            self.detected_addresses = self.i2c.scan()
        except Exception as exc:
            self.detected_addresses = []
            self._set_error("i2c_bus", exc)
            return []

        if verbose:
            print("[I2C] SDA=A4/GPIO11 SCL=A5/GPIO12 @ 100 kHz")
            if not self.detected_addresses:
                print("[I2C] FAIL: no devices detected")
            else:
                print(
                    "[I2C] Detected:",
                    [hex(address) for address in self.detected_addresses],
                )

            expected = (
                ("BME680", config.BME680_I2C_ADDRESS),
                ("SGP40", config.SGP40_I2C_ADDRESS),
                ("SCD30", config.SCD30_I2C_ADDRESS),
                ("MLX90614", config.MLX90614_I2C_ADDRESS),
            )
            for name, address in expected:
                status = "PASS" if address in self.detected_addresses else "MISSING"
                print(
                    "[I2C] {:9s} {} at {}".format(
                        name, status, hex(address)
                    )
                )

            if (
                config.BME680_I2C_ADDRESS not in self.detected_addresses
                and 0x76 in self.detected_addresses
            ):
                print(
                    "[I2C] WARNING: BME680 appears at 0x76; "
                    "repo expects 0x77. Check SDO."
                )

        return list(self.detected_addresses)

    def initialize(self):
        print("[SENSOR] Initialising shared sensor bus...")

        self.i2c = I2C(
            config.I2C_ID,
            sda=Pin(config.I2C_SDA_PIN),
            scl=Pin(config.I2C_SCL_PIN),
            freq=config.I2C_FREQ_HZ,
        )
        self.mmwave_out = Pin(config.MMWAVE_OUT_PIN, Pin.IN)

        devices = self.scan_bus(verbose=True)

        if config.BME680_I2C_ADDRESS in devices:
            try:
                self.bme680 = BME680_I2C(
                    self.i2c,
                    address=config.BME680_I2C_ADDRESS,
                )
                self._set_ok("bme680")
                print("[SENSOR][BME680] PASS: driver initialised")
            except Exception as exc:
                self._set_error("bme680", exc)
        else:
            self.health["bme680"] = "MISSING"

        if config.SGP40_I2C_ADDRESS in devices:
            self._set_ok("sgp40")
            print("[SENSOR][SGP40] PASS: detected at 0x59")
        else:
            self.health["sgp40"] = "MISSING"

        if config.MLX90614_I2C_ADDRESS in devices:
            self._set_ok("mlx90614")
            print("[SENSOR][MLX90614] PASS: detected at 0x5A")
        else:
            self.health["mlx90614"] = "MISSING"

        if config.SCD30_I2C_ADDRESS in devices:
            try:
                self._scd30_start()
                self._set_ok("scd30")
                print("[SENSOR][SCD30] PASS: continuous measurement started")
            except Exception as exc:
                self._set_error("scd30", exc)
        else:
            self.health["scd30"] = "MISSING"

        try:
            state = self.mmwave_out.value()
            self._set_ok("mmwave")
            print(
                "[SENSOR][MMWAVE] PASS: OT2 on D2/GPIO5, initial state={}".format(
                    state
                )
            )
        except Exception as exc:
            self._set_error("mmwave", exc)

        if config.MMWAVE_UART_ENABLED:
            self.health["mmwave_uart"] = "PENDING"
            print("[SENSOR][MMWAVE] UART enabled in config but parser is not active")
        else:
            self.health["mmwave_uart"] = "NOT_CONNECTED"
            print(
                "[SENSOR][MMWAVE] UART TX/RX intentionally NOT CONNECTED. "
                "Reserved: TX GPIO17 -> sensor RX, RX GPIO18 <- sensor TX."
            )

        self.initialized = True
        return bool(devices)

    def _read_bme680(self):
        if self.bme680 is None:
            return None
        try:
            data = self.bme680.read_all()
            temperature = float(data["temperature_c"])
            humidity = float(data["humidity_pct"])
            pressure = float(data["pressure_hpa"])
            gas = int(data["gas_ohm"])

            if not (-40.0 <= temperature <= 85.0):
                raise ValueError("implausible temperature {:.2f} C".format(temperature))
            if not (0.0 <= humidity <= 100.0):
                raise ValueError("implausible humidity {:.2f} %RH".format(humidity))
            if not (300.0 <= pressure <= 1100.0):
                raise ValueError("implausible pressure {:.2f} hPa".format(pressure))
            if gas <= 0:
                raise ValueError("invalid gas resistance {}".format(gas))

            self._set_ok("bme680")
            return {
                "temperature_c": temperature,
                "humidity_pct": humidity,
                "pressure_hpa": pressure,
                "bme680_gas_ohm": gas,
            }
        except Exception as exc:
            self._set_error("bme680", exc)
            return None

    def _mlx_temperature(self, register):
        data = self.i2c.readfrom_mem(
            config.MLX90614_I2C_ADDRESS,
            register,
            3,
        )
        raw = data[0] | (data[1] << 8)
        return raw * 0.02 - 273.15

    def _read_mlx90614(self):
        if config.MLX90614_I2C_ADDRESS not in self.detected_addresses:
            return None
        try:
            ambient = self._mlx_temperature(_MLX_AMBIENT_REG)
            object_temp = self._mlx_temperature(_MLX_OBJECT_REG)
            self._set_ok("mlx90614")
            return {
                "mlx90614_ambient_c": ambient,
                "surface_temperature_c": object_temp,
            }
        except Exception as exc:
            self._set_error("mlx90614", exc)
            return None

    def _scd30_command(self, command):
        self.i2c.writeto(
            config.SCD30_I2C_ADDRESS,
            bytes([(command >> 8) & 0xFF, command & 0xFF]),
        )

    def _scd30_command_argument(self, command, argument):
        self.i2c.writeto(
            config.SCD30_I2C_ADDRESS,
            bytes(
                [
                    (command >> 8) & 0xFF,
                    command & 0xFF,
                ]
            )
            + _sensirion_word(argument),
        )

    def _scd30_start(self):
        self._scd30_command_argument(
            _SCD30_CMD_SET_INTERVAL,
            config.SCD30_MEASUREMENT_INTERVAL_S,
        )
        time.sleep_ms(20)
        self._scd30_command_argument(_SCD30_CMD_START_CONTINUOUS, 0)
        time.sleep_ms(20)

    def _scd30_ready(self):
        self._scd30_command(_SCD30_CMD_DATA_READY)
        time.sleep_ms(5)
        data = self.i2c.readfrom(config.SCD30_I2C_ADDRESS, 3)
        if _crc8(data[0:2]) != data[2]:
            raise ValueError("data-ready CRC mismatch")
        return ((data[0] << 8) | data[1]) == 1

    def _decode_scd30_float(self, data):
        if _crc8(data[0:2]) != data[2]:
            raise ValueError("CRC mismatch in first float word")
        if _crc8(data[3:5]) != data[5]:
            raise ValueError("CRC mismatch in second float word")
        raw = bytes([data[0], data[1], data[3], data[4]])
        return struct.unpack(">f", raw)[0]

    def _read_scd30(self):
        if config.SCD30_I2C_ADDRESS not in self.detected_addresses:
            return None
        try:
            if not self._scd30_ready():
                return self.last_scd30

            self._scd30_command(_SCD30_CMD_READ_MEASUREMENT)
            time.sleep_ms(5)
            data = self.i2c.readfrom(config.SCD30_I2C_ADDRESS, 18)

            result = {
                "co2_ppm": self._decode_scd30_float(data[0:6]),
                "scd30_temperature_c": self._decode_scd30_float(data[6:12]),
                "scd30_humidity_pct": self._decode_scd30_float(data[12:18]),
            }
            self.last_scd30 = result
            self._set_ok("scd30")
            return result
        except Exception as exc:
            self._set_error("scd30", exc)
            return self.last_scd30

    @staticmethod
    def _sgp40_humidity_ticks(relative_humidity):
        relative_humidity = max(0.0, min(100.0, float(relative_humidity)))
        return int(relative_humidity * 65535.0 / 100.0)

    @staticmethod
    def _sgp40_temperature_ticks(temperature_c):
        temperature_c = max(-45.0, min(130.0, float(temperature_c)))
        return int((temperature_c + 45.0) * 65535.0 / 175.0)

    def _read_sgp40(self, temperature_c, humidity_pct):
        if config.SGP40_I2C_ADDRESS not in self.detected_addresses:
            return None
        try:
            command = (
                _SGP40_MEASURE_RAW
                + _sensirion_word(
                    self._sgp40_humidity_ticks(humidity_pct)
                )
                + _sensirion_word(
                    self._sgp40_temperature_ticks(temperature_c)
                )
            )
            self.i2c.writeto(config.SGP40_I2C_ADDRESS, command)
            time.sleep_ms(40)
            data = self.i2c.readfrom(config.SGP40_I2C_ADDRESS, 3)

            if _crc8(data[0:2]) != data[2]:
                raise ValueError("CRC mismatch")

            raw_signal = (data[0] << 8) | data[1]
            self._set_ok("sgp40")
            return {"sgp40_raw_signal": raw_signal}
        except Exception as exc:
            self._set_error("sgp40", exc)
            return None

    def _read_mmwave(self):
        try:
            occupied = bool(self.mmwave_out.value())
            self._set_ok("mmwave")
            return {"occupied": occupied}
        except Exception as exc:
            self._set_error("mmwave", exc)
            return None

    def read_all(self):
        if not self.initialized:
            raise RuntimeError("SensorManager.initialize() must be called first")

        readings = {
            "temperature_c": None,
            "humidity_pct": None,
            "pressure_hpa": None,
            "voc_index": None,
            "co2_ppm": None,
            "surface_temperature_c": None,
            "occupied": None,
            "bme680_gas_ohm": None,
            "sgp40_raw_signal": None,
            "mlx90614_ambient_c": None,
            "scd30_temperature_c": None,
            "scd30_humidity_pct": None,
        }

        bme = self._read_bme680()
        if bme:
            readings.update(bme)

        scd = self._read_scd30()
        if scd:
            readings.update(scd)

        compensation_temp = readings["temperature_c"]
        compensation_humidity = readings["humidity_pct"]

        if compensation_temp is None and scd:
            compensation_temp = scd["scd30_temperature_c"]
        if compensation_humidity is None and scd:
            compensation_humidity = scd["scd30_humidity_pct"]

        if compensation_temp is None:
            compensation_temp = 25.0
        if compensation_humidity is None:
            compensation_humidity = 50.0

        sgp = self._read_sgp40(compensation_temp, compensation_humidity)
        if sgp:
            readings.update(sgp)

        mlx = self._read_mlx90614()
        if mlx:
            readings.update(mlx)

        mmwave = self._read_mmwave()
        if mmwave:
            readings.update(mmwave)

        return readings

    def get_health(self):
        return dict(self.health)

    def get_diagnostics(self):
        return {
            "detected_i2c_addresses": [
                hex(address) for address in self.detected_addresses
            ],
            "sensor_health": dict(self.health),
            "sensor_errors": dict(self.last_errors),
            "mmwave_uart_connected": bool(config.MMWAVE_UART_ENABLED),
        }
