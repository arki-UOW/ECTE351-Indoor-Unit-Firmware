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
- Wi-Fi loss and automatic reconnection verified.
- MQTT socket failure after Wi-Fi loss and automatic MQTT reconnection verified.
- Modular firmware architecture established.
- Malformed-message handling, reset defaults and broader communications validation remain to be tested.

## Development approach

1. Verify Wi-Fi connectivity. ✅
2. Verify MQTT/ThingsBoard connectivity. ✅
3. Implement Wi-Fi/MQTT reconnection and timeout handling. ✅ (malformed-message test still pending)
4. Define and validate default behaviour after reset/reconnection.
5. Validate communications handling under simulated failure conditions.
6. Confirm final GPIO/interface map.
7. Integrate sensors individually and verify bus compatibility.
8. Replace simulated values with live sensor data.
9. Process and validate sensor data.
10. Add environmental and operating-mode logic.
11. Add diagnostics/fault handling.
12. Perform full end-to-end integration testing.

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

## Communications verification

The current communications firmware has been tested on the Waveshare ESP32-S3-Nano with MicroPython v1.28.0. The board successfully connects to Wi-Fi, establishes an MQTT session with ThingsBoard and publishes telemetry to `v1/devices/me/telemetry`.

A deliberate Wi-Fi outage was also tested. The firmware detected the Wi-Fi loss, reconnected when the network became available again, detected the stale MQTT socket (`ECONNABORTED`) and automatically established a new MQTT connection.

During development, an Optus access point repeatedly returned MicroPython status `202` (`STAT_WRONG_PASSWORD`) despite the credential being confirmed. The same firmware connected successfully through an iPhone hotspot, proving the ESP32 Wi-Fi/MQTT firmware path. Router compatibility can be investigated separately if required.

## Security

Never commit real Wi-Fi passwords or ThingsBoard access tokens. Copy `secrets.example.py` to `secrets.py` locally and enter credentials there. `secrets.py` is ignored by Git.
