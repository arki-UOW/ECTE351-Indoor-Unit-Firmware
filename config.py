"""Configuration for the ECTE351 indoor unit.

IMPORTANT: keep real passwords and ThingsBoard tokens out of GitHub.
Replace these placeholders only in the local copy used for flashing/testing.
"""

WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

THINGSBOARD_HOST = "YOUR_THINGSBOARD_HOST"
THINGSBOARD_PORT = 1883
THINGSBOARD_ACCESS_TOKEN = "YOUR_DEVICE_ACCESS_TOKEN"
MQTT_CLIENT_ID = "ECTE351_Indoor_ESP32S3"

WIFI_CONNECT_TIMEOUT_S = 20
MQTT_KEEPALIVE_S = 60
TELEMETRY_INTERVAL_S = 2

# Sensor bus placeholders. Update after final pin assignment is confirmed.
I2C_ID = 0
I2C_SCL_PIN = None
I2C_SDA_PIN = None
I2C_FREQ_HZ = 100000

UART_ID = 1
UART_TX_PIN = None
UART_RX_PIN = None
UART_BAUDRATE = 9600
