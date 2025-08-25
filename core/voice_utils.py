# voice_utils.py
import pyttsx3
import speech_recognition as sr
import threading

engine = pyttsx3.init()
engine.setProperty('rate', 180)
engine.setProperty('volume', 1.0)

audio_lock = threading.Lock()
listener = sr.Recognizer()

def speak(text):
    with audio_lock:
        print("AI:", text)
        engine.say(text)
        engine.runAndWait()

def listen_command():
    with sr.Microphone() as source:
        print("Listening...")
        listener.adjust_for_ambient_noise(source)
        audio = listener.listen(source, phrase_time_limit=5)
    try:
        command = listener.recognize_google(audio).lower()
        print("You:", command)
        return command
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        return "network error"
