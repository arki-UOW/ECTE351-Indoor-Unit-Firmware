"""Top-level firmware application.

Initial milestone: prove Wi-Fi and ThingsBoard MQTT connectivity first.
Later stages will enable real sensors, processing, environmental logic and
outdoor-controller commands without changing the overall architecture.
"""

import time

import config
from diagnostics import Diagnostics
from mqtt_manager import MQTTManager
from wifi_manager import WiFiManager


def main():
    diagnostics = Diagnostics()
    wifi = WiFiManager()
    mqtt = MQTTManager()

    print("\nECTE351 Indoor Unit starting...")

    if not wifi.connect():
        diagnostics.report_error("wifi", "initial connection failed")
        return

    if not mqtt.connect():
        diagnostics.report_error("mqtt", "initial connection failed")
        return

    # Stage-1 proof-of-connection telemetry.
    mqtt.publish_telemetry({
        "firmware_status": "online",
        "connectivity_test": 1,
    })

    print("[SYSTEM] Stage-1 connectivity test complete")

    while True:
        if not wifi.ensure_connected():
            diagnostics.report_error("wifi", "reconnection failed")
            time.sleep(2)
            continue

        if not mqtt.ensure_connected():
            diagnostics.report_error("mqtt", "reconnection failed")
            time.sleep(2)
            continue

        mqtt.check_messages()
        time.sleep(config.TELEMETRY_INTERVAL_S)


try:
    main()
except KeyboardInterrupt:
    print("[SYSTEM] Stopped by user")
except Exception as exc:
    print("[SYSTEM] Fatal error:", exc)
