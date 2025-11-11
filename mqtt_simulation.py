import paho.mqtt.client as mqtt
import time
import json
import math
import random
import requests

BROKER = "localhost"
PORT = 1883
NODERED_URL = "http://localhost:1880"

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "sensor_simulator")

device_states = {"light": "OFF", "fan": "OFF", "alarm": "OFF"}
sensor_values = {
    "temperature": 22.0,
    "humidity": 50.0,
    "light_intensity": 30.0,
    "current_light": 0.0,
    "current_fan": 0.0,
    "current_alarm": 0.0
}

ambient_temp = 22.0
time_started = time.time()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        client.subscribe("home/light")
        client.subscribe("home/fan")
        client.subscribe("home/alarm")
    else:
        print(f"Connection failed: {rc}")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    
    if "light" in topic:
        device_states["light"] = payload
        print(f"Light: {payload}")
    elif "fan" in topic:
        device_states["fan"] = payload
        print(f"Fan: {payload}")
    elif "alarm" in topic:
        device_states["alarm"] = payload
        print(f"Alarm: {payload}")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

print("Connecting to MQTT Broker...")
mqtt_client.connect(BROKER, PORT, keepalive=60)
mqtt_client.loop_start()
time.sleep(2)

def simulate_sensors():
    global ambient_temp
    
    light_on = device_states["light"] == "ON"
    fan_on = device_states["fan"] == "ON"
    alarm_on = device_states["alarm"] == "ON"
    
    if light_on:
        sensor_values["current_light"] = 800 + random.randint(-50, 50)
    else:
        sensor_values["current_light"] = max(0, sensor_values["current_light"] - 100)
    
    if fan_on:
        sensor_values["current_fan"] = 600 + random.randint(-50, 50)
        ambient_temp = max(18, ambient_temp - 0.5)
    else:
        sensor_values["current_fan"] = max(0, sensor_values["current_fan"] - 100)
        ambient_temp = min(28, ambient_temp + 0.2)
    
    if alarm_on:
        sensor_values["current_alarm"] = 400 + random.randint(-50, 50)
    else:
        sensor_values["current_alarm"] = max(0, sensor_values["current_alarm"] - 100)
    
    if light_on:
        sensor_values["temperature"] = min(45, sensor_values["temperature"] + 0.3)
        sensor_values["light_intensity"] = min(100, sensor_values["light_intensity"] + 2)
    else:
        sensor_values["temperature"] = max(ambient_temp, sensor_values["temperature"] - 0.2)
        sensor_values["light_intensity"] = max(20, sensor_values["light_intensity"] - 1)
    
    sensor_values["humidity"] = 50 + 10 * math.sin(time.time() / 30)
    sensor_values["humidity"] = max(30, min(70, sensor_values["humidity"]))
    
    if fan_on:
        sensor_values["humidity"] = max(30, sensor_values["humidity"] - 1)

def publish_sensors():
    data = {
        "temperature": round(sensor_values["temperature"], 2),
        "humidity": round(sensor_values["humidity"], 2),
        "light_intensity": round(sensor_values["light_intensity"], 2),
        "current_light": round(sensor_values["current_light"], 2),
        "current_fan": round(sensor_values["current_fan"], 2),
        "current_alarm": round(sensor_values["current_alarm"], 2),
        "light_state": device_states["light"],
        "fan_state": device_states["fan"],
        "alarm_state": device_states["alarm"],
        "timestamp": time.time()
    }
    
    mqtt_client.publish("sensors/temperature", json.dumps({"value": data["temperature"], "unit": "C"}))
    mqtt_client.publish("sensors/humidity", json.dumps({"value": data["humidity"], "unit": "%"}))
    mqtt_client.publish("sensors/light_intensity", json.dumps({"value": data["light_intensity"], "unit": "%"}))
    mqtt_client.publish("sensors/current_light", json.dumps({"value": data["current_light"], "unit": "mA"}))
    mqtt_client.publish("sensors/current_fan", json.dumps({"value": data["current_fan"], "unit": "mA"}))
    mqtt_client.publish("sensors/current_alarm", json.dumps({"value": data["current_alarm"], "unit": "mA"}))


    mqtt_client.publish("sensors/all", json.dumps(data))
    
    try:
        requests.post(f"{NODERED_URL}/sensor_data", json=data, timeout=1)
    except:
        pass



try:
    while True:
        simulate_sensors()
        publish_sensors()
        
        print("\nSensor Data:")
        print(f"  Temperature: {sensor_values['temperature']:.1f}°C")
        print(f"  Humidity: {sensor_values['humidity']:.1f}%")
        print(f"  Light Intensity: {sensor_values['light_intensity']:.1f}%")
        print(f"  Current Light: {sensor_values['current_light']:.0f}mA")
        print(f"  Current Fan: {sensor_values['current_fan']:.0f}mA")
        print(f"  Current Alarm: {sensor_values['current_alarm']:.0f}mA")
        print(f"  Device States: Light={device_states['light']}, Fan={device_states['fan']}, Alarm={device_states['alarm']}")
        
        time.sleep(1)

except KeyboardInterrupt:
    print("\nSensor simulator stopped")
    mqtt_client.loop_stop()
