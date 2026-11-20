# MBRUS

MBRUS is a local, browser-based personal AI assistant built around a FastAPI
server. Its web dashboard combines text and voice conversations with Google
Gemini, live information, and Windows desktop controls.

## What it does

- Accepts typed commands and browser-based speech input, and replies with
  neural text-to-speech audio.
- Supports English, Hindi, Bengali, Bhojpuri, Haryanvi, and Marwadi.
- Uses Gemini for conversational AI. Configure an API key in the dashboard;
  MBRUS saves it in a `.env` file in the project directory.
- Provides live weather, cricket scores, news and web search, plus GPS-based
  location and weather when you grant browser location access.
- Opens websites and supported desktop applications in dedicated browser tabs,
  launches YouTube or Spotify playback, and searches within supported sites.
- Opens user-configured priority websites, adjusts system volume, and reports
  CPU, memory, disk, and battery status.
- Includes a wake-word standby engine, a custom call name, an in-dashboard
  Gemini model switcher, settings for the default city and speech voice, and a
  new-chat action that resets conversation history.

## Recent upgrades

- Added a modern Dragon HUD dashboard with live status indicators, quick-command
  chips, an arc-reactor assistant state, hands-free listening controls, and
  audio mute controls.
- Added configurable wake-word standby listening and custom wake/call phrases,
  including support for names such as "Hey MBRUS" or "Jarvis".
- Added new-tab browser automation for YouTube, Gmail, WhatsApp, GitHub,
  ChatGPT, Spotify, Google Maps, Amazon, Instagram, Facebook, and more.
- Added YouTube and Spotify playback commands, app-specific search commands,
  direct domain launching, and Google fallback search.
- Expanded priority-site management with dashboard controls to add, list, and
  remove custom websites.
- Added Gemini model selection and a **New Chat** control for clearing
  multi-turn chat history.
- Improved multilingual command handling and localized voice responses for
  English, Hindi, Bengali, Bhojpuri, Haryanvi, and Marwadi.
- Added browser tab handling so chat and priority-site actions open URLs in
  `_blank` tabs while preserving the MBRUS interface.

Live information and Gemini require an internet connection. Gemini-backed
conversation requires a Google Gemini API key. Microphone and location features
also depend on browser support and the permissions you grant.

## Requirements

- Windows (the included launcher and desktop controls target Windows)
- Python 3.10 or newer
- A modern browser; allow microphone and location access if you want to use
  speech input or GPS
- Internet access for Gemini, live information, web search, and Edge TTS

The browser UI is served by the Python application, so no separate Node.js
installation or frontend build is required.

### Python dependencies

Install the packages listed in [`requirements.txt`](./requirements.txt):

| Package | Use |
| --- | --- |
| `fastapi`, `uvicorn` | HTTP API and local web server |
| `pydantic` | API request validation |
| `google-genai` | Google Gemini chat |
| `httpx`, `beautifulsoup4`, `ddgs` | Fetching and parsing live information and web search results |
| `edge-tts`, `pyttsx3` | Online neural speech generation and offline TTS helper |
| `psutil`, `pyautogui` | System diagnostics and Windows desktop/volume controls |
| `pyjokes` | Joke responses |
| `python-dotenv` | Loading and saving local configuration |

## Initialize and run

1. Install Python 3.10 or newer and make sure `python` is available in your
   terminal.
2. From the project directory, create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use Command Prompt instead:

   ```bat
   .venv\Scripts\activate.bat
   ```

3. Install the dependencies:

   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

4. Start MBRUS using either:

   ```powershell
   python server.py
   ```

   or, on Windows, double-click `start_mbrus.bat`.

5. Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.
   Click **Connect Gemini** in the dashboard and provide your Gemini API key
   to enable Gemini chat.

Stop the server with `Ctrl+C` in the terminal (or close the launcher window).
The default server address is `127.0.0.1:8000`.

## Configuration

The application loads optional settings from a `.env` file in the project
root. For example:

```dotenv
HOST=127.0.0.1
PORT=8000
DEFAULT_CITY=New Delhi
GEMINI_MODEL=gemini-3.5-flash-lite
ASSISTANT_NAME=MBRUS
WAKE_WORD=Hey MBRUS
TTS_VOICE=en-US-ChristopherNeural
TTS_RATE=+18%
TTS_PITCH=+0Hz
```

Set the Gemini key through **Connect Gemini** in the dashboard, or add
`GEMINI_API_KEY=your-key` to the local `.env` file. Treat `.env` as a secret:
do not commit or share it. Keep the server bound to localhost unless you have
deliberately configured and secured access from other devices.

The default city, neural TTS voice, wake/call name, and auto-wake setting can
also be changed from the dashboard settings. Wake-word and auto-wake preferences
are runtime settings and should be managed through the dashboard.
