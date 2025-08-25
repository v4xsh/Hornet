import cv2

def test_all_cameras(max_tested=5):
    print("🔍 Scanning for available webcams...")
    for i in range(max_tested):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            print(f"[✅] Camera found at index {i}. Showing preview...")
            ret, frame = cap.read()
            if ret:
                cv2.imshow(f"Camera Index {i}", frame)
                cv2.waitKey(2000)  # Show for 2 seconds
                cv2.destroyAllWindows()
            cap.release()
        else:
            print(f"[❌] Camera index {i} not available.")

test_all_cameras()
