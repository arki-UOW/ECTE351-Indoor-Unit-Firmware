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
#
# Shared I2C bus:
#   A4 / GPIO11 -> SDA
#   A5 / GPIO12 -> SCL
#
# The four I2C sensors have unique addresses and therefore share one bus.
# Physical wiring and bus validation are performed separately during hardware
# integration; these assignments define the firmware-side contract.
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
# Module pins observed: 3V3, GND, TX, RX, OUT.
# Reserve UART1 on D8/D9 and a separate digital input for OUT.
# Sensor TX connects to ESP RX; sensor RX connects to ESP TX.
MMWAVE_UART_ID = 1
MMWAVE_UART_TX_PIN = 17   # board label D8 -> sensor RX
MMWAVE_UART_RX_PIN = 18   # board label D9 -> sensor TX
MMWAVE_OUT_PIN = 5        # board label D2 -> sensor OUT

# Exact UART baud/protocol depends on the specific HMMD mmWave module firmware
# and will be confirmed during physical integration.
MMWAVE_UART_BAUDRATE = None
