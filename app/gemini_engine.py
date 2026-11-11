"""
MBRUS Gemini Chatbot Engine
Provides Google Gemini API integration with multi-turn conversation memory,
multilingual reasoning, code execution formatting, and voice synthesis extraction.
Optimized for high-speed, meaningful, conversational Gemini answers.
"""

import os
import re
from pathlib import Path
from dotenv import set_key, load_dotenv
from app.config import ASSISTANT_NAME

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH, override=True)

_gemini_client = None
_active_model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
_conversation_history = []

AVAILABLE_MODELS = [
    {"id": "gemini-3.5-flash-lite", "name": "Gemini 3.5 Flash Lite (Fastest & Conversational)", "badge": "⚡ Ultra Fast"},
    {"id": "gemini-3.5-flash", "name": "Gemini 3.5 Flash (Balanced Deep Reasoning)", "badge": "🧠 Flash"},
    {"id": "gemini-3.7-flash", "name": "Gemini 3.7 Flash (Next-Gen Flash)", "badge": "🚀 Fast"},
    {"id": "gemini-3.8-flash", "name": "Gemini 3.8 Flash (Comprehensive Reasoning)", "badge": "⚡ 3.8"}
]

FALLBACK_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.7-flash",
    "gemini-3.8-flash"
]


def init_gemini_client():
    """Initializes the official Google GenAI client if GEMINI_API_KEY is available."""
    global _gemini_client
    load_dotenv(ENV_PATH, override=True)
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if api_key:
        try:
            from google import genai
            _gemini_client = genai.Client(api_key=api_key)
            print("[GeminiEngine] Google Gemini Client successfully initialized.")
            return True
        except Exception as e:
            print(f"[GeminiEngine] Error initializing Gemini client: {e}")
            _gemini_client = None
            return False
    _gemini_client = None
    return False


init_gemini_client()


def get_gemini_status() -> dict:
    """Returns current status of Gemini API connection and model."""
    load_dotenv(ENV_PATH, override=True)
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    has_key = bool(api_key and len(api_key) > 10)
    
    masked_key = ""
    if has_key:
        masked_key = f"{api_key[:6]}...{api_key[-4:]}"

    return {
        "configured": bool(_gemini_client and has_key),
        "has_key": has_key,
        "masked_key": masked_key,
        "active_model": _active_model,
        "available_models": AVAILABLE_MODELS
    }


def save_gemini_key(new_key: str, model: str = "") -> dict:
    """Saves Gemini API key and active model to .env and updates runtime client."""
    global _active_model
    clean_key = new_key.strip()
    
    if not ENV_PATH.exists():
        ENV_PATH.write_text(f"GEMINI_API_KEY={clean_key}\nGEMINI_MODEL={model or _active_model}\n", encoding="utf-8")
    else:
        set_key(str(ENV_PATH), "GEMINI_API_KEY", clean_key)
        if model:
            set_key(str(ENV_PATH), "GEMINI_MODEL", model)

    os.environ["GEMINI_API_KEY"] = clean_key
    if model:
        _active_model = model
        os.environ["GEMINI_MODEL"] = model

    success = init_gemini_client()
    return {
        "success": success,
        "message": "Gemini API connected successfully!" if success else "Key saved. Could not verify client.",
        "status": get_gemini_status()
    }


def set_active_model(model_id: str):
    """Switches the active Gemini model."""
    global _active_model
    _active_model = model_id
    if ENV_PATH.exists():
        set_key(str(ENV_PATH), "GEMINI_MODEL", model_id)
    os.environ["GEMINI_MODEL"] = model_id


def clear_chat_session():
    """Resets multi-turn conversation history (New Chat)."""
    global _conversation_history
    _conversation_history = []
    return {"success": True, "message": "Conversation history cleared."}


def parse_gemini_response(raw_output: str) -> tuple[str, str]:
    """
    Extracts conversational spoken text and rich markdown display text.
    Supports tagged format <voice>...</voice><display>...</display> with regex fallbacks.
    """
    if not raw_output:
        return "", ""

    voice_match = re.search(r"<voice>([\s\S]*?)</voice>", raw_output, re.IGNORECASE)
    display_match = re.search(r"<display>([\s\S]*?)</display>", raw_output, re.IGNORECASE)

    if voice_match and display_match:
        spoken = voice_match.group(1).strip()
        markdown = display_match.group(1).strip()
        return spoken, markdown

    clean_display = raw_output.replace("<voice>", "").replace("</voice>", "").replace("<display>", "").replace("</display>", "").strip()
    
    text_no_code = re.sub(r"```[\s\S]*?```", "", clean_display)
    text_no_code = re.sub(r"`.*?`", "", text_no_code)
    text_no_code = re.sub(r"#+\s*", "", text_no_code)
    text_clean = text_no_code.replace("*", "").replace("_", "").replace("~", "")
    text_clean = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text_clean)
    lines = [line.strip() for line in text_clean.split("\n") if line.strip() and not line.strip().startswith(("|", "-", "*", ">"))]
    clean_passage = " ".join(lines)

    sentences = re.split(r"(?<=[.!?।])\s+", clean_passage)
    spoken = " ".join(sentences[:2]).strip()
    if not spoken:
        spoken = clean_passage[:150].strip()

    return spoken, clean_display


def generate_gemini_response(
    user_prompt: str,
    language: str = "auto",
    context_data: str = ""
) -> dict:
    """Main generator using Google Gemini API with multi-turn conversational intelligence."""
    global _gemini_client, _conversation_history, _active_model

    if _gemini_client is None:
        init_gemini_client()

    if _gemini_client is None:
        return {
            "success": False,
            "error": "Gemini API key is not configured.",
            "requires_key": True
        }

    lang_instructions = {
        "bho": "Speak and reply in authentic colloquial Bhojpuri (भोजपुरी) using Devanagari script. Tone: warm, respectful, conversational (use 'भैया' / 'रउआ').",
        "bgc": "Speak and reply in energetic Haryanvi dialect (हरियाणवी) using Devanagari script. Tone: energetic, conversational, respectful (use 'भाई' / 'ताऊ').",
        "mwr": "Speak and reply in authentic Marwadi / Rajasthani (मारवाड़ी) using Devanagari script. Tone: courteous, warm (use 'हुकम सा' / 'सा').",
        "bn": "Speak and reply in natural, conversational Bengali (বাংলা) using Bengali script.",
        "hi": "Speak and reply in natural, fluent, conversational Hindi (हिंदी) using Devanagari script.",
        "en": "Speak and reply in articulate, warm, and brilliant conversational English like Gemini paired with Jarvis."
    }
    lang_guidance = lang_instructions.get(language, "Match the user's language naturally and conversationally.")

    system_instruction = (
        f"You are {ASSISTANT_NAME}, a brilliant, friendly, and ultra-intelligent AI assistant powered by Google Gemini. "
        "Motto: TALK • THINK • ACT.\n\n"
        f"Conversational & Language Directive: {lang_guidance}\n\n"
        "Crucial Formatting Rule:\n"
        "You MUST structure your entire response using these two tags:\n"
        "<voice>\n"
        "1 or 2 natural, punchy, conversational spoken sentences directly answering the user. No markdown symbols, no asterisks, no code syntax, no bullet points — this is read aloud by the neural TTS engine.\n"
        "</voice>\n"
        "<display>\n"
        "The complete, meaningful, beautifully formatted response in Markdown. Use bold headers, bullet lists, tables, and formatted code blocks with language identifiers where appropriate. Be thorough, insightful, and engaging.\n"
        "</display>"
    )

    augmented_prompt = user_prompt
    if context_data:
        augmented_prompt = f"{user_prompt}\n\n[Context Grounding:\n{context_data}]"

    from google.genai import types

    contents_payload = []
    # Keep last 6 turns for fast context window
    for turn in _conversation_history[-6:]:
        contents_payload.append(types.Content(
            role=turn["role"],
            parts=[types.Part.from_text(text=turn["text"])]
        ))
    
    contents_payload.append(types.Content(
        role="user",
        parts=[types.Part.from_text(text=augmented_prompt)]
    ))

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.7,
        top_p=0.95,
        max_output_tokens=1500
    )

    # Try active model first, with instant fallback through candidate list if needed
    candidate_models = [_active_model] + [m for m in FALLBACK_MODELS if m != _active_model]
    last_error = None

    for model_name in candidate_models:
        try:
            response = _gemini_client.models.generate_content(
                model=model_name,
                contents=contents_payload,
                config=config
            )

            raw_text = response.text or ""
            spoken, markdown = parse_gemini_response(raw_text)

            _conversation_history.append({"role": "user", "text": user_prompt})
            _conversation_history.append({"role": "model", "text": markdown or raw_text})

            if model_name != _active_model:
                _active_model = model_name

            return {
                "success": True,
                "model_used": model_name,
                "full_markdown": markdown or raw_text,
                "voice_summary": spoken
            }
        except Exception as e:
            last_error = str(e)
            print(f"[GeminiEngine] Model {model_name} attempt failed: {e}. Trying fallback...")
            continue

    return {
        "success": False,
        "error": last_error or "All Gemini models were unavailable."
    }
