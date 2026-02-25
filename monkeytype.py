from selenium import webdriver
from selenium.webdriver.chrome.options import Options
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
        if "monkeytype" in driver.current_url.lower():
            print(f"Connected to: {driver.current_url}")
            return driver

    raise Exception("Monkeytype tab not found")

# ── scrape ─────────────────────────────────────────────────

def get_words(driver):
    soup = BeautifulSoup(driver.page_source, "html.parser")
    words = soup.select("#words .word")
    result = []

    for word in words:
        letters = word.find_all("letter")
        if not letters:
            continue

        # skip fully typed words
        is_typed = all(
            'correct' in l.get('class', []) or 'incorrect' in l.get('class', [])
            for l in letters
        )
        if is_typed:
            continue

        # skip partially typed words (active word)
        is_partial = any(
            'correct' in l.get('class', []) or 'incorrect' in l.get('class', [])
            for l in letters
        )
        if is_partial:
            continue

        word_text = "".join(l.get_text() for l in letters)
        if word_text:
            result.append(word_text)

    return result

# ── kill switch ────────────────────────────────────────────

def listen_for_keys():
    global running

    def on_press(key):
        global running
        if key == pynput_keyboard.Key.esc:
            running = False
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
    driver.execute_script("document.getElementById('wordsInput').focus();")
    time.sleep(0.3)


# ── typing ─────────────────────────────────────────────────

def type_text(driver, words, duration):
    global running
    i = 0
    start_time = time.time()

    while i < len(words):
        if not running:
            break

        # stop if time is up
        if time.time() - start_time >= duration:
            running = False
            break

        pyautogui.write(words[i], interval=0)

        if not running:
            break

        pyautogui.press('space')
        i += 1

        if i % 20 == 0 and running:
            new_words = get_words(driver)
            if new_words:
                words = new_words
                i = 0

# ── main ───────────────────────────────────────────────────

def main():
    global running

    driver = attach_to_browser()
    words = get_words(driver)

    if not words:
        print("No words found. Make sure Monkeytype is open and ready.")
        return

    duration = 120

    wait_for_trigger(driver)

    if running:
        type_text(driver, words, duration)

    print("\nDone.")

if __name__ == "__main__":
    main()