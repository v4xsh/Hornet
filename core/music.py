import time
import os
import pyautogui
import pygetwindow as gw
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from pathlib import Path

# ✅ Get correct path to drivers folder regardless of script location
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

def play_song_on_spotify(song_name):
    driver = launch_brave_driver()
    driver.maximize_window()
    driver.get(f"https://open.spotify.com/search/{song_name.replace(' ', '%20')}")
    
    time.sleep(5)  # Wait for page to load

    try:
        brave_window = gw.getWindowsWithTitle("Spotify")[0]
        x_anchor = brave_window.left
        y_anchor = brave_window.top

        # 🎯 Estimated position of the first play button
        x_offset = 682
        y_offset = 485

        pyautogui.moveTo(x_anchor + x_offset, y_anchor + y_offset, duration=0.6)
        pyautogui.click()
        print("✅ Clicked estimated play button.")

        time.sleep(5)

    except Exception as e:
        print("❌ Error:", e)
