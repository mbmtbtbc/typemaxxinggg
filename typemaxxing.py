from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pytesseract
import cv2
import numpy as np
import pyautogui
import keyboard
import threading
import time

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def attach_to_browser():
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Chrome(options=options)
    return driver

def scrape_paragraph(driver):
    WebDriverWait(driver, 120).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "span[unselectable='on']"))
    )

    page_html = driver.page_source
    soup = BeautifulSoup(page_html, "html.parser")

    spans = soup.find_all("span", attrs={"unselectable": "on"})
    print(f"Found {len(spans)} spans")

    full_text = ""
    for span in spans:
        full_text += span.get_text()

    return full_text.strip()

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

def solve_captcha(driver):
    captcha_image = driver.find_element(By.CLASS_NAME, "challengeImg").screenshot_as_png
    captcha_image = cv2.imdecode(np.frombuffer(captcha_image, np.uint8), cv2.IMREAD_COLOR)

    # save raw captcha for debugging
    cv2.imwrite("captcha.png", captcha_image)

    captcha_image = ocr_preprocess(captcha_image)

    # save preprocessed image for debugging
    cv2.imwrite("preprocessed_captcha.png", captcha_image)

    captcha_text = pytesseract.image_to_string(captcha_image)
    print("Captcha text: ", captcha_text)

    if not captcha_text:
        print("No captcha text found")
        return None

    return type_text(captcha_text)

def type_text(text):
    pyautogui.typewrite(text, interval=0.10)

def wait_for_trigger():
    trigger = threading.Event()
    keyboard.add_hotkey("ctrl+alt+t", lambda: trigger.set(), suppress=True)
    trigger.wait()
    time.sleep(0.3)

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
    solve_captcha(driver)

if __name__ == "__main__":
    main()