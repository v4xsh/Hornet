from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from core.text_to_speech import speak  # Ensure speak() is accessible

def play_top_youtube_video(query, driver):
    """
    Plays the top YouTube video for the given query using the provided Selenium driver.
    """
    try:
        driver.get("https://www.youtube.com")  # Reload YouTube homepage
        time.sleep(2)
        search_box = driver.find_element(By.NAME, "search_query")
        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        time.sleep(3)

        videos = driver.find_elements(By.ID, "video-title") 
        if videos:
            videos[0].click()
        else:
            speak("No videos found.")
    except Exception as e:
        speak("An error occurred while trying to play the video.")
        print(f"[YouTube Play Error] {e}")

def search_and_type_on_site(site, query):
    """
    Opens a site (YouTube, Wikipedia, etc.) and performs a search using Selenium.
    For YouTube, returns the driver so it can be reused.
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    if site == "youtube":
        driver.get("https://www.youtube.com")
        time.sleep(3)
        search_box = driver.find_element(By.NAME, "search_query")
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        return driver  # ✅ Return driver for reuse

    elif site == "wikipedia":
        driver.get("https://www.wikipedia.org")
        time.sleep(2)
        search_box = driver.find_element(By.NAME, "search")
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)

    elif site == "twitter":
        driver.get("https://twitter.com/explore")
        time.sleep(3)
        search_box = driver.find_element(By.XPATH, '//input[@aria-label="Search query"]')
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)

    elif site == "chatgpt":
        driver.get("https://chat.openai.com")

    elif site == "instagram":
        driver.get("https://www.instagram.com")

    else:
        driver.get(f"https://www.{site}.com")

    return None  # Only YouTube returns a driver

