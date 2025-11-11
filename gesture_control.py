import cv2
import mediapipe as mp
import paho.mqtt.client as mqtt
import requests
from datetime import datetime
import time
import json

BROKER = "localhost"
PORT = 1883
NODERED_URL = "http://localhost:1880"

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "gesture_control")

device_states = {"light": "OFF", "fan": "OFF", "alarm": "OFF"}
sensor_data = {
    "temperature": 22.0,
    "humidity": 50.0,
    "light_intensity": 30.0,
    "current_light": 0.0,
    "current_fan": 0.0,
    "current_alarm": 0.0
}

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.3
)
mp_drawing = mp.solutions.drawing_utils

last_gesture = None
cooldown = 0

gesture_map = {
    "THUMBS_UP": ("light", "ON"),
    "THUMBS_DOWN": ("light", "OFF"),
    "OPEN_HAND": ("fan", "ON"),
    "CLOSED_HAND": ("fan", "OFF"),
    "PEACE": ("alarm", "ON"),
    "ROCK": ("alarm", "OFF"),
}

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        client.subscribe("sensors/#")
    else:
        print(f"Connection failed: {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        if "temperature" in msg.topic:
            sensor_data["temperature"] = payload.get("value", 22.0)
        elif "humidity" in msg.topic:
            sensor_data["humidity"] = payload.get("value", 50.0)
        elif "light_intensity" in msg.topic:
            sensor_data["light_intensity"] = payload.get("value", 30.0)
        elif "current_light" in msg.topic:
            sensor_data["current_light"] = payload.get("value", 0.0)
        elif "current_fan" in msg.topic:
            sensor_data["current_fan"] = payload.get("value", 0.0)
        elif "current_alarm" in msg.topic:
            sensor_data["current_alarm"] = payload.get("value", 0.0)
    except:
        pass

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

print("Connecting to MQTT Broker...")
mqtt_client.connect(BROKER, PORT, keepalive=60)
mqtt_client.loop_start()
time.sleep(2)

def classify_gesture(lm):
    try:
        t_tip, i_tip, m_tip, r_tip, p_tip = lm[4], lm[8], lm[12], lm[16], lm[20]
        t_base, i_base, m_base, r_base, p_base = lm[2], lm[5], lm[9], lm[13], lm[17]
        wrist = lm[0]
        
        fingers = 0
        if t_tip.x < t_base.x: fingers += 1
        if i_tip.y < i_base.y: fingers += 1
        if m_tip.y < m_base.y: fingers += 1
        if r_tip.y < r_base.y: fingers += 1
        if p_tip.y < p_base.y: fingers += 1
        
        dist = ((t_tip.x - i_tip.x)**2 + (t_tip.y - i_tip.y)**2)**0.5
        
        if fingers == 0: return "CLOSED_HAND"
        elif fingers == 5: return "OPEN_HAND"
        elif fingers == 2 and dist > 0.05: return "PEACE"
        elif fingers == 1 and t_tip.y < wrist.y and t_tip.x > i_tip.x: return "THUMBS_UP"
        elif fingers == 1 and t_tip.y > wrist.y: return "THUMBS_DOWN"
        elif fingers == 2 and dist < 0.05: return "ROCK"
    except:
        pass
    return None


cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

frame_skip = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    frame = cv2.flip(frame, 1)
    h, w, c = frame.shape
    
    frame_skip += 1
    if frame_skip % 2 != 0:
        continue
    
    try:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)
        
        gesture = None
        
        if results.multi_hand_landmarks and len(results.multi_hand_landmarks) > 0:
            landmarks = results.multi_hand_landmarks[0]
            lm = landmarks.landmark
            gesture = classify_gesture(lm)
            
            try:
                mp_drawing.draw_landmarks(frame, landmarks, mp_hands.HAND_CONNECTIONS)
            except:
                pass
            
            if gesture and gesture != last_gesture and time.time() > cooldown:
                device, state = gesture_map[gesture]
                device_states[device] = state
                
                mqtt_client.publish(f"home/{device}", state)
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] {device.upper()}: {state}")
                print(gesture)
                gesture_data = {
                    "gesture": gesture,
                    "device": device,
                    "state": state,
                    "timestamp": datetime.now().isoformat()
                }
                
                try:
                    requests.post(f"{NODERED_URL}/gesture", json=gesture_data, timeout=1)
                except:
                    pass
                
                last_gesture = gesture
                cooldown = time.time() + 2.0
        
        if gesture:
            cv2.putText(frame, f"Gesture: {gesture}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        
        
        
        y = 160
        for device in ["light", "fan", "alarm"]:
            state = device_states[device]
            
           
            
            color = (0, 255, 0) if state == "ON" else (0, 0, 255)
            
            
            status_text = f"{device.upper()}: {state}"
            cv2.putText(frame, status_text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            y += 45
        
        
        cv2.imshow("Gesture Control", frame)
        
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break
    
    except Exception as e:
        continue

cap.release()
cv2.destroyAllWindows()
mqtt_client.loop_stop()
