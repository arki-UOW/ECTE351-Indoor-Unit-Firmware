"""Wi-Fi connection management for the ESP32-S3 indoor unit."""

import network
import time

import config


class WiFiManager:
    def __init__(self):
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)

    def is_connected(self):
        return self.wlan.isconnected()

    def connect(self):
        if self.is_connected():
            return True

        print("[Wi-Fi] Connecting to", config.WIFI_SSID)
        self.wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)

        deadline = time.ticks_add(
            time.ticks_ms(), config.WIFI_CONNECT_TIMEOUT_S * 1000
        )

        while not self.is_connected():
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                print("[Wi-Fi] Connection timed out")
                return False
            time.sleep_ms(250)

        print("[Wi-Fi] Connected. IP:", self.wlan.ifconfig()[0])
        return True

    def disconnect(self):
        if self.is_connected():
            self.wlan.disconnect()

    def ensure_connected(self):
        if self.is_connected():
            return True

        try:
            self.wlan.disconnect()
        except Exception:
            pass

        return self.connect()
