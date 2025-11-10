"""
Quick camera test to verify it works before running main system
"""
import cv2

def test_camera():
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        return False
    
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        cv2.putText(frame, "Camera Test", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Camera Test", frame)
        
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("Camera test complete!")
    return True

if __name__ == "__main__":
    test_camera()