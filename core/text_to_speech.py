import pyttsx3
import threading
import queue

# --- Setup TTS Engine ---
engine = pyttsx3.init()
engine.setProperty('rate', 180)
engine.setProperty('volume', 1.0)

# --- Global Speech Queue ---
speech_queue = queue.Queue()

def tts_worker():
    """Worker thread: speaks queued text one by one."""
    while True:
        text = speech_queue.get()
        if text is None:
            break  # exit signal
        try:
            print("AI:", text)
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"⚠️ TTS error: {e}")
        finally:
            speech_queue.task_done()

# Start the worker thread (daemon = ends with program)
threading.Thread(target=tts_worker, daemon=True).start()

def speak(text):
    """Add text to the queue to be spoken sequentially."""
    speech_queue.put(text)

def shutdown_tts():
    """Clean shutdown (optional if you want to stop worker)."""
    speech_queue.put(None)
