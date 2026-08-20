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
            print("[Wi-Fi] Already connected. IP:", self.wlan.ifconfig()[0])
            return True

        print("[Wi-Fi] Connecting to", config.WIFI_SSID)

        # Start from a clean station state. A short pause helps after resets or
        # failed DHCP attempts on some access points.
        try:
            self.wlan.disconnect()
        except Exception:
            pass
        time.sleep_ms(500)

        try:
            self.wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
        except Exception as exc:
            print("[Wi-Fi] Connect call failed:", exc)
            return False

        deadline = time.ticks_add(
            time.ticks_ms(), config.WIFI_CONNECT_TIMEOUT_S * 1000
        )
        last_status = None

        while not self.is_connected():
            status = self.wlan.status()
            if status != last_status:
                print("[Wi-Fi] Status:", status)
                last_status = status

            # Negative status codes represent terminal failures on ESP32.
            # Do not wait for the entire timeout if association has already failed.
            if status < 0:
                print("[Wi-Fi] Connection failed with status:", status)
                return False

            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                # One final check avoids a race where DHCP completes exactly at
                # the timeout boundary.
                if self.wlan.isconnected():
                    break
                print("[Wi-Fi] Connection timed out. Last status:", status)
                return False

            time.sleep_ms(500)

        print("[Wi-Fi] Connected. IP:", self.wlan.ifconfig()[0])
        return True

    def disconnect(self):
        try:
            self.wlan.disconnect()
        except Exception:
            pass

    def ensure_connected(self):
        if self.is_connected():
            return True

        print("[Wi-Fi] Connection lost; retrying...")
        time.sleep(config.WIFI_RETRY_DELAY_S)
        return self.connect()
