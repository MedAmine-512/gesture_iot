"""
Test MQTT connection and subscribe to all home topics
"""
import paho.mqtt.client as mqtt
import time

MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(" Connected to MQTT Broker!")
        client.subscribe("home/#")
    else:
        print(f"Connection failed: {rc}")

def on_message(client, userdata, msg):
    print(f" {msg.topic}: {msg.payload.decode()}")

def test_mqtt():
    client = mqtt.Client(client_id="mqtt_test")

    client.on_connect = on_connect
    client.on_message = on_message
    
    print(f"Connecting to {MQTT_BROKER}...")
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()
    
    print("Listening f")
    time.sleep(1)
    
    client.loop_stop()
    print("Test complete!")

if __name__ == "__main__":
    test_mqtt()