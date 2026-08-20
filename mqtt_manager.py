"""ThingsBoard MQTT communications for the ECTE351 indoor unit."""

import json

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

    def _on_message(self, topic, message):
        print("[MQTT] RX:", topic, message)
        if self.rpc_callback is not None:
            try:
                payload = json.loads(message)
                self.rpc_callback(topic, payload)
            except Exception as exc:
                print("[MQTT] Invalid message:", exc)

    def connect(self):
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
            self.connected = False
            print("[MQTT] Connection failed:", exc)
            return False

    def disconnect(self):
        if self.client is not None:
            try:
                self.client.disconnect()
            except Exception:
                pass
        self.connected = False

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
            self.connected = False
            print("[MQTT] Publish failed:", exc)
            return False

    def publish_attributes(self, payload):
        if not self.ensure_connected():
            return False
        try:
            self.client.publish(ATTRIBUTES_TOPIC, json.dumps(payload))
            return True
        except Exception as exc:
            self.connected = False
            print("[MQTT] Attribute publish failed:", exc)
            return False

    def check_messages(self):
        if not self.connected or self.client is None:
            return False
        try:
            self.client.check_msg()
            return True
        except Exception as exc:
            self.connected = False
            print("[MQTT] Message check failed:", exc)
            return False
