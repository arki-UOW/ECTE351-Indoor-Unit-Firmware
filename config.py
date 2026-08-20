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

# Sensor buses will be locked down in the sensor-integration stage.
I2C_ID = 0
I2C_SCL_PIN = None
I2C_SDA_PIN = None
I2C_FREQ_HZ = 100000

UART_ID = 1
UART_TX_PIN = None
UART_RX_PIN = None
UART_BAUDRATE = 9600
