"""Desktop regression tests for MQTT message handling and failure recovery."""

import importlib
import json
import sys
import types


# Provide desktop stubs before importing mqtt_manager.py.
config = types.ModuleType("config")
config.MQTT_CLIENT_ID = "test-client"
config.THINGSBOARD_HOST = "example.invalid"
config.THINGSBOARD_PORT = 1883
config.THINGSBOARD_ACCESS_TOKEN = "test-token"
config.MQTT_KEEPALIVE_S = 60
config.MQTT_HEALTHCHECK_INTERVAL_S = 30
sys.modules["config"] = config

umqtt = types.ModuleType("umqtt")
umqtt_simple = types.ModuleType("umqtt.simple")


class DummyMQTTClient:
    def __init__(self, *args, **kwargs):
        self.callback = None
        self.published = []
        self.ping_count = 0
        self.fail_ping = False
        self.fail_check = None

    def set_callback(self, callback):
        self.callback = callback

    def connect(self):
        return 0

    def subscribe(self, topic):
        self.subscribed = topic

    def disconnect(self):
        pass

    def publish(self, topic, message):
        self.published.append((topic, message))

    def check_msg(self):
        if self.fail_check is not None:
            raise self.fail_check

    def ping(self):
        self.ping_count += 1
        if self.fail_ping:
            raise OSError(113)


umqtt_simple.MQTTClient = DummyMQTTClient
sys.modules["umqtt"] = umqtt
sys.modules["umqtt.simple"] = umqtt_simple

mqtt_manager = importlib.import_module("mqtt_manager")


class FakeTime:
    now = 100000

    @classmethod
    def ticks_ms(cls):
        return cls.now

    @staticmethod
    def ticks_diff(new, old):
        return new - old


mqtt_manager.time.ticks_ms = FakeTime.ticks_ms
mqtt_manager.time.ticks_diff = FakeTime.ticks_diff


def assert_true(value, message):
    if not value:
        raise AssertionError(message)


def run():
    manager = mqtt_manager.MQTTManager()
    manager.client = DummyMQTTClient()
    manager.connected = True

    received = []
    manager.set_rpc_callback(lambda topic, payload: received.append((topic, payload)))

    # Valid bytes JSON is decoded and delivered.
    manager._on_message(
        b"v1/devices/me/rpc/request/1",
        b'{"method":"set_mode","params":{"mode":"auto"}}',
    )
    assert_true(len(received) == 1, "valid RPC was not delivered")
    assert_true(received[0][1]["method"] == "set_mode", "valid RPC decoded incorrectly")

    # Malformed JSON must be ignored without invoking the handler.
    manager._on_message(b"v1/devices/me/rpc/request/2", b'{"method":')
    assert_true(len(received) == 1, "malformed JSON reached RPC handler")

    # Valid JSON with a non-object top-level payload must also be ignored.
    manager._on_message(b"v1/devices/me/rpc/request/3", b'["set_mode"]')
    assert_true(len(received) == 1, "non-object JSON reached RPC handler")

    # RPC responses must use the matching request ID.
    assert_true(
        manager.publish_rpc_response(
            b"v1/devices/me/rpc/request/42", {"success": True, "mode": "AUTO"}
        ),
        "RPC response publish failed",
    )
    topic, message = manager.client.published[-1]
    assert_true(topic == b"v1/devices/me/rpc/response/42", "wrong RPC response topic")
    decoded = json.loads(message)
    assert_true(decoded["success"] is True, "RPC response payload incorrect")

    # Idle OSError(-1) is not treated as a disconnect.
    manager.client.fail_check = OSError(-1)
    assert_true(manager.check_messages() is True, "idle poll was treated as a failure")
    assert_true(manager.connected is True, "idle poll disconnected MQTT")

    # Real socket error must mark the connection dead for reconnection.
    manager.client.fail_check = OSError(113)
    assert_true(manager.check_messages() is False, "socket failure was not detected")
    assert_true(manager.connected is False, "socket failure did not clear connection state")

    # Recreate a healthy connection and verify active PING health checking.
    manager.client = DummyMQTTClient()
    manager.connected = True
    manager.last_healthcheck_ms = 0
    assert_true(manager.health_check(force=True) is True, "healthy MQTT ping failed")
    assert_true(manager.client.ping_count == 1, "MQTT ping was not sent")

    # Failed PING must clear the connection so ensure_connected can recover it.
    manager.client.fail_ping = True
    assert_true(manager.health_check(force=True) is False, "failed MQTT ping was not detected")
    assert_true(manager.connected is False, "failed MQTT ping did not clear connection state")

    print("comms_logic_test: PASS")


if __name__ == "__main__":
    run()
