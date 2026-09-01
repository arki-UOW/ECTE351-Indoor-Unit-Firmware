"""Minimal BME680 I2C driver for MicroPython.

Adapted from the MIT-licensed BME680 MicroPython driver by Robert Hammelrath,
itself based on Adafruit's BME680 driver. I2C only.

The coefficient parsing and compensation path is aligned with the standalone
BME680 breadboard program that was physically validated on the project sensor.
"""

import time
import math
try:
    import struct
except ImportError:
    import ustruct as struct

_CHIP_ID = 0x61
_REG_CHIP_ID = 0xD0
_COEFF_ADDR1 = 0x89
_COEFF_ADDR2 = 0xE1
_REG_RES_HEAT0 = 0x5A
_REG_GAS_WAIT0 = 0x64
_REG_SOFT_RESET = 0xE0
_REG_CTRL_GAS = 0x71
_REG_CTRL_HUM = 0x72
_REG_CTRL_MEAS = 0x74
_REG_CONFIG = 0x75
_REG_MEAS_STATUS = 0x1D
_RUN_GAS = 0x10

_LOOKUP_TABLE_1 = (
    2147483647.0, 2147483647.0, 2147483647.0, 2147483647.0,
    2147483647.0, 2126008810.0, 2147483647.0, 2130303777.0,
    2147483647.0, 2147483647.0, 2143188679.0, 2136746228.0,
    2147483647.0, 2126008810.0, 2147483647.0, 2147483647.0,
)
_LOOKUP_TABLE_2 = (
    4096000000.0, 2048000000.0, 1024000000.0, 512000000.0,
    255744255.0, 127110228.0, 64000000.0, 32258064.0,
    16016016.0, 8000000.0, 4000000.0, 2000000.0,
    1000000.0, 500000.0, 250000.0, 125000.0,
)


def _read24(data):
    value = 0.0
    for byte in data:
        value = value * 256.0 + float(byte & 0xFF)
    return value


def _signed8(value):
    return value - 256 if value & 0x80 else value


def _signed4(value):
    value &= 0x0F
    return value - 16 if value & 0x08 else value


class BME680_I2C:
    def __init__(self, i2c, address=0x77, refresh_rate=10):
        self.i2c = i2c
        self.address = address

        self._write(_REG_SOFT_RESET, [0xB6])
        time.sleep_ms(10)

        chip_id = self._read_byte(_REG_CHIP_ID)
        if chip_id != _CHIP_ID:
            raise RuntimeError(
                "BME680 chip ID mismatch: expected 0x61, got 0x%02X" % chip_id
            )

        self._read_calibration()

        self._write(_REG_RES_HEAT0, [0x73])
        self._write(_REG_GAS_WAIT0, [0x65])

        self.sea_level_pressure = 1013.25
        self._pressure_oversample = 0b011
        self._temp_oversample = 0b100
        self._humidity_oversample = 0b010
        self._filter = 0b010

        self._adc_pres = None
        self._adc_temp = None
        self._adc_hum = None
        self._adc_gas = None
        self._gas_range = None
        self._t_fine = None

        self._last_reading = time.ticks_ms()
        self._min_refresh_time = max(1, 1000 // int(refresh_rate))

    def _read(self, register, length):
        return self.i2c.readfrom_mem(self.address, register, length)

    def _write(self, register, values):
        self.i2c.writeto_mem(self.address, register, bytes(values))

    def _read_byte(self, register):
        return self._read(register, 1)[0]

    def _read_calibration(self):
        coeff = self._read(_COEFF_ADDR1, 25)
        coeff += self._read(_COEFF_ADDR2, 16)

        unpacked = list(
            struct.unpack(
                "<hbBHhbBhhbbHhhBBBHbbbBbHhbb",
                bytes(coeff[1:39]),
            )
        )
        coeff = [float(value) for value in unpacked]

        self._temp_calibration = [coeff[x] for x in [23, 0, 1]]
        self._pressure_calibration = [
            coeff[x] for x in [3, 4, 5, 7, 8, 10, 9, 12, 13, 14]
        ]
        self._humidity_calibration = [
            coeff[x] for x in [17, 16, 18, 19, 20, 21, 22]
        ]
        self._gas_calibration = [coeff[x] for x in [25, 24, 26]]

        # H1/H2 are nibble-packed in the Bosch calibration block.
        self._humidity_calibration[1] *= 16
        self._humidity_calibration[1] += self._humidity_calibration[0] % 16
        self._humidity_calibration[0] /= 16

        # Preserve the signed calibration interpretation used by the physically
        # validated standalone breadboard driver. This matters particularly for
        # the gas-resistance compensation path.
        self._heat_range = (self._read_byte(0x02) & 0x30) / 16
        self._heat_val = _signed8(self._read_byte(0x00))
        self._sw_err = _signed4((self._read_byte(0x04) & 0xF0) >> 4)

    def _perform_reading(self):
        elapsed = time.ticks_diff(time.ticks_ms(), self._last_reading)
        if 0 <= elapsed < self._min_refresh_time:
            time.sleep_ms(self._min_refresh_time - elapsed)

        self._write(_REG_CONFIG, [self._filter << 2])
        self._write(
            _REG_CTRL_MEAS,
            [(self._temp_oversample << 5) | (self._pressure_oversample << 2)],
        )
        self._write(_REG_CTRL_HUM, [self._humidity_oversample])
        self._write(_REG_CTRL_GAS, [_RUN_GAS])

        ctrl = self._read_byte(_REG_CTRL_MEAS)
        self._write(_REG_CTRL_MEAS, [(ctrl & 0xFC) | 0x01])

        deadline = time.ticks_add(time.ticks_ms(), 1000)
        while True:
            data = self._read(_REG_MEAS_STATUS, 15)
            if data[0] & 0x80:
                break
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                raise RuntimeError("BME680 measurement timeout")
            time.sleep_ms(5)

        self._last_reading = time.ticks_ms()
        self._adc_pres = _read24(data[2:5]) / 16
        self._adc_temp = _read24(data[5:8]) / 16
        self._adc_hum = struct.unpack(">H", bytes(data[8:10]))[0]
        self._adc_gas = int(struct.unpack(">H", bytes(data[13:15]))[0] / 64)
        self._gas_range = data[14] & 0x0F

        var1 = (self._adc_temp / 8) - (self._temp_calibration[0] * 2)
        var2 = (var1 * self._temp_calibration[1]) / 2048
        var3 = ((var1 / 2) * (var1 / 2)) / 4096
        var3 = (var3 * self._temp_calibration[2] * 16) / 16384
        self._t_fine = int(var2 + var3)

    def read_all(self):
        # One forced-mode sample is used for all four compensated outputs so the
        # values in a telemetry snapshot correspond to the same sensor sample.
        self._perform_reading()

        calc_temp = (((self._t_fine * 5) + 128) / 256) / 100

        var1 = (self._t_fine / 2) - 64000
        var2 = ((var1 / 4) * (var1 / 4)) / 2048
        var2 = (var2 * self._pressure_calibration[5]) / 4
        var2 += var1 * self._pressure_calibration[4] * 2
        var2 = (var2 / 4) + (self._pressure_calibration[3] * 65536)
        var1 = (
            ((((var1 / 4) * (var1 / 4)) / 8192)
             * (self._pressure_calibration[2] * 32) / 8)
            + ((self._pressure_calibration[1] * var1) / 2)
        )
        var1 /= 262144
        var1 = ((32768 + var1) * self._pressure_calibration[0]) / 32768
        if var1 == 0:
            raise RuntimeError("BME680 pressure compensation divide by zero")

        calc_pres = 1048576 - self._adc_pres
        calc_pres = (calc_pres - (var2 / 4096)) * 3125
        calc_pres = (calc_pres / var1) * 2
        var1 = (
            self._pressure_calibration[8]
            * (((calc_pres / 8) * (calc_pres / 8)) / 8192)
        ) / 4096
        var2 = ((calc_pres / 4) * self._pressure_calibration[7]) / 8192
        var3 = (
            ((calc_pres / 256) ** 3) * self._pressure_calibration[9]
        ) / 131072
        calc_pres += (
            var1 + var2 + var3 + (self._pressure_calibration[6] * 128)
        ) / 16
        pressure_hpa = calc_pres / 100

        temp_scaled = ((self._t_fine * 5) + 128) / 256
        var1 = (
            self._adc_hum
            - (self._humidity_calibration[0] * 16)
            - ((temp_scaled * self._humidity_calibration[2]) / 200)
        )
        var2 = (
            self._humidity_calibration[1]
            * (
                ((temp_scaled * self._humidity_calibration[3]) / 100)
                + (
                    (
                        temp_scaled
                        * ((temp_scaled * self._humidity_calibration[4]) / 100)
                    )
                    / 64
                    / 100
                )
                + 16384
            )
        ) / 1024
        var3 = var1 * var2
        var4 = self._humidity_calibration[5] * 128
        var4 = (
            var4 + ((temp_scaled * self._humidity_calibration[6]) / 100)
        ) / 16
        var5 = ((var3 / 16384) * (var3 / 16384)) / 1024
        var6 = (var4 * var5) / 2
        humidity = (((var3 + var6) / 1024) * 1000) / 4096
        humidity = max(0.0, min(100.0, humidity / 1000))

        var1 = (
            (1340 + (5 * self._sw_err))
            * _LOOKUP_TABLE_1[self._gas_range]
        ) / 65536
        var2 = ((self._adc_gas * 32768) - 16777216) + var1
        if var2 == 0:
            raise RuntimeError("BME680 gas compensation divide by zero")
        var3 = (_LOOKUP_TABLE_2[self._gas_range] * var1) / 512
        gas_ohm = int((var3 + (var2 / 2)) / var2)

        return {
            "temperature_c": calc_temp,
            "humidity_pct": humidity,
            "pressure_hpa": pressure_hpa,
            "gas_ohm": gas_ohm,
        }

    @property
    def temperature(self):
        return self.read_all()["temperature_c"]

    @property
    def humidity(self):
        return self.read_all()["humidity_pct"]

    @property
    def pressure(self):
        return self.read_all()["pressure_hpa"]

    @property
    def gas(self):
        return self.read_all()["gas_ohm"]

    @property
    def altitude(self):
        pressure = self.pressure
        return 44330.77 * (
            1.0 - math.pow(pressure / self.sea_level_pressure, 0.1902632)
        )
