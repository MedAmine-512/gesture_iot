import cv2
import mediapipe as mp
import requests
from datetime import datetime
import time

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.3
)
mp_drawing = mp.solutions.drawing_utils

device_states = {"light": "OFF", "fan": "OFF", "alarm": "OFF"}
last_gesture = None
cooldown = 0
gesture_delay = 0

gesture_map = {
    "THUMBS_UP": ("light", "ON"),
    "THUMBS_DOWN": ("light", "OFF"),
    "OPEN_HAND": ("fan", "ON"),
    "CLOSED_HAND": ("fan", "OFF"),
    "PEACE": ("alarm", "ON"),
    "ROCK": ("alarm", "OFF"),
}

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

print("="*50)
print("FIST → Light OFF")
print("OPEN → Light ON")
print("UP → Fan ON")
print("DOWN → Fan OFF")
print("PEACE → Alarm ON")
print("ROCK → Alarm OFF")
print("Press 'q' to quit\n")

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
                
                try:
                    requests.post(f"http://localhost:1880/{device}", json={"state": state}, timeout=1)
                except:
                    pass
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}]  {device.upper()}: {state}")
                
                last_gesture = gesture
                cooldown = time.time() + 2.0
        
        if gesture:
            cv2.putText(frame, f"Gesture: {gesture}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        y = 70
        for device, state in device_states.items():
            color = (0, 255, 0) if state == "ON" else (0, 0, 255)
            cv2.circle(frame, (w-30, y-20), 15, color, -1)
            cv2.putText(frame, f"{device.upper()}: {state}", (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
            y += 40
        
        cv2.imshow("Gesture Control → Node-RED", frame)
        
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break
    
    except Exception as e:
        continue

cap.release()
cv2.destroyAllWindows()
