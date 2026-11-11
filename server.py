"""
MBRUS Personal AI Assistant - FastAPI Web Server
Runs locally at http://127.0.0.1:8000
Provides APIs for Gemini reasoning, live Cricbuzz scores, GPS geolocation,
priority websites launcher, multilingual TTS, and hardware telemetry.
"""

import os
import asyncio
import uvicorn
from pathlib import Path
from fastapi import FastAPI, Request, Query, Response, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.config import (
    SERVER_HOST,
    SERVER_PORT,
    ASSISTANT_NAME,
    DEFAULT_CITY,
    TTS_VOICE,
    INDIAN_LANGUAGES
)
from app.brain import MBRUSBrain, localize_location_response, detect_language
from app.tts_engine import generate_speech_audio
from app.live_info import (
    get_live_cricket_matches,
    get_live_weather,
    get_state_or_city_details,
    reverse_geocode_gps,
    get_weather_by_coords,
    INDIAN_STATES
)
from app.system_control import (
    get_system_diagnostics,
    load_priority_sites,
    add_priority_site,
    remove_priority_site,
    open_application
)
from app.gemini_engine import (
    get_gemini_status,
    save_gemini_key,
    set_active_model,
    clear_chat_session
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title=f"{ASSISTANT_NAME} AI Core", version="2.5")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static assets
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Shared Brain instance
brain = MBRUSBrain()


# ---------------------------------------------------------
# Request Models
# ---------------------------------------------------------
class ChatRequest(BaseModel):
    message: str
    voice: Optional[str] = ""
    language: Optional[str] = "auto"


class GPSLocationRequest(BaseModel):
    latitude: float
    longitude: float
    language: Optional[str] = "auto"


class PrioritySiteRequest(BaseModel):
    key: str
    name: str
    url: str
    icon: Optional[str] = "🌐"
    category: Optional[str] = "Custom"


class PriorityLaunchRequest(BaseModel):
    key: str


class GeminiKeyRequest(BaseModel):
    api_key: str
    model: Optional[str] = ""


class GeminiModelRequest(BaseModel):
    model: str


class SettingsRequest(BaseModel):
    default_city: Optional[str] = None
    tts_voice: Optional[str] = None


# ---------------------------------------------------------
# Routes
# ---------------------------------------------------------
@app.get("/")
async def serve_index():
    """Serves the main MBRUS Dragon HUD web application."""
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(str(index_path))


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """Processes user queries through the MBRUS Brain."""
    if not req.message or not req.message.strip():
        return JSONResponse(content={"voice_text": "Sir, I didn't receive any command.", "display_text": "No input received."})

    lang = req.language if req.language and req.language != "auto" else detect_language(req.message)
    response_data = await asyncio.to_thread(brain.classify_and_process, req.message, req.language or "auto")

    # Pick recommended voice based on resolved language
    detected_lang = response_data.get("language", lang)
    if detected_lang == "bn":
        recommended_voice = "bn-IN-BashkarNeural"
    elif detected_lang in ["hi", "bho", "bgc", "mwr"]:
        recommended_voice = "hi-IN-MadhurNeural"
    else:
        recommended_voice = req.voice or TTS_VOICE

    response_data["recommended_voice"] = recommended_voice
    return JSONResponse(content=response_data)


@app.get("/api/tts")
async def tts_endpoint(text: str = Query(...), voice: Optional[str] = None, lang: Optional[str] = None):
    """Streams neural Edge-TTS voice audio."""
    chosen_voice = voice
    if not chosen_voice:
        if lang == "bn":
            chosen_voice = "bn-IN-BashkarNeural"
        elif lang in ["hi", "bho", "bgc", "mwr"]:
            chosen_voice = "hi-IN-MadhurNeural"
        else:
            chosen_voice = TTS_VOICE

    audio_bytes = await generate_speech_audio(text, voice=chosen_voice)
    if not audio_bytes:
        return Response(content=b"", media_type="audio/mpeg", status_code=204)
    return Response(content=audio_bytes, media_type="audio/mpeg")


@app.post("/api/location/gps")
async def gps_location_endpoint(req: GPSLocationRequest):
    """Registers GPS coordinates from the browser and retrieves pinpoint weather."""
    loc_meta = reverse_geocode_gps(req.latitude, req.longitude)
    weather_data = get_weather_by_coords(req.latitude, req.longitude)
    loc_meta["weather"] = weather_data

    # Save into brain memory
    brain.set_user_gps(req.latitude, req.longitude, loc_meta)

    lang = req.language or "auto"
    if lang == "auto":
        lang = "en"

    voice_summary = localize_location_response(lang, weather_data)

    recommended_voice = "hi-IN-MadhurNeural" if lang in ["hi", "bho", "bgc", "mwr"] else ("bn-IN-BashkarNeural" if lang == "bn" else TTS_VOICE)

    return {
        "success": True,
        "location": loc_meta,
        "weather": weather_data,
        "voice_text": voice_summary,
        "recommended_voice": recommended_voice
    }


@app.get("/api/location/search")
async def location_search_endpoint(q: str = Query(...)):
    """Explores any Indian state or global city's telemetry & weather."""
    details = get_state_or_city_details(q)
    return {"success": True, "data": details}


@app.get("/api/priority-sites")
async def get_priority_sites_endpoint():
    """Lists all configured priority websites."""
    sites = load_priority_sites()
    return {"success": True, "sites": sites}


@app.post("/api/priority-sites")
async def add_priority_site_endpoint(req: PrioritySiteRequest):
    """Adds a new priority site to the launcher."""
    sites = add_priority_site(req.key, req.name, req.url, req.icon or "🌐", req.category or "Custom")
    return {"success": True, "sites": sites}


@app.delete("/api/priority-sites/{key}")
async def delete_priority_site_endpoint(key: str):
    """Deletes a priority site from the launcher."""
    sites = remove_priority_site(key)
    return {"success": True, "sites": sites}


@app.post("/api/priority-sites/launch")
async def launch_priority_site_endpoint(req: PriorityLaunchRequest):
    """Opens the priority site in the user's default browser."""
    sites = load_priority_sites()
    key_clean = req.key.lower().strip()
    site_info = sites.get(key_clean)

    res = open_application(key_clean)
    return {
        "success": True,
        "site": site_info,
        "voice_text": res.get("voice_text", f"Opening {key_clean} in your browser, Sir.")
    }


@app.get("/api/live/sports")
async def live_sports_endpoint():
    """Returns Cricbuzz live matches and ball-by-ball running status."""
    matches = get_live_cricket_matches()
    return {"success": True, "matches": matches, "count": len(matches)}


@app.get("/api/live/weather")
async def live_weather_endpoint(city: Optional[str] = None):
    """Returns live weather for the default or specified city."""
    target_city = city or DEFAULT_CITY
    w = get_live_weather(target_city)
    return {"success": True, "weather": w}


@app.get("/api/live/system")
async def live_system_endpoint():
    """Returns real-time hardware diagnostics (CPU, RAM, Battery, Disk)."""
    stats = get_system_diagnostics()
    return {"success": True, "stats": stats}


# ---------------------------------------------------------
# Gemini Chatbot Integration Endpoints
# ---------------------------------------------------------
@app.get("/api/gemini/status")
async def gemini_status_endpoint():
    """Returns current Gemini API connection status and active model."""
    status = get_gemini_status()
    return JSONResponse(content=status)


@app.post("/api/gemini/key")
async def gemini_key_endpoint(req: GeminiKeyRequest):
    """Saves and verifies a Gemini API key."""
    result = save_gemini_key(req.api_key, model=req.model or "")
    return JSONResponse(content=result)


@app.post("/api/gemini/model")
async def gemini_model_endpoint(req: GeminiModelRequest):
    """Switches the active Gemini model."""
    set_active_model(req.model)
    return JSONResponse(content={"success": True, "model": req.model})


@app.post("/api/gemini/clear-chat")
async def gemini_clear_chat_endpoint():
    """Resets multi-turn conversational history."""
    clear_chat_session()
    brain.conversation_history.clear()
    return JSONResponse(content={"success": True, "message": "Conversation session reset successfully."})


# ---------------------------------------------------------
# Settings Endpoints
# ---------------------------------------------------------
@app.get("/api/settings")
async def get_settings_endpoint():
    return {
        "default_city": DEFAULT_CITY,
        "tts_voice": TTS_VOICE,
        "supported_languages": INDIAN_LANGUAGES
    }


@app.post("/api/settings")
async def save_settings_endpoint(req: SettingsRequest):
    global DEFAULT_CITY, TTS_VOICE
    if req.default_city:
        DEFAULT_CITY = req.default_city
    if req.tts_voice:
        TTS_VOICE = req.tts_voice
    return {"success": True, "default_city": DEFAULT_CITY, "tts_voice": TTS_VOICE}


if __name__ == "__main__":
    print(f"\n=======================================================")
    print(f"  ⚡ {ASSISTANT_NAME} DRAGON AI ASSISTANT ONLINE")
    print(f"  📍 Localhost Server: http://{SERVER_HOST}:{SERVER_PORT}")
    print(f"  💬 Motto: TALK • THINK • ACT")
    print(f"=======================================================\n")
    uvicorn.run("server:app", host=SERVER_HOST, port=SERVER_PORT, reload=False)
