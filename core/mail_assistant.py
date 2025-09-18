# core/mail_assistant.py
import time
import threading
import pyautogui
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from core.text_to_speech import speak
from core.voice_capture import record_and_transcribe
from core.local_llm import get_local_llm_response
from core.speech_recognition_proxy import proxy_aware_sr
from pathlib import Path
import re
import os
import json

BASE_DIR = Path(__file__).resolve().parent.parent
CHROMEDRIVER_PATH = r"C:\Users\Vansh\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe"
BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
USER_DATA_DIR = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "BraveSoftware", "Brave-Browser", "User Data")


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
            response = record_and_transcribe(prompt="Here is the mail. Do you want me to send it?", duration=7)

            if isinstance(response, str) and any(kw in response for kw in ["yes", "send", "send it", "confirm"]):
                send_btn = compose_box.find_element(By.CSS_SELECTOR, "div[role='button'][data-tooltip*='Send']")
                send_btn.click()
                speak("Mail sent successfully.")
                return
            elif isinstance(response, str) and any(kw in response for kw in ["no", "don't", "do not", "cancel"]):
                speak("Okay, cancelling the mail.")
                return

        speak("I didn't get a clear confirmation. Canceling the mail for safety.")

    except Exception as e:
        speak("Something went wrong while sending the mail.")
        print("❌ Error in Gmail automation:", e)
    finally:
        time.sleep(5)
        driver.quit()


def clean_username(raw: str) -> str:
    """Clean raw spelled username using STT booster + rules."""
    if not raw:
        return ""

    text = raw.lower().strip()
    try:
        text = proxy_aware_sr.correct_names(text)
    except Exception:
        pass

    # spoken tokens
    text = text.replace(" dash ", "-").replace(" underscore ", "_").replace(" dot ", ".")
    text = text.replace(" period ", ".").replace(" full stop ", ".").replace(" space ", "").replace(" at ", "")
    # remove spelling separators
    text = text.replace("-", "").replace(" ", "")

    # digits
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

    # sanitize
    text = re.sub(r"\.{2,}", ".", text)
    text = text.strip("._-")
    text = re.sub(r"[^a-z0-9._-]", "", text)

    return text


def replace_placeholders(body: str, recipient_name: str, sender_name: str) -> str:
    """Replace [Name] and [Your Name] in body."""
    if not body:
        return body
    b = body
    b = re.sub(r"\[(name|recipient)\]", recipient_name, b, flags=re.I)
    b = re.sub(r"\[(your ?name|sender)\]", sender_name, b, flags=re.I)
    return b


def handle_send_mail(command=None):
    # Step 1: ask for email first
    username_raw = record_and_transcribe(prompt="Please spell the email username", duration=12)
    if not username_raw:
        speak("Sorry, I couldn't hear the username.")
        return
    username = clean_username(username_raw)
    if not username:
        speak("Could not parse the username.")
        return
    to_email = username + "@gmail.com"
    print("✅ Final Email:", to_email)

    # Step 2: extract recipient name using LLM
    try:
        response = get_local_llm_response(
            f"Extract a clean, nicely formatted first name from this email: {to_email}. "
            f"Return ONLY the name, no symbols or numbers."
        )
        recipient_name = response.strip().split()[0].capitalize()
    except Exception:
        recipient_name = "there"

    # Step 3: ask for description
    description = record_and_transcribe(prompt="What is the email about?", duration=20)
    if not description:
        speak("I didn't get a description for the email body.")
        return

    speak("Got it. I’ll start drafting the email in the background.")
    mail_result = {}
    mail_done = threading.Event()

    def draft_mail():
        try:
            response = get_local_llm_response(
                f"Write a professional email for [Name] based on this description: {description}. "
                f"Use placeholders [Name] for recipient and [Your Name] for sender if needed. "
                f"Return JSON with 'subject' and 'body'."
            )
            try:
                parsed = json.loads(response)
                mail_result.update(parsed)
            except Exception:
                # fallback parsing if not proper JSON
                parts = response.strip().split("\n", 1)
                mail_result["subject"] = parts[0].replace("Subject:", "").strip()
                mail_result["body"] = parts[1].strip() if len(parts) > 1 else ""
        except Exception as e:
            print("❌ LLM Drafting error:", e)
        finally:
            mail_done.set()

    threading.Thread(target=draft_mail, daemon=True).start()

    if not mail_done.wait(timeout=60):
        speak("Email drafting took too long. Cancelling.")
        return

    subject = mail_result.get("subject", "No Subject")
    body = mail_result.get("body", "No Body")

    # Clean up subject from boilerplate like "Creating a professional mail"
    subject = re.sub(r"(?i)creating a professional mail|professional email for .*", "", subject).strip()
    if not subject:
        subject = "No Subject"

    # Replace placeholders and fix leftover LLM mistakes
    sender_name = "Hornet"  # Replace with your actual name
    if recipient_name.lower() in ["after", "there", "recipient"]:
        recipient_name = "Teacher"  # fallback if LLM messed up

    body = replace_placeholders(body, recipient_name, sender_name)
    body = re.sub(r"\bAfter\b", recipient_name, body)
    body = re.sub(r"\bYour Name\b", sender_name, body)

    # Ensure signature at the end
    if not re.search(r"(best regards|thanks|sincerely)", body.lower()):
        body += f"\n\nBest regards,\n{sender_name}"

    # Proper paragraph spacing
    body = "\n\n".join([line.strip() for line in body.split("\n") if line.strip()])

    speak("Opening Gmail and preparing the mail now.")
    send_mail_gmail(to_email, subject, body)
