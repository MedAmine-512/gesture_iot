import paho.mqtt.client as mqtt
import time

broker = "test.mosquitto.org"
devices = {"light": False, "fan": False, "alarm": False}

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker\n")
        client.subscribe("home/#")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    
    print(f"\n🎯 Command Received!")
    print(f"Topic: {topic}")
    print(f"Command: {payload}\n")
    
    if "light" in topic:
        devices["light"] = (payload == "ON")
        status = "💡 LIGHT TURNED ON" if payload == "ON" else "💡 LIGHT TURNED OFF"
        print(status)
    
    elif "fan" in topic:
        devices["fan"] = (payload == "ON")
        status = "🌀 FAN TURNED ON" if payload == "ON" else "🌀 FAN TURNED OFF"
        print(status)
    
    elif "alarm" in topic:
        if payload == "ON":
            print("🔔 ALARM TRIGGERED! BEEP BEEP BEEP!")
            for i in range(3):
                print("   📢 ALERT!")
                time.sleep(0.3)
        else:
            print("🔔 Alarm OFF")
    
    print("\n📊 Current Device States:")
    print(f"   💡 Light: {'ON' if devices['light'] else 'OFF'}")
    print(f"   🌀 Fan: {'ON' if devices['fan'] else 'OFF'}")
    print(f"   🔔 Alarm: {'OFF'}\n")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "gesture_receiver")
client.on_connect = on_connect
client.on_message = on_message

print("📡 Connecting to MQTT Broker...")
client.connect(broker, 1883, keepalive=60)
client.loop_start()

print("⏳ Waiting for gestures... Make hand gestures in other terminal!")
print("Press Ctrl+C to stop\n")

try:
    while True:
        time.sleep(5)
except KeyboardInterrupt:
    print("\n\n✅ Receiver stopped")
    client.loop_stop()