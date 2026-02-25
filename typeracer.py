from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pyautogui
import keyboard
import threading
import cv2
import numpy as np
import os
import time
from google import genai
from PIL import Image

client = genai.Client(api_key="is_a_secret")

# ── browser ──────────────────────────────────────────────────────────────────

def attach_to_browser():
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Chrome(options=options)
    
    # find and switch to the typeracer tab
    for handle in driver.window_handles:
        driver.switch_to.window(handle)
        if "typeracer" in driver.current_url:
            print(f"Connected to: {driver.current_url}")
            return driver
    
    # if no typeracer tab found, just print what it sees
    print(f"Warning: no Typeracer tab found, connected to: {driver.current_url}")
    print("Available tabs:", [driver.switch_to.window(h) or driver.current_url for h in driver.window_handles])
    return driver

# ── scrape paragraph ──────────────────────────────────────────────────────────

def scrape_paragraph(driver):
    WebDriverWait(driver, 120).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "span[unselectable='on']"))
    )
    page_html = driver.page_source
    soup = BeautifulSoup(page_html, "html.parser")
    spans = soup.find_all("span", attrs={"unselectable": "on"})
    print(f"Found {len(spans)} spans")
    return "".join(span.get_text() for span in spans).strip()

# ── image preprocessing ───────────────────────────────────────────────────────

def ocr_preprocess(img):
    black_lo = np.array([0, 0, 0])
    black_hi = np.array([255, 255, 70])
    pixels = np.float32(img.reshape(-1, 3))

    n_colors = 2
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, .1)
    flags = cv2.KMEANS_RANDOM_CENTERS

    _, labels, palette = cv2.kmeans(pixels, n_colors, None, criteria, 10, flags)
    _, counts = np.unique(labels, return_counts=True)
    dominant = palette[np.argmax(counts)]

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, black_lo, black_hi)
    SE = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask = cv2.dilate(mask, SE, iterations=1)
    img[mask > 0] = dominant
    return img

# ── captcha solver ────────────────────────────────────────────────────────────

def solve_captcha_text_only(driver):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    save_path = os.path.join(script_dir, "captcha.jpeg")

    captcha_element = driver.find_element(By.CLASS_NAME, "challengeImg")
    png_bytes = captcha_element.screenshot_as_png
    captcha_image = cv2.imdecode(np.frombuffer(png_bytes, np.uint8), cv2.IMREAD_COLOR)
    captcha_image = ocr_preprocess(captcha_image)
    cv2.imwrite(save_path, captcha_image)

    pil_image = Image.open(save_path)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            "What does the text in this captcha say? Respond with only the text and nothing else, no quotes, no explanation.",
            pil_image
        ]
    )

    captcha_text = response.text.strip()
    print(f"Captcha text: {captcha_text}")
    return captcha_text

# ── typing ────────────────────────────────────────────────────────────────────

def type_text(text):
    pyautogui.typewrite(text, interval=0.03)

# ── trigger ───────────────────────────────────────────────────────────────────

def wait_for_trigger():
    trigger = threading.Event()
    keyboard.add_hotkey("ctrl+alt+t", lambda: trigger.set(), suppress=True)
    trigger.wait()
    time.sleep(0.3)

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    print("Attaching to existing Chrome window...")
    driver = attach_to_browser()

    print("Waiting for paragraph to load, get into a race...")
    paragraph = scrape_paragraph(driver)
    print(f"\nScraped text: {paragraph}")

    print("\nClick into the Typeracer input box, then press Ctrl+Alt+T to start typing...")
    wait_for_trigger()
    type_text(paragraph)

    print("\nIf captcha appears, press Ctrl+Alt+T again to solve it...")
    wait_for_trigger()
    captcha_text = solve_captcha_text_only(driver)
    if captcha_text:
        type_text(captcha_text)

if __name__ == "__main__":
    main()