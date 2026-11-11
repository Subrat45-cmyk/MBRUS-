"""
MBRUS Text-to-Speech (TTS) Engine
Provides Edge-TTS neural speech generation with in-memory caching and pyttsx3 offline fallback.
Optimized for high-speed voice playback and conversational cadence (+18% speech rate).
"""

import io
import asyncio
import edge_tts
import pyttsx3
from app.config import TTS_VOICE, TTS_RATE, TTS_PITCH

_pyttsx3_engine = None
_audio_cache = {}  # In-memory cache for ultra-fast repeated voice queries (hash -> bytes)
MAX_CACHE_ITEMS = 64

def get_offline_engine():
    global _pyttsx3_engine
    if _pyttsx3_engine is None:
        try:
            _pyttsx3_engine = pyttsx3.init()
            _pyttsx3_engine.setProperty("rate", 195)
            voices = _pyttsx3_engine.getProperty("voices")
            if voices:
                _pyttsx3_engine.setProperty("voice", voices[0].id)
        except Exception as e:
            print(f"[TTS] pyttsx3 init error: {e}")
            _pyttsx3_engine = False
    return _pyttsx3_engine if _pyttsx3_engine else None


async def generate_speech_audio(text: str, voice: str = TTS_VOICE) -> bytes:
    if not text:
        return b""
    clean_speech = text.replace("*", "").replace("#", "").replace("`", "").strip()
    if not clean_speech:
        return b""

    # Truncate voice speech to a max of 2 sentences or 220 chars to prevent long speech latency
    if len(clean_speech) > 220:
        parts = clean_speech.split(". ")
        if len(parts) > 1:
            clean_speech = ". ".join(parts[:2]) + "."
        else:
            clean_speech = clean_speech[:220]

    cache_key = f"{voice}_{clean_speech}"
    if cache_key in _audio_cache:
        return _audio_cache[cache_key]

    try:
        communicate = edge_tts.Communicate(clean_speech, voice, rate=TTS_RATE, pitch=TTS_PITCH)
        audio_stream = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_stream.write(chunk["data"])
        
        audio_bytes = audio_stream.getvalue()
        if audio_bytes:
            if len(_audio_cache) >= MAX_CACHE_ITEMS:
                _audio_cache.pop(next(iter(_audio_cache)))
            _audio_cache[cache_key] = audio_bytes
        return audio_bytes
    except Exception as e:
        print(f"[TTS] Edge-TTS error: {e}")
        return b""


def speak_offline(text: str):
    engine = get_offline_engine()
    if engine:
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"[TTS] speak_offline error: {e}")
    else:
        print(f"[TTS Fallback Console]: {text}")
