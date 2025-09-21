# core/mail_assistant.py
import time
import threading
import pyautogui
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from core.text_to_speech import speak
from core.local_llm import get_local_llm_response
from core.speech_recognition_proxy import proxy_aware_sr
from pathlib import Path
import re
import os
import json
from scipy.io import wavfile

BASE_DIR = Path(__file__).resolve().parent.parent
CHROMEDRIVER_PATH = r"C:\Users\Vansh\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe"
BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
USER_DATA_DIR = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "BraveSoftware", "Brave-Browser", "User Data")

# ===================== SILENCE BASED RECORDING =====================
def record_with_silence(prompt="Speak now", min_start=2.0, silence_limit=1.5, threshold=500, fs=16000):
    """Record audio with silence detection, return transcribed text"""
    import sounddevice as sd

    speak(prompt)
    print(f"🎤 {prompt} (listening with silence detection)")

    recording = []
    start_time = time.time()
    silence_time = None

    with sd.InputStream(samplerate=fs, channels=1, dtype="int16") as stream:
        while True:
            chunk, _ = stream.read(1024)
            pcm = np.frombuffer(chunk, dtype=np.int16)
            recording.append(pcm)

            intensity = np.mean(np.abs(pcm))
            elapsed = time.time() - start_time

            if elapsed > min_start:
                if intensity < threshold:
                    if silence_time is None:
                        silence_time = time.time()
                    elif time.time() - silence_time > silence_limit:
                        break
                else:
                    silence_time = None

    audio = np.hstack(recording).astype(np.int16)
    temp_wav = os.path.join(BASE_DIR, "temp_mail.wav")
    wavfile.write(temp_wav, fs, audio)

    try:
        text = proxy_aware_sr.recognize_audio(temp_wav)
    except Exception as e:
        print("❌ Speech recognition failed:", e)
        text = ""
    finally:
        if os.path.exists(temp_wav):
            os.remove(temp_wav)

    print("✅ Transcribed:", text)
    return text.strip()

# ===================== BROWSER + GMAIL =====================
def launch_brave_driver():
    options = webdriver.ChromeOptions()
    options.binary_location = BRAVE_PATH
    options.add_argument(f"user-data-dir={USER_DATA_DIR}")
    options.add_argument("profile-directory=Default")
    return webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)

def send_mail_gmail(to_email, subject, body):
    driver = launch_brave_driver()
    driver.maximize_window()
    driver.get("https://mail.google.com/mail/u/0/#inbox?compose=new")

    try:
        wait = WebDriverWait(driver, 20)
        compose_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='dialog']")))

        pyautogui.write(to_email, interval=0.05)
        pyautogui.press("enter")
        time.sleep(1)
        pyautogui.press("tab")
        time.sleep(0.5)
        pyautogui.write(subject, interval=0.05)
        time.sleep(0.5)
        pyautogui.press("tab")

        body_div = compose_box.find_element(By.CSS_SELECTOR, "div[aria-label='Message Body']")
        body_div.click()
        time.sleep(0.5)
        body_div.send_keys(body)

        for attempt in range(2):
            response = record_with_silence("Here is the mail. Do you want me to send it?")
            if any(kw in response.lower() for kw in ["yes", "send", "confirm"]):
                send_btn = compose_box.find_element(By.CSS_SELECTOR, "div[role='button'][data-tooltip*='Send']")
                send_btn.click()
                speak("Mail sent successfully.")
                return
            elif any(kw in response.lower() for kw in ["no", "don't", "cancel"]):
                speak("Okay, cancelling the mail.")
                return

        speak("I didn't get a clear confirmation. Cancelling for safety.")

    except Exception as e:
        speak("Something went wrong while sending the mail.")
        print("❌ Gmail automation error:", e)
    finally:
        time.sleep(5)
        driver.quit()

# ===================== HELPERS =====================
def clean_username(raw: str) -> str:
    if not raw:
        return ""
    text = raw.lower().strip()
    try:
        text = proxy_aware_sr.correct_names(text)
    except Exception:
        pass

    text = text.replace(" dash ", "-").replace(" underscore ", "_").replace(" dot ", ".")
    text = text.replace(" period ", ".").replace(" full stop ", ".").replace(" space ", "").replace(" at ", "")
    text = text.replace("-", "").replace(" ", "")

    digit_map = {
        r"\bzero\b": "0", r"\bo\b": "0",
        r"\bone\b": "1", r"\bwon\b": "1",
        r"\btwo\b": "2", r"\bto\b": "2", r"\btoo\b": "2",
        r"\bthree\b": "3",
        r"\bfour\b": "4", r"\bfor\b": "4",
        r"\bfive\b": "5",
        r"\bsix\b": "6",
        r"\bseven\b": "7",
        r"\beight\b": "8",
        r"\bnine\b": "9",
    }
    for pat, digit in digit_map.items():
        text = re.sub(pat, digit, text)

    text = re.sub(r"\.{2,}", ".", text)
    text = text.strip("._-")
    text = re.sub(r"[^a-z0-9._-]", "", text)
    return text

def replace_placeholders(body: str, recipient_name: str, sender_name: str) -> str:
    if not body:
        return body
    b = body
    b = re.sub(r"\[(name|recipient)\]", recipient_name, b, flags=re.I)
    b = re.sub(r"\[(your ?name|sender)\]", sender_name, b, flags=re.I)
    return b

def sanitize_subject(subject: str) -> str:
    subject = subject.strip()
    subject = re.sub(
        r"(?i)(here is (a )?(professional )?mail:?|creating (a )?professional mail:?|professional email for .*)",
        "",
        subject
    ).strip()
    return subject if subject else "No Subject"

# ===================== MAIN FLOW =====================
def handle_send_mail(command=None):
    # Step 1: Ask for email first
    username_raw = record_with_silence("Please spell the email username")
    if not username_raw:
        speak("Sorry, I couldn't hear the username.")
        return
    username = clean_username(username_raw)
    if not username:
        speak("Could not parse the username.")
        return
    to_email = username + "@gmail.com"
    print("✅ Final Email:", to_email)

    # Step 2: Ask for description
    description = record_with_silence("What is the email about?")
    if not description:
        speak("I didn't get a description for the email body.")
        return

    # Step 3: Recipient name via LLM
    try:
        response = get_local_llm_response(
            f"Extract a clean first name from this email: {to_email}. Return ONLY the name."
        )
        recipient_name = response.strip().split()[-1].capitalize()
    except Exception:
        recipient_name = "Teacher"

    # Override with description keywords if needed
    desc_lower = description.lower()
    if "sir" in desc_lower:
        recipient_name = "Sir"
    elif "madam" in desc_lower or "ma'am" in desc_lower:
        recipient_name = "Madam"
    elif "teacher" in desc_lower:
        recipient_name = "Teacher"

    # Step 4: Draft the email body via LLM
    speak("Got it. Drafting email in the background...")
    mail_result, mail_done = {}, threading.Event()

    def draft_mail():
        try:
            response = get_local_llm_response(
                f"Write a professional email for [Name] based on this description: {description}. "
                f"Use placeholders [Name] for recipient and [Your Name] for sender. "
                f"Do not include JSON, markdown, or any explanations in the returned mail, Return only the final formatted email with: subject and body dont write anything like here is the mail or something give the mail directly "
            )
            try:
                parsed = json.loads(response)
                mail_result.update(parsed)
            except Exception:
                parts = response.strip().split("\n", 1)
                mail_result["subject"] = parts[0].replace("Subject:", "").strip()
                mail_result["body"] = parts[1].strip() if len(parts) > 1 else ""
        except Exception as e:
            print("❌ LLM Draft error:", e)
        finally:
            mail_done.set()

    threading.Thread(target=draft_mail, daemon=True).start()

    if not mail_done.wait(timeout=60):
        speak("Email drafting took too long. Cancelling.")
        return

    subject = sanitize_subject(mail_result.get("subject", "No Subject"))
    sender_name = "Vansh"
    body = replace_placeholders(mail_result.get("body", "No Body"), recipient_name, sender_name)

    # Extra fixes
    body = re.sub(r"\bAfter\b", recipient_name, body)
    body = re.sub(r"\bYour Name\b", sender_name, body)

    if not re.search(r"(best regards|thanks|sincerely)", body.lower()):
        body += f"\n\nBest regards,\n{sender_name}"

    body = "\n\n".join([line.strip() for line in body.split("\n") if line.strip()])

    # Step 5: Send
    speak("Opening Gmail and preparing the mail now.")
    send_mail_gmail(to_email, subject, body)
