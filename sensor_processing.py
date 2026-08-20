"""Sensor validation, filtering and health processing."""

import time

import config

INITIALISING = "INITIALISING"
VALID = "VALID"
INVALID = "INVALID"
STALE = "STALE"
FAULT = "FAULT"


def _ticks_ms():
    """Return a monotonic millisecond counter on MicroPython or desktop Python."""
    if hasattr(time, "ticks_ms"):
        return time.ticks_ms()
    return int(time.monotonic() * 1000)


def _ticks_diff(new_ms, old_ms):
    """Return elapsed milliseconds on MicroPython or desktop Python."""
    if hasattr(time, "ticks_diff"):
        return time.ticks_diff(new_ms, old_ms)
    return new_ms - old_ms


class SensorProcessor:
    def __init__(self):
        self.history = {}
        self.last_valid_ms = {}
        self.health = {}

    def _now_ms(self):
        return _ticks_ms()

    def _is_number(self, value):
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    def _validate_value(self, key, value):
        if value is None:
            return False

        if key == "occupied":
            return isinstance(value, bool)

        limits = config.SENSOR_VALID_RANGES.get(key)
        if limits is None:
            return True

        if not self._is_number(value):
            return False

        minimum, maximum = limits
        return minimum <= value <= maximum

    def _filtered_value(self, key, value):
        if key == "occupied" or not self._is_number(value):
            return value

        values = self.history.setdefault(key, [])
        values.append(float(value))

        window = max(1, int(config.SENSOR_FILTER_WINDOW))
        if len(values) > window:
            del values[:-window]

        return sum(values) / len(values)

    def _missing_health(self, key, now_ms):
        last_valid = self.last_valid_ms.get(key)
        if last_valid is None:
            return INITIALISING

        age_ms = _ticks_diff(now_ms, last_valid)
        if age_ms >= config.SENSOR_STALE_TIMEOUT_MS:
            return STALE

        return INVALID

    def process(self, readings):
        """Validate and filter one raw sensor snapshot.

        Returns:
            processed: validated/filtered values; rejected readings become None.
            validity: per-field boolean validity map.
            health: per-field status map using INITIALISING/VALID/INVALID/STALE.
        """
        now_ms = self._now_ms()
        processed = {}
        validity = {}

        expected = (
            "temperature_c",
            "humidity_pct",
            "pressure_hpa",
            "voc_index",
            "co2_ppm",
            "surface_temperature_c",
            "occupied",
        )

        for key in expected:
            value = readings.get(key)
            is_valid = self._validate_value(key, value)
            validity[key] = is_valid

            if is_valid:
                processed[key] = self._filtered_value(key, value)
                self.last_valid_ms[key] = now_ms
                self.health[key] = VALID
            else:
                processed[key] = None
                self.health[key] = self._missing_health(key, now_ms)

        return processed, validity, dict(self.health)

    def get_health(self):
        return dict(self.health)
