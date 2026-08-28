"""Top-level firmware application for the ECTE351 indoor unit."""

import time

import config
from diagnostics import Diagnostics
from environment_logic import EnvironmentLogic
from mode_logic import ModeLogic
from mqtt_manager import MQTTManager
from sensor_processing import SensorProcessor
from sensors import SensorManager
from wifi_manager import WiFiManager


def _ticks_due(last_ms, interval_s):
    if not last_ms:
        return True
    return time.ticks_diff(time.ticks_ms(), last_ms) >= int(interval_s * 1000)


def _telemetry_payload(raw, processed, validity, sensor_health, decision):
    payload = {}

    for key, value in processed.items():
        if value is not None:
            payload[key] = value

    extra_keys = (
        "bme680_gas_ohm",
        "sgp40_raw_signal",
        "mlx90614_ambient_c",
        "scd30_temperature_c",
        "scd30_humidity_pct",
    )
    for key in extra_keys:
        value = raw.get(key)
        if value is not None:
            payload[key] = value

    payload.update(
        {
            "mode": decision["mode"],
            "environment_state": decision["environment_state"],
            "ventilation_request": decision["ventilation_request"],
            "manual_override": decision["manual_override"],
            "mmwave_uart_connected": bool(config.MMWAVE_UART_ENABLED),
        }
    )

    for key, is_valid in validity.items():
        payload["{}_valid".format(key)] = bool(is_valid)

    for sensor, status in sensor_health.items():
        payload["{}_status".format(sensor)] = status

    return payload


def _print_snapshot(raw, processed, sensor_health, decision):
    print()
    print("================ LIVE INDOOR UNIT ================")

    def show(label, key, suffix=""):
        value = raw.get(key)
        if value is None:
            print("{:<22} {}".format(label, "UNAVAILABLE"))
        elif isinstance(value, float):
            print("{:<22} {:.2f}{}".format(label, value, suffix))
        else:
            print("{:<22} {}{}".format(label, value, suffix))

    show("BME680 temperature", "temperature_c", " C")
    show("BME680 humidity", "humidity_pct", " %RH")
    show("BME680 pressure", "pressure_hpa", " hPa")
    show("BME680 gas", "bme680_gas_ohm", " ohm")
    show("SCD30 CO2", "co2_ppm", " ppm")
    show("SCD30 temperature", "scd30_temperature_c", " C")
    show("SCD30 humidity", "scd30_humidity_pct", " %RH")
    show("SGP40 raw signal", "sgp40_raw_signal")
    show("MLX ambient", "mlx90614_ambient_c", " C")
    show("MLX object", "surface_temperature_c", " C")
    show("Occupied", "occupied")

    print("Environment            {}".format(decision["environment_state"]))
    print("Mode                   {}".format(decision["mode"]))
    print("Ventilation request    {}".format(decision["ventilation_request"]))
    print("Sensor health          {}".format(sensor_health))
    print(
        "mmWave UART            {}".format(
            "CONNECTED" if config.MMWAVE_UART_ENABLED else "NOT CONNECTED"
        )
    )
    print("==================================================")


def main():
    diagnostics = Diagnostics()
    wifi = WiFiManager()
    mqtt = MQTTManager()
    mode_logic = ModeLogic()
    sensors = SensorManager()
    processor = SensorProcessor()
    environment = EnvironmentLogic()

    print()
    print("==================================================")
    print("ECTE351 SMART VENTILATION SYSTEM - INDOOR UNIT")
    print("Waveshare ESP32-S3-Nano / final breadboard integration")
    print("==================================================")

    def handle_rpc(topic, payload):
        method = payload.get("method") if isinstance(payload, dict) else None
        params = payload.get("params") if isinstance(payload, dict) else None

        if method == "set_mode":
            if not isinstance(params, dict):
                mqtt.publish_rpc_response(
                    topic,
                    {"success": False, "error": "invalid_params"},
                )
                return

            requested_mode = params.get("mode")
            if not mode_logic.set_mode(requested_mode):
                mqtt.publish_rpc_response(
                    topic,
                    {
                        "success": False,
                        "error": "unsupported_mode",
                        "requested_mode": requested_mode,
                    },
                )
                return

            print("[RPC] Mode set to:", mode_logic.mode)
            mqtt.publish_rpc_response(
                topic,
                {
                    "success": True,
                    "mode": mode_logic.mode,
                },
            )
            mqtt.publish_attributes(mode_logic.status())
            return

        if method == "set_ventilation":
            if not isinstance(params, dict):
                mqtt.publish_rpc_response(
                    topic,
                    {"success": False, "error": "invalid_params"},
                )
                return

            enabled = params.get("enabled")
            if not mode_logic.set_manual_ventilation(enabled):
                mqtt.publish_rpc_response(
                    topic,
                    {
                        "success": False,
                        "error": "manual_mode_required_or_invalid_value",
                    },
                )
                return

            print("[RPC] Manual ventilation:", enabled)
            mqtt.publish_rpc_response(
                topic,
                {
                    "success": True,
                    "ventilation_request": mode_logic.ventilation_request,
                },
            )
            mqtt.publish_attributes(mode_logic.status())
            return

        print("[RPC] Rejected unsupported method:", method)
        mqtt.publish_rpc_response(
            topic,
            {
                "success": False,
                "error": "unsupported_method",
            },
        )

    mqtt.set_rpc_callback(handle_rpc)

    try:
        sensors.initialize()
    except Exception as exc:
        diagnostics.report_error("sensors", exc)
        print("[SYSTEM] Continuing so Wi-Fi/MQTT diagnostics remain available.")

    if not wifi.connect():
        diagnostics.report_error("wifi", "initial connection failed")
        print("[SYSTEM] Will keep retrying Wi-Fi from the main loop.")

    if wifi.is_connected() and not mqtt.connect():
        diagnostics.report_error("mqtt", "initial connection failed")
        print("[SYSTEM] Will keep retrying MQTT from the main loop.")

    if mqtt.connected:
        mqtt.publish_attributes(mode_logic.status())
        mqtt.publish_attributes(
            {
                "firmware_status": "online",
                "hardware_target": "Waveshare ESP32-S3-Nano",
                "mmwave_uart_connected": bool(config.MMWAVE_UART_ENABLED),
                "mmwave_uart_baudrate": config.MMWAVE_UART_BAUDRATE,
            }
        )
        mqtt.publish_telemetry(
            {
                "firmware_status": "online",
                "boot_complete": True,
            }
        )

    last_sensor_read_ms = 0
    last_telemetry_ms = 0
    last_rescan_ms = time.ticks_ms()

    raw = {}
    processed = {}
    validity = {}
    sensor_health = {}
    decision = {
        "mode": mode_logic.mode,
        "environment_state": "INITIALISING",
        "ventilation_request": False,
        "manual_override": mode_logic.manual_override,
    }

    while True:
        if not wifi.ensure_connected():
            diagnostics.report_error("wifi", "reconnection failed")
        elif not mqtt.ensure_connected():
            diagnostics.report_error("mqtt", "reconnection failed")
        else:
            if not mqtt.check_messages():
                diagnostics.report_error("mqtt", "message polling failed")

            if not mqtt.health_check():
                diagnostics.report_error("mqtt", "health check failed")

        if _ticks_due(last_sensor_read_ms, config.SENSOR_READ_INTERVAL_S):
            last_sensor_read_ms = time.ticks_ms()

            try:
                raw = sensors.read_all()
                processed, validity, field_health = processor.process(raw)
                sensor_health = sensors.get_health()

                environment_state = environment.evaluate(processed, validity)
                decision = mode_logic.decide(environment_state, processed)

                for key, value in field_health.items():
                    sensor_health["field_{}".format(key)] = value

                _print_snapshot(raw, processed, sensor_health, decision)

            except Exception as exc:
                diagnostics.report_error("sensor_cycle", exc)

        if time.ticks_diff(time.ticks_ms(), last_rescan_ms) >= int(
            config.SENSOR_RESCAN_INTERVAL_S * 1000
        ):
            last_rescan_ms = time.ticks_ms()
            try:
                sensors.scan_bus(verbose=True)
            except Exception as exc:
                diagnostics.report_error("i2c_rescan", exc)

        if (
            mqtt.connected
            and raw
            and _ticks_due(last_telemetry_ms, config.TELEMETRY_INTERVAL_S)
        ):
            last_telemetry_ms = time.ticks_ms()

            try:
                payload = _telemetry_payload(
                    raw,
                    processed,
                    validity,
                    sensor_health,
                    decision,
                )

                diag = diagnostics.status(
                    wifi.is_connected(),
                    mqtt.connected,
                    sensor_health,
                )
                payload["wifi_ok"] = diag["wifi_ok"]
                payload["mqtt_ok"] = diag["mqtt_ok"]

                if not mqtt.publish_telemetry(payload):
                    diagnostics.report_error(
                        "mqtt",
                        "telemetry publish failed",
                    )
            except Exception as exc:
                diagnostics.report_error("telemetry", exc)

        time.sleep_ms(config.MQTT_POLL_INTERVAL_MS)


try:
    main()
except KeyboardInterrupt:
    print("[SYSTEM] Stopped by user")
except Exception as exc:
    print("[SYSTEM] Fatal error:", exc)
