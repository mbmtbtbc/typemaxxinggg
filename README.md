# typemaxxing

just a fun little project using a python bot that scrapes and auto-types text on typing test websites. 
built to learn web scraping, browser automation, and how typing test sites work under the hood.

---

## tech stack

| tool | purpose |
|------|---------|
| `selenium` | browser automation & DOM interaction |
| `beautifulsoup4` | HTML parsing & text scraping |
| `pyautogui` | simulating keystrokes |
| `pynput` | kill switch (ESC to stop) |
| `python 3.13` | the whole thing runs on this |

---

## how it works

```
1. attaches to your already-open chrome window via chrome devtools protocol (CDP)
2. finds the correct tab (typeracer / monkeytype / human benchmark)
3. scrapes all the words/text from the DOM before typing starts
4. waits for you to press ENTER in the terminal to trigger typing
5. uses alt+tab to switch focus back to chrome automatically
6. pyautogui types the scraped text at max speed
7. press ESC anytime to stop
```

each site required a different scraping approach since they all structure their DOM differently:

- **typeracer** — uses `<span unselectable="on">` tags
- **monkeytype** — uses `<div class="word">` with `<letter>` tags, dynamically loads new words as you type
- **human benchmark** — uses `<span class="incomplete">` tags inside a `div.letters` container

---

## results

### monkeytype — 295 wpm (120s, 100% accuracy)
<img width="1919" height="1019" alt="Screenshot 2026-02-26 211532" src="https://github.com/user-attachments/assets/72377a9f-0d82-47fc-95ea-4649eec4aae3" />

---

### human benchmark — 7143 wpm
<img width="1919" height="1018" alt="Screenshot 2026-02-26 211828" src="https://github.com/user-attachments/assets/829da5d6-d3ec-4c0b-b7f0-1e61a0f41971" />

---

### typeracer — 327 wpm (triggered captcha challenge)
<img width="1919" height="1012" alt="Screenshot 2026-02-26 212003" src="https://github.com/user-attachments/assets/e8e69cd0-1a44-41a5-9de6-62fb523b9c0f" />

> typeracer flagged the bot at 327 wpm and issued a captcha typing challenge requiring 245+ wpm to pass. the captcha solver uses an AI vision API to read and type the distorted text.

---


## 📝 notes

- monkeytype bot re-scrapes every 20 words to handle dynamic word loading
- typeracer bot includes a captcha solver using an AI vision API
- human benchmark bot uses direct selenium key injection for maximum speed
- all bots attach to an existing chrome session (no new windows opened)
- i have good programming skills
