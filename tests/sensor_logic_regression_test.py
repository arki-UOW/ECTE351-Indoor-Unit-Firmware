"""Edge-case/regression tests for the indoor sensor-processing logic.

Run from the repository root:
    python tests/sensor_logic_regression_test.py

The tests are desktop-only simulated-input checks. They deliberately exercise
threshold boundaries, hysteresis state transitions, conflicting conditions and
sensor-health recovery without requiring physical hardware or real-time waits.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from environment_logic import ACTION_REQUIRED, MOULD_RISK, NORMAL, WARNING, EnvironmentLogic
from sensor_processing import INITIALISING, INVALID, STALE, VALID, SensorProcessor


VALIDITY = {
    "temperature_c": True,
    "humidity_pct": True,
    "co2_ppm": True,
    "occupied": True,
}


def env(temperature=23.0, humidity=50.0, co2=700.0, occupied=True):
    return {
        "temperature_c": temperature,
        "humidity_pct": humidity,
        "co2_ppm": co2,
        "occupied": occupied,
    }


def raw(**changes):
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


class FakeClockProcessor(SensorProcessor):
    """SensorProcessor with a controllable monotonic clock for health tests."""

    def __init__(self):
        super().__init__()
        self.now_ms = 0

    def _now_ms(self):
        return self.now_ms


def check_temperature_boundaries():
    logic = EnvironmentLogic()

    # Entry is strictly above 24 C.
    assert logic.evaluate(env(temperature=24.0), VALIDITY) == NORMAL
    assert logic.evaluate(env(temperature=24.0001), VALIDITY) == ACTION_REQUIRED

    # Once active, exact 22 C remains active; it clears only below 22 C.
    assert logic.evaluate(env(temperature=22.0), VALIDITY) == ACTION_REQUIRED
    assert logic.evaluate(env(temperature=21.9999), VALIDITY) == NORMAL


def check_humidity_boundaries():
    logic = EnvironmentLogic()

    # Entry is strictly above 60 %RH.
    assert logic.evaluate(env(humidity=60.0), VALIDITY) == NORMAL
    assert logic.evaluate(env(humidity=60.0001), VALIDITY) == MOULD_RISK

    # Once active, exact 55 %RH remains active; it clears only below 55 %RH.
    assert logic.evaluate(env(humidity=55.0), VALIDITY) == MOULD_RISK
    assert logic.evaluate(env(humidity=54.9999), VALIDITY) == NORMAL


def check_co2_and_occupancy_boundaries():
    # Occupied-space threshold is inclusive at 1000 ppm.
    assert EnvironmentLogic().evaluate(env(co2=999.0, occupied=True), VALIDITY) == NORMAL
    assert EnvironmentLogic().evaluate(env(co2=1000.0, occupied=True), VALIDITY) == ACTION_REQUIRED
    assert EnvironmentLogic().evaluate(env(co2=1001.0, occupied=True), VALIDITY) == ACTION_REQUIRED

    # CO2 threshold is intentionally occupancy-dependent.
    assert EnvironmentLogic().evaluate(env(co2=1001.0, occupied=False), VALIDITY) == NORMAL


def check_priority_and_invalid_inputs():
    logic = EnvironmentLogic()

    # If both high humidity and occupied high CO2 occur, mould risk wins by
    # explicit priority in environment_logic.py.
    assert logic.evaluate(env(humidity=65.0, co2=1500.0), VALIDITY) == MOULD_RISK

    # Missing critical validity forces WARNING regardless of numeric values.
    invalid = dict(VALIDITY)
    invalid["co2_ppm"] = False
    assert EnvironmentLogic().evaluate(env(co2=1500.0), invalid) == WARNING


def check_validation_edges():
    processor = SensorProcessor()

    # Validity ranges are inclusive at both ends.
    reading = raw(temperature_c=-20.0, humidity_pct=0.0, co2_ppm=250.0)
    _, validity, health = processor.process(reading)
    assert validity["temperature_c"] is True
    assert validity["humidity_pct"] is True
    assert validity["co2_ppm"] is True
    assert health["temperature_c"] == VALID

    processor = SensorProcessor()
    reading = raw(temperature_c=60.0001, humidity_pct=100.0001, co2_ppm=10000.0001)
    processed, validity, health = processor.process(reading)
    assert validity["temperature_c"] is False
    assert validity["humidity_pct"] is False
    assert validity["co2_ppm"] is False
    assert processed["temperature_c"] is None
    assert health["temperature_c"] == INITIALISING

    # Occupancy must be a real bool; numeric 0/1 is rejected.
    _, validity, _ = SensorProcessor().process(raw(occupied=1))
    assert validity["occupied"] is False


def check_filter_window_rollover():
    processor = SensorProcessor()
    temperatures = (10.0, 20.0, 30.0, 40.0)
    outputs = []
    for value in temperatures:
        data, _, _ = processor.process(raw(temperature_c=value))
        outputs.append(data["temperature_c"])

    # Window size is 3: [10] -> 10; [10,20] -> 15; [10,20,30] -> 20;
    # then oldest sample drops and [20,30,40] -> 30.
    assert outputs == [10.0, 15.0, 20.0, 30.0]


def check_health_state_machine_and_recovery():
    processor = FakeClockProcessor()

    # Before any valid sample, missing data is INITIALISING.
    _, validity, health = processor.process(raw(co2_ppm=None))
    assert validity["co2_ppm"] is False
    assert health["co2_ppm"] == INITIALISING

    # A valid sample establishes the last-valid timestamp.
    processor.now_ms = 100
    _, validity, health = processor.process(raw(co2_ppm=700.0))
    assert validity["co2_ppm"] is True
    assert health["co2_ppm"] == VALID

    # Missing before timeout -> INVALID.
    processor.now_ms = 100 + config.SENSOR_STALE_TIMEOUT_MS - 1
    _, _, health = processor.process(raw(co2_ppm=None))
    assert health["co2_ppm"] == INVALID

    # Missing at the exact timeout -> STALE.
    processor.now_ms = 100 + config.SENSOR_STALE_TIMEOUT_MS
    _, _, health = processor.process(raw(co2_ppm=None))
    assert health["co2_ppm"] == STALE

    # A subsequent valid reading must recover immediately to VALID.
    processor.now_ms += 1
    processed, validity, health = processor.process(raw(co2_ppm=800.0))
    assert validity["co2_ppm"] is True
    assert health["co2_ppm"] == VALID
    assert processed["co2_ppm"] is not None


def run():
    check_temperature_boundaries()
    check_humidity_boundaries()
    check_co2_and_occupancy_boundaries()
    check_priority_and_invalid_inputs()
    check_validation_edges()
    check_filter_window_rollover()
    check_health_state_machine_and_recovery()
    print("sensor_logic_regression_test: PASS")


if __name__ == "__main__":
    run()
