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
- Default startup/reset state verified: `AUTO` mode, no manual override, no ventilation request and `INITIALISING` system condition.
- Modular firmware architecture established.
- Firmware-side GPIO/interface map confirmed for the shared I2C sensors and mmWave interface.
- Sensor-processing logic verified with simulated inputs: validity rejection, per-field health state, stale-data detection and 3-sample moving-average filtering.
- Environmental-condition outputs verified with simulated inputs: `NORMAL`, `WARNING`, `ACTION_REQUIRED` and `MOULD_RISK`.
- Temperature hysteresis verified: high condition enters above 24 C and clears below 22 C.
- Humidity hysteresis verified: mould-risk condition enters above 60 %RH and clears below 55 %RH.
- Occupied-space CO2 action threshold implemented at 1000 ppm.
- Malformed-message handling and broader communications validation remain to be tested.
- Physical sensor integration, live readings, calibration and bus-compatibility validation remain pending.

## Development approach

1. Verify Wi-Fi connectivity. ✅
2. Verify MQTT/ThingsBoard connectivity. ✅
3. Implement Wi-Fi/MQTT reconnection and timeout handling. In progress — malformed-message test pending.
4. Define and validate default behaviour after reset/reconnection. ✅
5. Validate communications handling under simulated failure conditions.
6. Confirm final GPIO/interface map. ✅ firmware-side contract
7. Integrate sensors individually and verify bus compatibility. Pending physical integration.
8. Replace simulated values with live sensor data. Pending physical integration.
9. Process and validate sensor data. ✅ simulated-input verification complete
10. Add environmental logic. ✅ simulated-input verification complete
11. Add operating-mode and ventilation-decision logic.
12. Add diagnostics/fault handling.
13. Perform full end-to-end integration testing.

## Firmware modules

- `boot.py` - minimal boot-time setup
- `main.py` - top-level application loop
- `config.py` - non-secret firmware configuration, interface assignments and thresholds
- `secrets.py` - local Wi-Fi and ThingsBoard credentials; intentionally ignored by Git
- `secrets.example.py` - safe template for local secrets
- `wifi_manager.py` - Wi-Fi connection/reconnection
- `mqtt_manager.py` - ThingsBoard MQTT connection, telemetry and command handling
- `sensors.py` - sensor initialisation and raw readings
- `sensor_processing.py` - validation, filtering and health/status handling
- `environment_logic.py` - environmental thresholds, hysteresis and state generation
- `mode_logic.py` - operating mode and ventilation decisions
- `diagnostics.py` - fault reporting and health checks
- `tests/sensor_logic_smoke_test.py` - repeatable desktop smoke tests for the simulated sensor-processing/environment layer

## Sensor-processing verification

Desktop tests using simulated sensor readings have verified the current processing and environmental logic independently of the physical sensors.

Verified behaviour includes:

- valid readings are accepted and marked `VALID`;
- missing or physically implausible readings are rejected;
- sensor health progresses from `VALID` to `INVALID` and then `STALE` when valid data does not return before the configured timeout;
- the 3-sample moving-average filter produces the expected result (20 C, 26 C, 32 C -> 26 C);
- occupied CO2 at 1400 ppm produces `ACTION_REQUIRED`;
- humidity above 60 %RH produces `MOULD_RISK`;
- temperature above 24 C produces `ACTION_REQUIRED`;
- temperature remains in the high state through the deadband and clears below 22 C;
- humidity remains in mould-risk through the deadband and clears below 55 %RH;
- missing critical data produces `WARNING`.

These tests validate the software decision layer only. They do not replace live-sensor integration, calibration, electrical checks or I2C/UART bus validation.

To rerun the repeatable desktop smoke test from the repository root (with local `secrets.py` present):

```powershell
python tests/sensor_logic_smoke_test.py
```

## Communications verification

The current communications firmware has been tested on the Waveshare ESP32-S3-Nano with MicroPython v1.28.0. The board successfully connects to Wi-Fi, establishes an MQTT session with ThingsBoard and publishes telemetry to `v1/devices/me/telemetry`.

A deliberate Wi-Fi outage was also tested. The firmware detected the Wi-Fi loss, reconnected when the network became available again, detected the stale MQTT socket (`ECONNABORTED`) and automatically established a new MQTT connection.

The reset/default configuration was tested directly on the ESP32-S3-Nano. A new `ModeLogic` instance initializes to `AUTO`, `manual_override=False`, `ventilation_request=False` and `system_condition=INITIALISING`.

During development, an Optus access point repeatedly returned MicroPython status `202` (`STAT_WRONG_PASSWORD`) despite the credential being confirmed. The same firmware connected successfully through an iPhone hotspot, proving the ESP32 Wi-Fi/MQTT firmware path. Router compatibility can be investigated separately if required.

## Security

Never commit real Wi-Fi passwords or ThingsBoard access tokens. Copy `secrets.example.py` to `secrets.py` locally and enter credentials there. `secrets.py` is ignored by Git.
