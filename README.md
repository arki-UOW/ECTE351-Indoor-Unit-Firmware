# ECTE351 Indoor Unit Firmware

MicroPython firmware for the ECTE351 Smart Ventilation System indoor unit.

Target controller: Waveshare ESP32-S3-Nano running MicroPython.

## Current hardware

- BME680 — temperature, humidity, pressure and gas resistance
- Adafruit SGP40 — raw VOC signal / air-quality sensing
- Sensirion SCD30 — CO2, temperature and humidity
- MLX90614 — infrared surface/object temperature
- Waveshare HMMD-mmWave-Sensor — occupancy / presence detection

## Verified ESP32-S3-Nano interface map

| Function | Nano header pin | ESP32-S3 GPIO | Firmware use |
| --- | --- | ---: | --- |
| I2C SDA | A4 | GPIO11 | Shared SDA for BME680, SGP40, SCD30 and MLX90614 |
| I2C SCL | A5 | GPIO12 | Shared SCL for BME680, SGP40, SCD30 and MLX90614 |
| mmWave UART TX | D8 | GPIO17 | ESP32 TX -> HMMD RX; reserved, not physically connected yet |
| mmWave UART RX | D9 | GPIO18 | ESP32 RX <- HMMD TX; reserved, not physically connected yet |
| mmWave digital OUT | D2 | GPIO5 | HMMD OT2 occupancy output -> ESP32 input |
| RGB LED red | On-board | GPIO46 | Common-anode red channel; LOW = on |
| RGB LED green | On-board | GPIO0 | Common-anode green channel; LOW = on |
| RGB LED blue | On-board | GPIO45 | Common-anode blue channel; LOW = on |
| Ground | GND | GND | Common ground for the indoor sensors |

Shared I2C configuration:

- bus: `I2C(0)`
- frequency: `100000` Hz (100 kHz)
- BME680 address: `0x77`
- SGP40 address: `0x59`
- SCD30 address: `0x61`
- MLX90614 address: `0x5A`

BME680 breakout in I2C mode:

- `SCK -> A5 / GPIO12`
- `SDI -> A4 / GPIO11`
- `CS -> 3.3 V`
- `SDO -> 3.3 V` for address `0x77`

Waveshare HMMD-mmWave-Sensor:

- `OT2 -> D2 / GPIO5`
- UART default baud rate: `115200`
- `D8 / GPIO17 -> HMMD RX` and `D9 / GPIO18 <- HMMD TX` are reserved for later UART validation
- UART is runtime-disabled until those two wires are physically connected

### RGB LED note

The on-board Waveshare RGB LED is common-anode and is mapped as red=`GPIO46`, green=`GPIO0`, blue=`GPIO45`. `GPIO0` and `GPIO46` are ESP32-S3 strapping pins, so the firmware treats the RGB LED as a runtime status indicator only after normal boot.

## Current status

### Communications and control — verified

- Wi-Fi connection verified on the ESP32-S3-Nano.
- MQTT connection to ThingsBoard verified using the assigned host, port and access token.
- End-to-end telemetry publishing verified.
- Wi-Fi loss and automatic reconnection verified.
- MQTT socket failure after Wi-Fi loss and automatic MQTT reconnection verified.
- Default startup/reset state verified: `AUTO`, no manual override, no ventilation request, `INITIALISING` condition.
- Live ThingsBoard RPC dashboard control verified end-to-end.
- All six valid dashboard modes verified: `AUTO`, `MANUAL`, `SLEEP`, `WORK`, `ENERGY_SAVING`, `PURGE`.
- Invalid modes and unsupported RPC methods are rejected safely without breaking later valid commands.

### Sensor software logic — verified with simulated inputs

- Sensor validity rejection and per-field health states.
- Stale-data detection.
- 3-sample moving-average filtering.
- Environmental outputs: `NORMAL`, `WARNING`, `ACTION_REQUIRED`, `MOULD_RISK`.
- Temperature hysteresis: high condition enters above 24 C and clears below 22 C.
- Humidity hysteresis: mould-risk condition enters above 60 %RH and clears below 55 %RH.
- Occupied-space CO2 action threshold at 1000 ppm.
- Edge-case regression suite passes.

### Individual physical sensor breadboard verification — complete

- MLX90614: detected at `0x5A`; ambient/object readings verified; object temperature responds to applied heat. ✅
- SGP40: detected at `0x59`; continuous raw VOC signal verified; signal responds strongly to hand-sanitiser vapour. ✅
- SCD30: detected at `0x61`; live CO2/temperature/humidity verified; CO2 and humidity respond strongly to breath exposure. ✅
- BME680: detected at `0x77`; compensated temperature/humidity/pressure/gas readings verified with the validated driver; environmental responses confirmed. ✅
- Waveshare HMMD-mmWave-Sensor: OT2 digital presence on `D2/GPIO5` verified for presence and absence. ✅

### Full subsystem integration — current test stage

All sensors are now physically connected together on the breadboard. The `full-indoor-integration` branch replaces the sensor placeholders with live hardware reads and connects the live sensor pipeline to the existing ThingsBoard/MQTT system.

Remaining hardware validation before merging:

1. Confirm simultaneous shared-I2C detection of `0x59`, `0x5A`, `0x61`, `0x77`.
2. Confirm all live values remain believable while the complete sensor set is connected.
3. Confirm HMMD OT2 occupancy continues working while the I2C sensors are active.
4. Confirm live sensor telemetry reaches ThingsBoard continuously.
5. Re-run ThingsBoard RPC controls while sensor telemetry is active.
6. Test sensor removal/loose-wire fault reporting and recovery.
7. Connect HMMD UART TX/RX and validate UART communication separately before enabling it in runtime firmware.

## Firmware modules

- `boot.py` - minimal boot-time setup
- `main.py` - complete application loop, live sensor processing, ThingsBoard telemetry and RPC handler
- `config.py` - non-secret firmware configuration, interface assignments and thresholds
- `secrets.py` - local Wi-Fi and ThingsBoard credentials; intentionally ignored by Git
- `secrets.example.py` - safe template for local secrets
- `wifi_manager.py` - Wi-Fi connection/reconnection
- `mqtt_manager.py` - ThingsBoard MQTT connection, telemetry, RPC subscription and RPC responses
- `bme680_driver.py` - physically validated BME680 I2C compensation driver
- `sensors.py` - shared-bus initialisation and live BME680/SGP40/SCD30/MLX90614/HMMD readings
- `sensor_processing.py` - validation, filtering and health/status handling
- `environment_logic.py` - environmental thresholds, hysteresis and state generation
- `mode_logic.py` - operating mode and ventilation decisions
- `diagnostics.py` - fault reporting and health checks
- `tests/sensor_logic_smoke_test.py` - repeatable desktop smoke tests
- `tests/sensor_logic_regression_test.py` - edge-case regression tests
- `docs/VALIDATION.md` - detailed software and communications verification record

## SGP40 telemetry note

The current firmware publishes `sgp40_raw_signal`. This is the physical SGP40 raw measurement and must not be interpreted as Sensirion's processed VOC Index. A proper VOC Index algorithm can be integrated later; until then, the raw signal is monitored and telemetried but does not independently trigger an environmental state.

## Security

Never commit real Wi-Fi passwords or ThingsBoard access tokens. Copy `secrets.example.py` to `secrets.py` locally and enter credentials there. `secrets.py` is ignored by Git.
