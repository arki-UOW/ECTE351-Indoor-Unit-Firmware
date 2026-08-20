"""Sensor validation, filtering and health processing."""


class SensorProcessor:
    def __init__(self):
        self.previous = {}

    def process(self, readings):
        """Return validated/processed readings plus a simple validity map."""
        processed = dict(readings)
        validity = {}

        for key, value in processed.items():
            validity[key] = value is not None

        return processed, validity
