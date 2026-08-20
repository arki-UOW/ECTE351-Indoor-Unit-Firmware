"""Non-secret configuration for the ECTE351 indoor unit.

Real Wi-Fi credentials and the ThingsBoard access token live in secrets.py.
secrets.py is intentionally excluded from Git so credentials are never committed.
"""

from secrets import WIFI_SSID, WIFI_PASSWORD, THINGSBOARD_ACCESS_TOKEN

THINGSBOARD_HOST = "mqtt.thingsboard.cloud"
THINGSBOARD_PORT = 1883
MQTT_CLIENT_ID = "esp32s3-nano"

# Some access points take longer to complete association/DHCP after ESP32 reset.
WIFI_CONNECT_TIMEOUT_S = 60
WIFI_RETRY_DELAY_S = 2
MQTT_KEEPALIVE_S = 60
TELEMETRY_INTERVAL_S = 5

# Safe runtime defaults applied after boot/reset.
DEFAULT_OPERATING_MODE = "AUTO"
DEFAULT_MANUAL_OVERRIDE = False
DEFAULT_VENTILATION_REQUEST = False
DEFAULT_SYSTEM_CONDITION = "INITIALISING"

# RGB LED pins from the recovered working firmware.
# Common anode: LOW = on, HIGH = off.
LED_R_PIN = 14
LED_G_PIN = 16
LED_B_PIN = 15

# ---------------------------------------------------------------------------
# Indoor sensor interface contract
# Target board: Waveshare ESP32-S3-Nano (Arduino Nano ESP32-compatible pinout)
# ---------------------------------------------------------------------------
I2C_ID = 0
I2C_SDA_PIN = 11   # board label A4
I2C_SCL_PIN = 12   # board label A5
I2C_FREQ_HZ = 100000

BME680_I2C_ADDRESS = 0x77
SGP40_I2C_ADDRESS = 0x59
SCD30_I2C_ADDRESS = 0x61
MLX90614_I2C_ADDRESS = 0x5A

# mmWave presence sensor interface.
MMWAVE_UART_ID = 1
MMWAVE_UART_TX_PIN = 17   # board label D8 -> sensor RX
MMWAVE_UART_RX_PIN = 18   # board label D9 -> sensor TX
MMWAVE_OUT_PIN = 5        # board label D2 -> sensor OUT
MMWAVE_UART_BAUDRATE = None

# ---------------------------------------------------------------------------
# Sensor-processing configuration
# These ranges are sanity/validity limits, not comfort thresholds.
# ---------------------------------------------------------------------------
SENSOR_FILTER_WINDOW = 3
SENSOR_STALE_TIMEOUT_MS = 15000

SENSOR_VALID_RANGES = {
    "temperature_c": (-20.0, 60.0),
    "humidity_pct": (0.0, 100.0),
    "pressure_hpa": (300.0, 1100.0),
    "voc_index": (0.0, 500.0),
    "co2_ppm": (250.0, 10000.0),
    "surface_temperature_c": (-70.0, 380.0),
}

# ---------------------------------------------------------------------------
# Environmental targets recovered from the Autumn project material.
# Temperature hysteresis: activate above 24 C, clear only below 22 C.
# Humidity hysteresis: high-risk above 60 %RH, clear only below 55 %RH.
# Occupied-space CO2 target: below 1000 ppm.
# Mould-risk target: maintain RH within 40-60 %RH over 24 h.
# No numeric VOC action threshold was specified in the recovered Autumn
# material, so VOC remains monitored/validated but does not independently
# change the environmental state yet.
# ---------------------------------------------------------------------------
TEMPERATURE_HIGH_ON_C = 24.0
TEMPERATURE_HIGH_OFF_C = 22.0

HUMIDITY_TARGET_MIN_PCT = 40.0
HUMIDITY_HIGH_ON_PCT = 60.0
HUMIDITY_HIGH_OFF_PCT = 55.0

CO2_OCCUPIED_LIMIT_PPM = 1000.0
