import time
import os
import re
import subprocess
import pyautogui
import pyperclip
from gtts import gTTS
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ✅ Generate voice note using gTTS
def generate_ai_mp3(text, filename="ai_voice.mp3"):
    voice_notes_dir = Path("voice_notes")
    voice_notes_dir.mkdir(exist_ok=True)
    mp3_path = voice_notes_dir / filename
    tts = gTTS(text=text, lang='en')
    tts.save(mp3_path)
    time.sleep(1)
    return str(mp3_path.resolve())

# ✅ Copy file to clipboard (Windows)
def copy_file_to_clipboard_windows(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError("❌ File does not exist.")
    subprocess.run([
        "powershell", "-Command", f'Set-Clipboard -Path "{file_path}"'
    ])

# ✅ Slugify filename
def slugify(text):
    return "".join(c for c in text if c.isalnum() or c in (' ', '_')).rstrip().replace(" ", "_")[:50] + ".mp3"

# ✅ Send plain text message
def send_whatsapp_message(contact_name, message):
    chrome_driver_path = r"C:\Users\Vansh\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe"
    brave_path = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"

    if not os.path.exists(brave_path):
        raise FileNotFoundError("❌ Brave browser not found in default path.")

    options = webdriver.ChromeOptions()
    options.binary_location = brave_path
    user_profile = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "BraveSoftware", "Brave-Browser", "User Data")
    options.add_argument(f"user-data-dir={user_profile}")
    options.add_argument("profile-directory=Default")
    options.add_argument("--remote-debugging-port=9222")

    driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)
    driver.get("https://web.whatsapp.com")

    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true'][@data-tab='3']"))
    )

    search_box = driver.find_element(By.XPATH, "//div[@contenteditable='true'][@data-tab='3']")
    search_box.click()
    search_box.send_keys(contact_name)
    time.sleep(2)
    search_box.send_keys(Keys.ENTER)

    message_box_xpath = "//div[@contenteditable='true'][@data-tab='10']"
    WebDriverWait(driver, 10).until(
         EC.presence_of_element_located((By.XPATH, message_box_xpath))
    )
    message_box = driver.find_element(By.XPATH, message_box_xpath)
    message_box.click()
    message_box.send_keys(message)
    message_box.send_keys(Keys.ENTER)
    time.sleep(2)
    print(f"✅ Text message sent to {contact_name}")
    driver.quit()

# ✅ Send AI-generated voice note
def send_whatsapp_voice_note(contact_name, message_text):
    try:
        filename = slugify(message_text)
        temp_path = generate_ai_mp3(message_text, filename)
    except Exception as e:
        print("❌ Failed to generate voice note:", e)
        return

    chrome_driver_path = r"C:\Users\Vansh\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe"
    brave_path = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"

    if not os.path.exists(brave_path):
        raise FileNotFoundError("❌ Brave browser not found in default path.")

    options = webdriver.ChromeOptions()
    options.binary_location = brave_path
    user_profile = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "BraveSoftware", "Brave-Browser", "User Data")
    options.add_argument(f"user-data-dir={user_profile}")
    options.add_argument("profile-directory=Default")

    try:
        driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)
        driver.get("https://web.whatsapp.com")

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true'][@data-tab='3']"))
        )

        search_box = driver.find_element(By.XPATH, "//div[@contenteditable='true'][@data-tab='3']")
        search_box.click()
        search_box.clear()
        search_box.send_keys(contact_name)
        time.sleep(2)
        search_box.send_keys(Keys.ENTER)

        message_box_xpath = "//div[@contenteditable='true'][@data-tab='10']"
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, message_box_xpath))
        )
        message_box = driver.find_element(By.XPATH, message_box_xpath)
        message_box.click()
        time.sleep(2)

        copy_file_to_clipboard_windows(temp_path)
        time.sleep(2)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(2)
        pyautogui.press("enter")

        print(f"✅ Voice note sent to {contact_name}")
        time.sleep(5)
    except Exception as e:
        print("❌ Error sending voice note:", e)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# ✅ Extract contact/message from command
def extract_contact_and_message(command):
    command = command.lower().strip()
    match = re.match(r"(send a message to|message)\s+(.+?)\s+(.*)", command)
    if match:
        contact = match.group(2).strip().title()
        message = match.group(3).strip()
        return contact, message
    return None, None

# ✅ Extract voice note command
def extract_voice_note_command(command):
    command = command.lower().strip()
    match = re.match(r"(send a voice note to|voice note to)\s+(.+?)\s+(saying|that)\s+(.+)", command)
    if match:
        contact = match.group(2).strip().title()
        message = match.group(4).strip()
        return contact, message
    return None, None

