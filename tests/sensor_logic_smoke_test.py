"""Repeatable desktop smoke tests for sensor processing/environment logic.

Run from the repository root after creating local secrets.py:
    python tests/sensor_logic_smoke_test.py

These tests use simulated readings. They do not replace live-sensor hardware
integration, calibration or bus-compatibility testing.
"""

import os
import sys

# Allow imports from repository root when this file is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sensor_processing import SensorProcessor
from environment_logic import (
    ACTION_REQUIRED,
    MOULD_RISK,
    NORMAL,
    WARNING,
    EnvironmentLogic,
)


def sample(**changes):
    reading = {
        "temperature_c": 23.0,
        "humidity_pct": 50.0,
        "pressure_hpa": 1013.0,
        "voc_index": 80.0,
        "co2_ppm": 700.0,
        "surface_temperature_c": 22.0,
        "occupied": True,
    }
    reading.update(changes)
    return reading


def evaluate_once(reading):
    processor = SensorProcessor()
    logic = EnvironmentLogic()
    data, validity, health = processor.process(reading)
    return logic.evaluate(data, validity), data, validity, health


def run():
    state, _, validity, health = evaluate_once(sample())
    assert state == NORMAL
    assert all(validity.values())
    assert all(value == "VALID" for value in health.values())

    state, _, _, _ = evaluate_once(sample(co2_ppm=1400.0))
    assert state == ACTION_REQUIRED

    state, _, _, _ = evaluate_once(sample(humidity_pct=65.0))
    assert state == MOULD_RISK

    state, _, validity, health = evaluate_once(sample(co2_ppm=None))
    assert state == WARNING
    assert validity["co2_ppm"] is False
    assert health["co2_ppm"] == "INITIALISING"

    state, _, validity, _ = evaluate_once(sample(humidity_pct=150.0))
    assert state == WARNING
    assert validity["humidity_pct"] is False

    # Three-sample moving average: 20, 26, 32 -> 26 C.
    processor = SensorProcessor()
    for temperature in (20.0, 26.0, 32.0):
        data, _, _ = processor.process(sample(temperature_c=temperature))
    assert abs(data["temperature_c"] - 26.0) < 1e-9

    # Temperature hysteresis: ON >24 C, remains active at 23 C, clears <22 C.
    logic = EnvironmentLogic()
    validity = {
        "temperature_c": True,
        "humidity_pct": True,
        "co2_ppm": True,
        "occupied": True,
    }
    data = {"temperature_c": 25.0, "humidity_pct": 50.0, "co2_ppm": 700.0, "occupied": True}
    assert logic.evaluate(data, validity) == ACTION_REQUIRED
    data["temperature_c"] = 23.0
    assert logic.evaluate(data, validity) == ACTION_REQUIRED
    data["temperature_c"] = 21.0
    assert logic.evaluate(data, validity) == NORMAL

    # Humidity hysteresis: ON >60 %RH, remains active at 57, clears <55.
    logic = EnvironmentLogic()
    data = {"temperature_c": 23.0, "humidity_pct": 65.0, "co2_ppm": 700.0, "occupied": True}
    assert logic.evaluate(data, validity) == MOULD_RISK
    data["humidity_pct"] = 57.0
    assert logic.evaluate(data, validity) == MOULD_RISK
    data["humidity_pct"] = 54.0
    assert logic.evaluate(data, validity) == NORMAL

    print("sensor_logic_smoke_test: PASS")


if __name__ == "__main__":
    run()
