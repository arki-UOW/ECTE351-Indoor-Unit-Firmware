"""Diagnostics and health reporting for the indoor unit."""

import time


class Diagnostics:
    def __init__(self):
        self.last_error = None
        self.boot_ms = time.ticks_ms()

    def report_error(self, source, error):
        self.last_error = {
            "source": source,
            "error": str(error),
            "timestamp_ms": time.ticks_ms(),
        }
        print("[FAULT]", source, error)

    def status(self, wifi_ok, mqtt_ok, sensor_health=None):
        return {
            "wifi_ok": bool(wifi_ok),
            "mqtt_ok": bool(mqtt_ok),
            "sensor_health": sensor_health or {},
            "last_error": self.last_error,
        }
