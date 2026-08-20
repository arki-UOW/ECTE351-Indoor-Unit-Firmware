# ECTE351 Indoor Unit Firmware

MicroPython firmware for the ECTE351 Smart Ventilation System indoor unit.

Target controller: Waveshare ESP32-S3-Nano running MicroPython.

## Current hardware

- BME680 — temperature, humidity, pressure and gas sensing
- Adafruit SGP40 — VOC Index / air-quality sensing
- Sensirion SCD30 — CO2, temperature and humidity
- MLX90614 — infrared surface/object temperature
- mmWave presence sensor — occupancy / presence detection

## Current status

- Wi-Fi connection verified on the ESP32-S3-Nano.
- MQTT connection to ThingsBoard verified using the assigned host, port and access token.
- End-to-end telemetry publishing verified; `firmware_status=online` and `connectivity_test=1` were received on ThingsBoard.
- Modular firmware architecture established.
- Reconnection, timeout and malformed-message handling are currently under development.

## Development approach

1. Verify Wi-Fi connectivity. ✅
2. Verify MQTT/ThingsBoard connectivity. ✅
3. Add robust reconnect/default handling. In progress.
4. Confirm final GPIO/interface map.
5. Integrate sensors individually and verify bus compatibility.
6. Replace simulated values with live sensor data.
7. Process and validate sensor data.
8. Add environmental and operating-mode logic.
9. Add diagnostics/fault handling.
10. Perform full end-to-end integration testing.

## Firmware modules

- `boot.py` - minimal boot-time setup
- `main.py` - top-level application loop
- `config.py` - non-secret firmware configuration
- `secrets.py` - local Wi-Fi and ThingsBoard credentials; intentionally ignored by Git
- `secrets.example.py` - safe template for local secrets
- `wifi_manager.py` - Wi-Fi connection/reconnection
- `mqtt_manager.py` - ThingsBoard MQTT connection, telemetry and command handling
- `sensors.py` - sensor initialisation and raw readings
- `sensor_processing.py` - validation/filtering/status handling
- `environment_logic.py` - thresholds, hysteresis and environment state
- `mode_logic.py` - operating mode and ventilation decisions
- `diagnostics.py` - fault reporting and health checks

## Security

Never commit real Wi-Fi passwords or ThingsBoard access tokens. Copy `secrets.example.py` to `secrets.py` locally and enter credentials there. `secrets.py` is ignored by Git.

## Verified Stage 1 behaviour

The current Stage 1 firmware has been tested on the Waveshare ESP32-S3-Nano with MicroPython v1.28.0. The board successfully connects to Wi-Fi, establishes an MQTT session with ThingsBoard and publishes telemetry to `v1/devices/me/telemetry`.

The next development target is robust communications handling: reconnection logic, timeout detection, malformed-message handling and safe default behaviour after reset or reconnection.
