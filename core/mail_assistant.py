# core/mail_assistant.py

import time
import pyautogui
import pygetwindow as gw
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from core.text_to_speech import speak
from core.gemini_utils import generate_mail_content
from core.voice_capture import record_and_transcribe # ✅ CORRECTED: Use the function that exists
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
CHROMEDRIVER_PATH = str(BASE_DIR / "drivers" / "chromedriver.exe")
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
            # ✅ CORRECTED: Reverted to the single function call
            response = record_and_transcribe(prompt="Here is the mail. Do you want me to send it?", duration=5)
            
            if any(kw in response for kw in ["yes", "send", "send it", "confirm"]):
                send_btn = compose_box.find_element(By.CSS_SELECTOR, "div[role='button'][data-tooltip*='Send']")
                send_btn.click()
                speak("Mail sent successfully.")
                return
            elif any(kw in response for kw in ["no", "don't", "do not", "cancel"]):
                speak("Okay, cancelling the mail.")
                return
        
        speak("I didn't get a clear confirmation. Canceling the mail for safety.")

    except Exception as e:
        speak("Something went wrong while sending the mail.")
        print("❌ Error in Gmail automation:", e)
    finally:
        time.sleep(5)
        driver.quit()

def handle_send_mail(command=None):
    # ✅ CORRECTED: Reverted to the single function call
    username_raw = record_and_transcribe(prompt="Let's begin. Please spell the email username letter by letter.", duration=10)
    if not username_raw:
        speak("Sorry, I couldn't hear the username.")
        return
    username = username_raw.replace(" dash ", "-").replace(" underscore ", "_").replace(" ", "")

    # ✅ CORRECTED: Reverted to the single function call
    domain_input = record_and_transcribe(prompt="Which domain is it? Gmail, Yahoo, or Outlook?", duration=6)
    if not domain_input:
        speak("Sorry, I couldn't hear the domain.")
        return

    domain_map = {"gmail": "gmail.com", "yahoo": "yahoo.com", "outlook": "outlook.com"}
    domain = domain_map.get(domain_input.strip())
    if not domain:
        speak("Sorry, I couldn't recognize the domain.")
        return

    to_email = username + "@" + domain
    
    # ✅ CORRECTED: Reverted to the single function call
    recipient_name = record_and_transcribe(prompt="What is the recipient's name?", duration=5)
    if not recipient_name: recipient_name = "there"

    # ✅ CORRECTED: Reverted to the single function call
    sender_name = record_and_transcribe(prompt="And what is your name for the signature?", duration=5)
    if not sender_name: sender_name = "Vansh"
        
    # ✅ CORRECTED: Reverted to the single function call
    description = record_and_transcribe(prompt=f"Got it. Now, what is the email about?", duration=20)
    if not description:
        speak("I didn't get a description for the email body.")
        return

    speak("Generating a professional email.")
    result = generate_mail_content(description, recipient_name, sender_name)
    
    if not isinstance(result, dict) or 'subject' not in result:
        speak("Something went wrong while generating the email.")
        return

    subject = result["subject"]
    body = result["body"]
    
    speak("Opening Gmail and preparing the mail now.")
    send_mail_gmail(to_email, subject, body)