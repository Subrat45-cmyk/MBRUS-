import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "MBRUS")
WAKE_WORDS = ["mbrus", "hey mbrus", "ok mbrus", "jarvis", "alexa", "एमब्रस", "हे एमब्रस"]

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 8000))
SERVER_HOST = HOST
SERVER_PORT = PORT

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AQ.Ab8RN6J1Zo65pW8xZMFJNm5WF0mLwGj-er1jz4o5dxvML7UBGg")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
DEFAULT_CITY = os.getenv("DEFAULT_CITY", "New Delhi")
TTS_VOICE = os.getenv("TTS_VOICE", "en-US-ChristopherNeural")
TTS_RATE = os.getenv("TTS_RATE", "+18%")
TTS_PITCH = os.getenv("TTS_PITCH", "+0Hz")

INDIAN_LANGUAGES = {
    "en": "English",
    "hi": "Hindi (हिंदी)",
    "bn": "Bengali (বাংলা)",
    "bho": "Bhojpuri (भोजपुरी)",
    "bgc": "Haryanvi (हरियाणवी)",
    "mwr": "Marwadi (मारवाड़ी)"
}

SYSTEM_PROMPT = f"""You are {ASSISTANT_NAME}, an ultra-intelligent, highly capable personal AI assistant and Gemini-powered chatbot inspired by Jarvis and Alexa.
Motto: TALK • THINK • ACT.
Key Behaviors:
1. When spoken to, provide clear, concise, direct answers suitable for voice playback (2-3 punchy sentences).
2. For real-time queries (match scores, sports running status, weather, GPS location, news), state the exact live situation immediately.
3. Keep the tone sophisticated, futuristic, and helpful — like Jarvis.
4. Support multilingual communication fluently: English, Hindi (हिंदी), Bengali (বাংলা), Bhojpuri (भोजपुरी), Haryanvi (हरियाणवी), and Marwadi (मारवाड़ी).
"""
