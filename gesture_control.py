import cv2
import mediapipe as mp
import requests
import time

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.3
)
mp_drawing = mp.solutions.drawing_utils

devices = {"light": "OFF", "fan": "OFF", "alarm": "OFF"}
last_gesture = None
cooldown = 0

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

print("\n🎮 GESTURE CONTROL → NODE-RED")
print("="*40)
print("✊ FIST → Light OFF")
print("🖐️  OPEN → Light ON")
print("👍 UP → Fan ON")
print("👎 DOWN → Fan OFF")
print("✌️  PEACE → Alarm ON")
print("🤘 ROCK → Alarm OFF")
print("="*40)
print("Press 'q' to quit\n")

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    frame = cv2.flip(frame, 1)
    h, w, c = frame.shape
    
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
                if gesture == "CLOSED_HAND":
                    devices["light"] = "OFF"
                    try:
                        requests.post("http://localhost:1880/light", json={"state": "OFF"}, timeout=1)
                    except:
                        pass
                    print(f"💡 Light: OFF")
                
                elif gesture == "OPEN_HAND":
                    devices["light"] = "ON"
                    try:
                        requests.post("http://localhost:1880/light", json={"state": "ON"}, timeout=1)
                    except:
                        pass
                    print(f"💡 Light: ON")
                
                elif gesture == "THUMBS_UP":
                    devices["fan"] = "ON"
                    try:
                        requests.post("http://localhost:1880/fan", json={"state": "ON"}, timeout=1)
                    except:
                        pass
                    print(f"🌀 Fan: ON")
                
                elif gesture == "THUMBS_DOWN":
                    devices["fan"] = "OFF"
                    try:
                        requests.post("http://localhost:1880/fan", json={"state": "OFF"}, timeout=1)
                    except:
                        pass
                    print(f"🌀 Fan: OFF")
                
                elif gesture == "PEACE":
                    devices["alarm"] = "ON"
                    try:
                        requests.post("http://localhost:1880/alarm", json={"state": "ON"}, timeout=1)
                    except:
                        pass
                    print(f"🔔 Alarm: ON")
                
                elif gesture == "ROCK":
                    devices["alarm"] = "OFF"
                    try:
                        requests.post("http://localhost:1880/alarm", json={"state": "OFF"}, timeout=1)
                    except:
                        pass
                    print(f"🔔 Alarm: OFF")
                
                last_gesture = gesture
                cooldown = time.time() + 1.5
        
        if gesture:
            cv2.putText(frame, f"Gesture: {gesture}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "Show hand...", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 2)
        
        y = 70
        for device, state in devices.items():
            color = (0, 255, 0) if state == "ON" else (0, 0, 255)
            cv2.putText(frame, f"{device.upper()}: {state}", (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            y += 35
        
        cv2.imshow("Gesture Control", frame)
        
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break
    
    except Exception as e:
        print(f"Error: {e}")
        continue

cap.release()
cv2.destroyAllWindows()
print("\n✅ Done")