"""ThingsBoard MQTT communications for the ECTE351 indoor unit."""

import json
import time

from umqtt.simple import MQTTClient

import config


TELEMETRY_TOPIC = b"v1/devices/me/telemetry"
ATTRIBUTES_TOPIC = b"v1/devices/me/attributes"
RPC_REQUEST_TOPIC = b"v1/devices/me/rpc/request/+"


class MQTTManager:
    def __init__(self):
        self.client = None
        self.connected = False
        self.rpc_callback = None
        self.last_connect_attempt_ms = 0
        self.reconnect_delay_ms = 3000

    def _on_message(self, topic, message):
        print("[MQTT] RX:", topic, message)
        if self.rpc_callback is not None:
            try:
                payload = json.loads(message)
                self.rpc_callback(topic, payload)
            except Exception as exc:
                print("[MQTT] Invalid message ignored:", exc)

    def _cleanup_client(self):
        if self.client is not None:
            try:
                self.client.disconnect()
            except Exception:
                pass
        self.client = None
        self.connected = False

    def connect(self, force=False):
        now = time.ticks_ms()

        if not force and self.last_connect_attempt_ms:
            elapsed = time.ticks_diff(now, self.last_connect_attempt_ms)
            if elapsed < self.reconnect_delay_ms:
                return False

        self.last_connect_attempt_ms = now
        self._cleanup_client()

        print("[MQTT] Connecting to ThingsBoard...")
        try:
            self.client = MQTTClient(
                client_id=config.MQTT_CLIENT_ID,
                server=config.THINGSBOARD_HOST,
                port=config.THINGSBOARD_PORT,
                user=config.THINGSBOARD_ACCESS_TOKEN,
                password="",
                keepalive=config.MQTT_KEEPALIVE_S,
            )
            self.client.set_callback(self._on_message)
            self.client.connect()
            self.client.subscribe(RPC_REQUEST_TOPIC)
            self.connected = True
            print("[MQTT] Connected")
            return True
        except Exception as exc:
            self._cleanup_client()
            print("[MQTT] Connection failed:", exc)
            return False

    def disconnect(self):
        self._cleanup_client()

    def ensure_connected(self):
        if self.connected and self.client is not None:
            return True
        return self.connect()

    def publish_telemetry(self, payload):
        if not self.ensure_connected():
            return False
        try:
            message = json.dumps(payload)
            self.client.publish(TELEMETRY_TOPIC, message)
            print("[MQTT] Telemetry:", message)
            return True
        except Exception as exc:
            print("[MQTT] Publish failed:", exc)
            self._cleanup_client()
            return False

    def publish_attributes(self, payload):
        if not self.ensure_connected():
            return False
        try:
            self.client.publish(ATTRIBUTES_TOPIC, json.dumps(payload))
            return True
        except Exception as exc:
            print("[MQTT] Attribute publish failed:", exc)
            self._cleanup_client()
            return False

    def check_messages(self):
        if not self.connected or self.client is None:
            return False

        try:
            self.client.check_msg()
            return True
        except OSError as exc:
            # On ESP32 MicroPython, umqtt.simple may raise OSError(-1)
            # when a non-blocking check has no message available. That is
            # an idle condition, not a lost MQTT session.
            errno = exc.args[0] if exc.args else None
            if errno == -1:
                return True

            print("[MQTT] Socket error:", exc)
            self._cleanup_client()
            return False
        except Exception as exc:
            print("[MQTT] Message check failed:", exc)
            self._cleanup_client()
            return False
