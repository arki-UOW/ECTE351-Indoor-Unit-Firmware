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
- End-to-end telemetry publishing verified.
- Wi-Fi loss and automatic reconnection verified.
- MQTT socket failure after Wi-Fi loss and automatic MQTT reconnection verified.
- Default startup/reset state verified: `AUTO`, no manual override, no ventilation request, `INITIALISING` condition.
- Live ThingsBoard RPC dashboard control verified end-to-end.
- All six valid dashboard modes verified: `AUTO`, `MANUAL`, `SLEEP`, `WORK`, `ENERGY_SAVING`, `PURGE`.
- Invalid modes and unsupported RPC methods are rejected safely with an RPC response; a subsequent valid command still succeeds.
- Modular firmware architecture established.
- Firmware-side GPIO/interface map confirmed for the shared I2C sensors and mmWave interface.
- Sensor-processing logic verified with simulated inputs: validity rejection, per-field health state, stale-data detection and 3-sample moving-average filtering.
- Environmental-condition outputs verified with simulated inputs: `NORMAL`, `WARNING`, `ACTION_REQUIRED`, `MOULD_RISK`.
- Temperature hysteresis verified: high condition enters above 24 C and clears below 22 C.
- Humidity hysteresis verified: mould-risk condition enters above 60 %RH and clears below 55 %RH.
- Occupied-space CO2 action threshold implemented at 1000 ppm.
- Edge-case regression suite passes.
- Physical sensor integration, live readings, calibration and bus-compatibility validation remain pending.

## Development approach

1. Verify Wi-Fi connectivity. ✅
2. Verify MQTT/ThingsBoard connectivity. ✅
3. Implement Wi-Fi/MQTT reconnection and timeout handling. ✅
4. Define and validate default behaviour after reset/reconnection. ✅
5. Validate dashboard/RPC communications and rejection of invalid commands. ✅
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
- `main.py` - top-level application loop and RPC command handler
- `config.py` - non-secret firmware configuration, interface assignments and thresholds
- `secrets.py` - local Wi-Fi and ThingsBoard credentials; intentionally ignored by Git
- `secrets.example.py` - safe template for local secrets
- `wifi_manager.py` - Wi-Fi connection/reconnection
- `mqtt_manager.py` - ThingsBoard MQTT connection, telemetry, RPC subscription and RPC responses
- `sensors.py` - sensor initialisation and raw readings
- `sensor_processing.py` - validation, filtering and health/status handling
- `environment_logic.py` - environmental thresholds, hysteresis and state generation
- `mode_logic.py` - operating mode and ventilation decisions
- `diagnostics.py` - fault reporting and health checks
- `tests/sensor_logic_smoke_test.py` - repeatable desktop smoke tests
- `tests/sensor_logic_regression_test.py` - edge-case regression tests
- `docs/VALIDATION.md` - detailed record of completed software and live communications verification

## Sensor-processing verification

Desktop tests using simulated sensor readings verify the current processing and environmental logic independently of the physical sensors.

Verified behaviour includes:

- valid readings accepted and marked `VALID`;
- missing or physically implausible readings rejected;
- `VALID -> INVALID -> STALE -> VALID` health recovery;
- 3-sample moving-average filtering and rolling-window behaviour;
- occupied CO2 behaviour around the 1000 ppm boundary;
- temperature and humidity hysteresis boundaries;
- environmental-state priority when multiple conditions are active;
- validity-range endpoints and invalid occupancy data types.

Run from the repository root:

```powershell
python tests/sensor_logic_smoke_test.py
python tests/sensor_logic_regression_test.py
```

Both should finish with a `PASS` line.

## Communications verification

The firmware has been tested live on the Waveshare ESP32-S3-Nano with MicroPython v1.28.0. The board connects to Wi-Fi, establishes MQTT with ThingsBoard, publishes telemetry and recovers after a deliberate Wi-Fi outage and stale MQTT socket.

ThingsBoard dashboard RPC testing is also complete. The device subscribes to:

```text
v1/devices/me/rpc/request/+
```

The dashboard `set_mode` command was verified for `auto`, `manual`, `sleep`, `work`, `energy_saving` and `purge`. Each command was received by the ESP32, applied, and acknowledged on the matching `v1/devices/me/rpc/response/<request_id>` topic.

Negative RPC tests verified that unsupported methods and unsupported modes are rejected without crashing or disconnecting the firmware. A valid `auto` command succeeded immediately after the rejected commands, confirming continued operation after invalid RPC traffic.

A malformed non-object `params` message could not be transmitted through the dashboard because ThingsBoard rejected that payload format before transmission. The firmware still includes defensive validation for that case.

## Development tooling note

On this ESP32-S3 development setup, `mpremote` can intermittently fail to enter raw REPL and report `TransportError: could not enter raw repl`, even while the normal serial REPL remains reachable. This has been treated as a development-tooling issue rather than a firmware validation failure. No artificial boot delay is used in production firmware; when file transfer fails, reconnect/reset the development session and retry the transfer.

## Security

Never commit real Wi-Fi passwords or ThingsBoard access tokens. Copy `secrets.example.py` to `secrets.py` locally and enter credentials there. `secrets.py` is ignored by Git.
