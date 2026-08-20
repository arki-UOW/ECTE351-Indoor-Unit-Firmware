"""Top-level firmware application."""

import time

import config
from diagnostics import Diagnostics
from mode_logic import ModeLogic
from mqtt_manager import MQTTManager
from wifi_manager import WiFiManager


def main():
    diagnostics = Diagnostics()
    wifi = WiFiManager()
    mqtt = MQTTManager()
    mode_logic = ModeLogic()

    print("\nECTE351 Indoor Unit starting...")

    def handle_rpc(topic, payload):
        """Validate and execute supported ThingsBoard RPC commands safely."""
        method = payload.get("method") if isinstance(payload, dict) else None
        params = payload.get("params") if isinstance(payload, dict) else None

        if method != "set_mode":
            print("[RPC] Rejected unsupported method:", method)
            mqtt.publish_rpc_response(topic, {
                "success": False,
                "error": "unsupported_method",
            })
            return

        if not isinstance(params, dict):
            print("[RPC] Rejected set_mode: params must be an object")
            mqtt.publish_rpc_response(topic, {
                "success": False,
                "error": "invalid_params",
            })
            return

        requested_mode = params.get("mode")
        if not mode_logic.set_mode(requested_mode):
            print("[RPC] Rejected unsupported mode:", requested_mode)
            mqtt.publish_rpc_response(topic, {
                "success": False,
                "error": "unsupported_mode",
                "requested_mode": requested_mode,
            })
            return

        print("[RPC] Mode set to:", mode_logic.mode)
        mqtt.publish_rpc_response(topic, {
            "success": True,
            "mode": mode_logic.mode,
        })
        mqtt.publish_attributes({"mode": mode_logic.mode})

    mqtt.set_rpc_callback(handle_rpc)

    if not wifi.connect():
        diagnostics.report_error("wifi", "initial connection failed")
        return

    if not mqtt.connect():
        diagnostics.report_error("mqtt", "initial connection failed")
        return

    mqtt.publish_telemetry({
        "firmware_status": "online",
        "connectivity_test": 1,
    })
    mqtt.publish_attributes(mode_logic.status())

    print("[SYSTEM] Connectivity/RPC test firmware ready")

    while True:
        if not wifi.ensure_connected():
            diagnostics.report_error("wifi", "reconnection failed")
            time.sleep(2)
            continue

        if not mqtt.ensure_connected():
            diagnostics.report_error("mqtt", "reconnection failed")
            time.sleep(2)
            continue

        # Check RPC traffic frequently so dashboard commands are responsive.
        if not mqtt.check_messages():
            diagnostics.report_error("mqtt", "message polling failed")
            time.sleep_ms(config.MQTT_POLL_INTERVAL_MS)
            continue

        # Periodic MQTT PING detects silent/stale broker connections that have
        # not yet produced a socket error during normal polling.
        if not mqtt.health_check():
            diagnostics.report_error("mqtt", "health check failed")

        time.sleep_ms(config.MQTT_POLL_INTERVAL_MS)


try:
    main()
except KeyboardInterrupt:
    print("[SYSTEM] Stopped by user")
except Exception as exc:
    print("[SYSTEM] Fatal error:", exc)
