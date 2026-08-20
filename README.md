# ECTE351 Indoor Unit Firmware

MicroPython firmware for the ECTE351 Smart Ventilation System indoor unit.

Target hardware: ESP32-S3.

Development approach:
1. Verify Wi-Fi connectivity.
2. Verify MQTT/ThingsBoard connectivity.
3. Add robust reconnect/default handling.
4. Integrate sensors.
5. Process and validate sensor data.
6. Add environmental and operating-mode logic.
7. Add diagnostics/fault handling.
8. Perform full end-to-end integration testing.

## Planned firmware modules

- `boot.py` - minimal boot-time setup
- `main.py` - top-level application loop
- `config.py` - configuration placeholders; do not commit real credentials
- `wifi_manager.py` - Wi-Fi connection/reconnection
- `mqtt_manager.py` - ThingsBoard MQTT connection and telemetry
- `sensors.py` - sensor initialisation and raw readings
- `sensor_processing.py` - validation/filtering/status handling
- `environment_logic.py` - thresholds, hysteresis, environment state
- `mode_logic.py` - operating mode and ventilation decisions
- `diagnostics.py` - fault reporting and health checks

## Security

Do not commit real Wi-Fi passwords or ThingsBoard access tokens. Replace placeholders only in the local working copy used for flashing/testing.
