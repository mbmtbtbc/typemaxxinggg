from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pyautogui
from pynput import keyboard as pynput_keyboard
import threading
import time

# ── globals ────────────────────────────────────────────────
running = True

# ── browser ────────────────────────────────────────────────

def attach_to_browser():
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Chrome(options=options)

    for handle in driver.window_handles:
        driver.switch_to.window(handle)
        if "humanbenchmark" in driver.current_url.lower():
            print(f"Connected to: {driver.current_url}")
            return driver

    raise Exception("Human Benchmark tab not found")

# ── scrape ─────────────────────────────────────────────────

def get_words(driver):
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # get all incomplete spans
    letters = soup.select("div.letters span.incomplete")

    full_text = "".join(l.get_text() for l in letters)
    words = full_text.split(" ")

    # filter empty strings
    words = [w for w in words if w]

    print(f"Scraped {len(words)} words")
    return words

# ── kill switch ────────────────────────────────────────────

def listen_for_keys():
    global running

    def on_press(key):
        global running
        if key == pynput_keyboard.Key.esc:
            running = False
            print("\nKill switch activated! Stopping...")
            return False

    with pynput_keyboard.Listener(on_press=on_press) as listener:
        listener.join()

# ── trigger ────────────────────────────────────────────────

def wait_for_trigger(driver):
    kill_thread = threading.Thread(target=listen_for_keys)
    kill_thread.daemon = True
    kill_thread.start()

    input("\nPress ENTER to start typing (ESC anytime to stop)...")

    pyautogui.hotkey('alt', 'tab')
    time.sleep(0.5)

    # focus the typing area
    try:
        driver.execute_script(
            "document.querySelector('div.letters').click();"
        )
    except:
        pass

    time.sleep(0.3)
    print("Typing!")

# ── typing ─────────────────────────────────────────────────

def type_text(driver, words):
    full_text = " ".join(words)
    input_area = driver.find_element(By.CSS_SELECTOR, "div.letters")
    input_area.send_keys(full_text)

# ── main ───────────────────────────────────────────────────

def main():
    global running

    print("Connecting to Chrome...")
    driver = attach_to_browser()

    print("Scraping text...")
    words = get_words(driver)

    if not words:
        print("No text found. Make sure Human Benchmark typing test is open and ready.")
        return

    print(f"Preview: {' '.join(words[:10])}...")

    wait_for_trigger(driver)

    if running:
        type_text(driver, words)

    print("\nDone.")

if __name__ == "__main__":
    main()