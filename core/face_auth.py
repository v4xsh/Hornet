import cv2
import numpy as np
import os
from deepface import DeepFace
import mediapipe as mp
import pyttsx3

def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def cosine_similarity(a, b):
    a = np.array(a).flatten()
    b = np.array(b).flatten()
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def verify_face(threshold=0.5):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    embedding_path = os.path.join(project_root, "face_data", "vansh_face_embedding.npy")

    if not os.path.exists(embedding_path):
        msg = "Reference embedding not found."
        print("❌", msg)
        speak(msg)
        return False

    ref_embedding = np.load(embedding_path)
    print("✅ Loaded reference embedding. First 5 values:", ref_embedding[:5])

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        msg = "Could not open webcam."
        print("❌", msg)
        speak(msg)
        return False

    print("📸 Look into the camera...")
    speak("Look into the camera please.")
    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        msg = "Could not capture frame."
        print("❌", msg)
        speak(msg)
        return False

    mp_face_detection = mp.solutions.face_detection
    with mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5) as face_detection:
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_detection.process(img_rgb)

        if not results.detections:
            msg = "No face detected in the captured frame."
            print("❌", msg)
            speak(msg)
            return False

        detection = results.detections[0]
        bboxC = detection.location_data.relative_bounding_box
        ih, iw, _ = frame.shape
        x1 = int(bboxC.xmin * iw)
        y1 = int(bboxC.ymin * ih)
        w = int(bboxC.width * iw)
        h = int(bboxC.height * ih)

        if w <= 0 or h <= 0:
            msg = "Invalid bounding box detected."
            print("❌", msg)
            speak(msg)
            return False

        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(iw, x1 + w)
        y2 = min(ih, y1 + h)

        print(f"Face bounding box (pixels): x={x1}, y={y1}, w={w}, h={h}")

        face_img = frame[y1:y2, x1:x2]

    if face_img.size == 0:
        msg = "Cropped face image is empty."
        print("❌", msg)
        speak(msg)
        return False

    face_img = cv2.resize(face_img, (112, 112))
    print(f"Face crop shape: {face_img.shape}")

    try:
        captured_embedding = DeepFace.represent(face_img, model_name='ArcFace', enforce_detection=False)[0]["embedding"]
    except Exception as e:
        msg = f"Error generating embedding: {e}"
        print("❌", msg)
        speak("Error generating face embedding.")
        return False

    print(f"Captured embedding shape: {np.array(captured_embedding).shape}")
    print(f"Captured embedding first 5 values: {captured_embedding[:5]}")

    similarity = cosine_similarity(ref_embedding, captured_embedding)
    print(f"🔍 Cosine similarity: {similarity:.3f}")

    if similarity > (1 - threshold):
        msg = "Face verified. Welcome back Chief!"
        
        print("✅", msg)
        speak(msg)
        return True
    else:
        msg = "Sorry, You are not Vansh only he can access me."
        print("🚫", msg)
        speak(msg)
        return False

if __name__ == "__main__":
    result = verify_face()
    print("Verification result:", result)
