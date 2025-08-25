# core/enroll_face.py

import os
import cv2
import face_recognition
import numpy as np
from datetime import datetime

def enroll_face_samples():
    """
    Capture a single face embedding from webcam and save it.
    """

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    folder = os.path.join(project_root, "face_data")
    os.makedirs(folder, exist_ok=True)
    save_path = os.path.join(folder, "vansh_face_embedding.npy")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Could not open webcam")
        return

    print("📷 Position your face in the frame and hold still...")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to capture frame.")
            break

        cv2.imshow("Enrollment - Press 's' to save", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("s"):  # Press S to save embedding
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            encodings = face_recognition.face_encodings(rgb_frame)

            if len(encodings) == 0:
                print("❌ No face detected. Try again.")
                continue

            np.save(save_path, encodings[0])
            print(f"✅ Face embedding saved at {save_path}")
            break

        elif key == ord("q"):  # Quit without saving
            print("❌ Enrollment canceled.")
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    enroll_face_samples()
