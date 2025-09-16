# core/hand_object_detector.py

import cv2
from PIL import Image
import numpy as np
from core.text_to_speech import speak
from transformers import BlipProcessor, BlipForConditionalGeneration
import torch

# Securely load BLIP model (uses safe weights, avoids torch.load CVE)
try:
    processor = BlipProcessor.from_pretrained(
        "Salesforce/blip-image-captioning-base",
        trust_remote_code=True
    )
    model = BlipForConditionalGeneration.from_pretrained(
        "Salesforce/blip-image-captioning-base",
        trust_remote_code=True,
        use_safetensors=True  # <-- Secure loading (no .bin vulnerability)
    )
except Exception as e:
    speak("Failed to load the BLIP model.")
    raise RuntimeError("BLIP model loading failed: " + str(e))

def capture_frame():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        speak("Camera not detected.")
        return None

    speak("Please hold the object in front of the camera.")
    for _ in range(30):  # Warm-up frames
        cap.read()
    ret, frame = cap.read()
    cap.release()

    if not ret:
        speak("Failed to capture image.")
        return None

    return frame

def predict_object(frame):
    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    inputs = processor(images=image, return_tensors="pt")

    with torch.no_grad():
        output_ids = model.generate(**inputs)
    
    caption = processor.tokenizer.decode(output_ids[0], skip_special_tokens=True)
    return caption

def identify_object_in_hand():
    frame = capture_frame()
    if frame is None:
        return

    description = predict_object(frame)
    speak(f"It looks like you're holding or showing: {description}.")

