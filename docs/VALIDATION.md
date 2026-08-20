# Validation Record

This file records repeatable verification completed for the ECTE351 indoor-unit firmware. It is intended to separate proven behaviour from integration work that still depends on physical hardware.

## Sensor-processing and environmental logic

Desktop tests with simulated inputs passed using:

```powershell
python tests/sensor_logic_smoke_test.py
python tests/sensor_logic_regression_test.py
```

Verified behaviour:

- valid readings accepted and marked `VALID`;
- invalid/out-of-range readings rejected;
- health transition `VALID -> INVALID -> STALE -> VALID` verified;
- 3-sample moving-average filter verified;
- occupied CO2 boundary at 1000 ppm verified;
- temperature hysteresis verified: enter above 24 C, clear below 22 C;
- humidity hysteresis verified: enter above 60 %RH, clear below 55 %RH;
- low-humidity warning behaviour verified;
- simultaneous environmental conditions follow the defined priority;
- exact boundaries and recovery paths covered by regression tests.

These are software-only tests. Live sensor wiring, calibration, I2C/UART compatibility and long-run hardware behaviour remain integration tasks.

## Wi-Fi / MQTT / ThingsBoard

Verified on the Waveshare ESP32-S3-Nano running MicroPython v1.28.0:

- Wi-Fi connection established;
- MQTT connection to ThingsBoard established;
- telemetry publishing verified;
- deliberate Wi-Fi loss detected and recovered;
- MQTT socket failure after Wi-Fi loss detected and MQTT reconnected;
- safe startup/default state verified.

## ThingsBoard RPC dashboard validation

Live end-to-end RPC testing was completed using the ThingsBoard dashboard. The device subscribed to:

```text
v1/devices/me/rpc/request/+
```

The dashboard used the method `set_mode` with parameters such as:

```json
{"mode":"auto"}
```

The following valid mode commands were received by the ESP32, applied successfully and acknowledged on the matching RPC response topic:

- `auto`
- `manual`
- `sleep`
- `work`
- `energy_saving`
- `purge`

Negative tests also passed:

- unsupported mode `invalid_mode` was rejected with `unsupported_mode`;
- unsupported RPC methods were rejected with `unsupported_method`;
- the MQTT loop remained alive after rejected commands;
- a subsequent valid `auto` command succeeded, proving recovery after invalid RPC traffic.

A malformed non-object `params` payload could not be generated through the ThingsBoard dashboard because the dashboard rejected that format before transmission. The firmware still contains a defensive check for non-object parameters.

## Remaining integration validation

The following items cannot be considered proven until physical integration:

- all sensors operating simultaneously on the real bus;
- live sensor values replacing simulated inputs;
- sensor calibration and warm-up behaviour;
- mmWave UART/digital output verification;
- electrical/power integrity;
- long-run stability with sensors + Wi-Fi + MQTT + RPC active together;
- final indoor-to-outdoor ventilation command integration.
