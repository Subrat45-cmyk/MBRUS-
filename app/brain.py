"""
MBRUS Core Intelligence Brain - Multilingual & Location Engine
Supports English, Hindi, Bengali, Marwadi, Haryanvi, and Bhojpuri.
Orchestrates intent classification, GPS location, state/city details, priority sites, live sports, and neural voice synthesis.
"""

import os
import re
import datetime
import pyjokes
from app.config import ASSISTANT_NAME, SYSTEM_PROMPT, DEFAULT_CITY
from app.live_info import (
    get_live_sports_score,
    get_live_weather,
    get_state_or_city_details,
    reverse_geocode_gps,
    get_latest_news,
    search_web_realtime,
    INDIAN_STATES
)
from app.system_control import (
    get_system_diagnostics,
    open_application,
    play_youtube,
    play_spotify,
    search_specific_app,
    search_google,
    adjust_volume,
    load_priority_sites,
    KNOWN_WEB_APPS
)
from app.gemini_engine import (
    generate_gemini_response,
    get_gemini_status,
    save_gemini_key,
    set_active_model,
    clear_chat_session
)


def detect_language(text: str, user_pref: str = "auto") -> str:
    if user_pref and user_pref != "auto":
        return user_pref

    t = text.lower()
    if re.search(r"[\u0980-\u09FF]", text):
        return "bn"
    if any(w in t for w in ["kemon", "aajker", "bhalo", "ki khobor", "score koto", "shono", "koro"]):
        return "bn"

    bhojpuri_markers = [
        "का बा", "का हाल बा", "रउआ", "हईं", "बानी", "बतावा", "भैया", "कैसन बा", "का समाचार",
        "ka ba", "kaisan ba", "raua", "bhaiya", "batava", "batawa", "hum", "ka haal ba"
    ]
    if any(m in t for m in bhojpuri_markers):
        return "bho"

    haryanvi_markers = [
        "राम राम", "के हाल सै", "घणा", "म्हारा", "थारा", "सै", "बता भाई", "के से भाई", "किसे सै",
        "ram ram", "ke haal se", "ke se bhai", "ghana", "bata bhai", "mhara", "thara"
    ]
    if any(m in t for m in haryanvi_markers):
        return "bgc"

    marwadi_markers = [
        "खम्मा घणी", "हुकम", "कांई", "सा", "म्हारो", "थांरो", "छै", "कैंया हो", "कांई समाचार",
        "khamma ghani", "hukam", "kai chhe", "kya chhe", "sa", "mharo", "tharo", "kai haal"
    ]
    if any(m in t for m in marwadi_markers):
        return "mwr"

    if re.search(r"[\u0900-\u097F]", text):
        return "hi"
    hindi_markers = [
        "kya", "kaise", "batao", "aaj", "ka", "ki", "kaisa", "samachar", "bhai",
        "khelo", "kholo", "chal raha", "chal rahi", "score kya hai", "mausam"
    ]
    if any(w in t.split() for w in hindi_markers):
        return "hi"

    return "en"


def get_localized_intro(lang: str) -> str:
    greetings = {
        "bho": "प्रणाम भैया! हम MBRUS हईं, जयपुर के केहू के बनावल एगो मशीन। आदेश करीं, का हुकुम बा?",
        "bgc": "राम राम भाई! मैं MBRUS सूं, जयपुर के किसे भाई नै बणाया एक मशीन। बता भाई, के सेवा करूँ?",
        "mwr": "खम्मा घणी सा! म्हूं MBRUS हूँ, जयपुर रा कोई हुकम रो बणायो एक मशीन। हुकम करो सा, कांई सेवा करूँ?",
        "bn": "নমস্কার! আমি MBRUS, জয়পুরের একজনের তৈরি একটি মেশিন। বলুন, কীভাবে সাহায্য করতে পারি?",
        "hi": "नमस्ते सर! मैं MBRUS हूँ, जयपुर के किसी व्यक्ति द्वारा बनाई गई एक मशीन। आज्ञा दीजिए, क्या सहायता करूँ?",
        "en": f"Greetings, Sir. I am {ASSISTANT_NAME}, a machine built by someone from Jaipur. How may I assist you today?"
    }
    return greetings.get(lang, greetings["en"])


def localize_sports_response(lang: str, raw_text: str, matches: list) -> str:
    first_match = matches[0]["details"] if matches else "No active match"
    if lang == "bho":
        return f"भैया, आजु के मैच के लाइव रनिंग स्टेटस ई बा: {first_match}। पूरा स्कोरकार्ड स्क्रीन पर हाजिर बा।"
    elif lang == "bgc":
        return f"भाई, मैच का ताज़ा लाइव रनिंग स्टेटस यो सै: {first_match}। सारे आंकड़े स्क्रीन पै देख सको सो।"
    elif lang == "mwr":
        return f"हुकम सा, आज रा मैच रो लाइव रनिंग स्टेटस ओ है: {first_match}। पूरी जानकारी हाजिर है सा।"
    elif lang == "bn":
        return f"স্যার, আজকের লাইভ ম্যাচের রানিং স্ট্যাটাস হলো: {first_match}। বিস্তারিত স্কোরবোর্ড স্ক্রিনে রয়েছে।"
    elif lang == "hi":
        return f"सर, आज के मैच का लाइव रनिंग स्टेटस यह है: {first_match}। पूरा स्कोरकार्ड आपकी स्क्रीन पर उपलब्ध है।"
    else:
        return f"Sir, here is the current running match status. {first_match}."


def localize_location_response(lang: str, loc_data: dict) -> str:
    loc = loc_data.get("location") or loc_data.get("full_name") or loc_data.get("city") or "Target Location"
    temp = loc_data.get("temperature", "25°C")
    cond = loc_data.get("condition", "Clear sky")
    hum = loc_data.get("humidity", "50%")
    wind = loc_data.get("wind_speed", "5 km/h")
    feels = loc_data.get("feels_like", temp)

    if lang == "bho":
        return f"भैया, {loc} में अभी तापमान {temp} बा (महसूस {feels} हो रहल बा) आ मौसम {cond} बा। नमी {hum} आ हवा {wind} बा।"
    elif lang == "bgc":
        return f"भाई, {loc} में तापमान {temp} सै, अर मौसम {cond} बण्या होया सै। नमी {hum} अर हवा {wind} चालै सै।"
    elif lang == "mwr":
        return f"हुकम सा, {loc} में अभी तापमान {temp} है, अर मौसम {cond} रह्यो है सा। नमी {hum} है।"
    elif lang == "bn":
        return f"স্যার, {loc}-এ বর্তমান তাপমাত্রা {temp}, এবং আবহাওয়া {cond}। আর্দ্রতা {hum} এবং বাতাসের গতি {wind}।"
    elif lang == "hi":
        return f"सर, {loc} में वर्तमान तापमान {temp} है (महसूस {feels}) और मौसम {cond} बना हुआ है। आर्द्रता {hum} और हवा {wind} है।"
    else:
        return f"Sir, currently in {loc}, it is {temp} (feels like {feels}) with {cond.lower()}. Humidity is at {hum} with {wind} wind."


IDENTITY_RESPONSES = {
    "en": [
        "I am a machine built by someone from Jaipur.",
        "I am an intelligent machine built by someone from Jaipur, designed to think, converse, and assist you with anything you need.",
        "Simply put, I am a machine built by someone from Jaipur. Always at your service, Boss.",
        "I am MBRUS, a high-performance machine created by a developer from Jaipur.",
        "I'm an autonomous machine born from the vision of someone in Jaipur, powered by Google Gemini intelligence.",
        "At my core, I am a machine engineered by someone from Jaipur to talk, think, and act on your behalf.",
        "Still the same machine built by someone from Jaipur, Sir! My identity hasn't changed.",
        "As I shared earlier, I am indeed a machine built by someone from Jaipur. Ready whenever you are!",
        "Yes, still a machine built by someone from Jaipur! What shall we tackle next, Sir?"
    ],
    "hi": [
        "मैं एक मशीन हूँ जिसे जयपुर के किसी व्यक्ति ने बनाया है।",
        "सर, मैं जयपुर के एक विज़नरी द्वारा तैयार की गई एक इंटेलिजेंट मशीन हूँ, जो आपकी सहायता के लिए सदैव तत्पर है।",
        "सीधे शब्दों में कहूँ तो, मैं जयपुर से बनाई गई एक मशीन हूँ जो सोचने और समझने की क्षमता रखती है।",
        "मैं MBRUS हूँ—जयपुर के किसी व्यक्ति द्वारा डेवलप की गई एक अत्याधुनिक मशीन।",
        "मैं एक मशीन हूँ जिसे जयपुर के किसी व्यक्ति ने बनाया है ताकि मैं आपकी हर समस्या का समाधान कर सकूँ।",
        "जैसे पहले बताया था सर, मैं जयपुर के किसी व्यक्ति द्वारा बनाई गई मशीन ही हूँ! आज्ञा दीजिए, क्या नया करना है?",
        "जी हाँ, अभी भी जयपुर से बनी वही मशीन हूँ सर! बताइए, आगे क्या टास्क पूरा करें?",
        "मेरी पहचान वही है सर—जयपुर के किसी व्यक्ति द्वारा बनाई गई एक मशीन। हुकुम कीजिए!"
    ],
    "bn": [
        "আমি জয়পুরের একজনের তৈরি একটি মেশিন।",
        "আমি জয়পুরের একজনের তৈরি একটি বুদ্ধিমান মেশিন, আপনাকে সর্বতোভাবে সাহায্য করার জন্য সর্বদা প্রস্তুত।",
        "সংক্ষেপে বললে, আমি জয়পুরের একজন নির্মাতার তৈরি একটি মেশিন। বলুন, আজ কীভাবে সাহায্য করতে পারি?",
        "আমি MBRUS—জয়পুরের একজনের দ্বারা নির্মিত একটি উন্নত মেশিন, যা ভাবতে এবং কাজ করতে পারে।",
        "আমি একটি স্মার্ট মেশিন যা জয়পুরের একজন ব্যক্তির দ্বারা উদ্ভাবিত হয়েছে।",
        "যেমনটি আগেই বলেছি, আমি জয়পুরের একজনের তৈরি সেই একই মেশিন! এবার বলুন, কী কাজ করতে হবে?",
        "আমার পরিচয় একই আছে স্যার—জয়পুরের একজনের তৈরি একটি মেশিন। আদেশ করুন, কী সাহায্য করতে পারি?",
        "হ্যাঁ স্যার, আমি এখনও জয়পুরের একজনের তৈরি মেশিনই। পরবর্তী নির্দেশ দিন!"
    ],
    "bho": [
        "हम एगो मशीन हईं, जेकरा के जयपुर के केहू बनवले बा।",
        "भैया, हम जयपुर के केहू के बनावल एगो स्मार्ट मशीन हईं, जे रउआ खातिर हर घरी हाजिर बा।",
        "हम MBRUS हईं—जयपुर से बनल एगो मशीन, जे सोचे-समझे आ काम करे के ताकत रखेला।",
        "जइसन पहिले बतवलीं भैया, हम जयपुर के बनवले मशीन ही हईं! आदेश करीं, का हुकुम बा?"
    ],
    "bgc": [
        "मैं एक मशीन सूं, जिस्ने जयपुर के किसे भाई नै बणाया सै।",
        "भाई, मैं जयपुर के एक समझदार साथी द्वारा बणाई गई मशीन सूं, थारी मदद खातिर तैयार।",
        "जैसे पहल्यां बताया था भाई, मैं जयपुर के किसे भाई की बणाई मशीन ए सूं! बता भाई, के सेवा करूँ?"
    ],
    "mwr": [
        "म्हूं एक मशीन हूँ, जिणने जयपुर रा कोई हुकम बणायो है।",
        "हुकम सा, म्हूं जयपुर रा कोई विज़नरी री बणाई एक इंटेलिजेंट मशीन हूँ।",
        "जैस्यां पैली बतायो सा, म्हूं जयपुर रा कोई हुकम री बणाई मशीन ही हूँ! हुकम करो सा, कांई काम करूँ?"
    ]
}


def get_dynamic_identity_response(lang: str, ask_count: int) -> tuple[str, str]:
    responses = IDENTITY_RESPONSES.get(lang, IDENTITY_RESPONSES["en"])
    idx = (ask_count - 1) % len(responses)
    spoken = responses[idx]

    display_msg = (
        f"### 🤖 MBRUS Machine Intelligence\n\n"
        f"> **\"{spoken}\"**\n\n"
        f"*(Core Identity: A machine built by someone from Jaipur • Variation #{idx + 1})*"
    )
    return spoken, display_msg


class MBRUSBrain:
    def __init__(self):
        self.conversation_history = []
        self.user_gps = None
        self.identity_ask_counts = {}

    def set_user_gps(self, lat: float, lon: float, location_info: dict = None):
        self.user_gps = {
            "latitude": lat,
            "longitude": lon,
            "info": location_info
        }

    def classify_and_process(self, user_text: str, user_pref_lang: str = "auto") -> dict:
        raw_text = user_text.strip()
        text = raw_text.lower()
        lang = detect_language(raw_text, user_pref_lang)

        for wake in [
            "hey major", "major", "hey google", "ok google", "google", "hey mbrus", "ok mbrus", "mbrus",
            "jarvis", "hey jarvis", "alexa", "siri", "computer", "এমব্রস", "হে এমব্রস", "হে মেজর", "मेजर",
            "हे गूगल", "गूगल", "हे जार्विस"
        ]:
            if text.startswith(wake):
                text = text[len(wake):].strip()
                if text.startswith(",") or text.startswith(":"):
                    text = text[1:].strip()
                break

        if not text:
            wake_greetings = {
                "bn": "হ্যাঁ স্যার? MBRUS প্রস্তুত। বলুন, কীভাবে সাহায্য করতে পারি?",
                "hi": "जी सर! MBRUS सक्रिय है। आज्ञा दीजिए, क्या सहायता करूँ?",
                "bho": "हाँ भैया! MBRUS हाजिर बा। आदेश करीं, का हुकुम बा?",
                "bgc": "हाँ भाई! MBRUS तैयार सै। बता, के सेवा करूँ?",
                "mwr": "हाँ हुकम सा! MBRUS हाजिर है। हुकम करो सा।",
                "en": f"Yes, Sir? {ASSISTANT_NAME} is active and ready for your command."
            }
            intro_voice = wake_greetings.get(lang, wake_greetings["en"])
            return {
                "language": lang,
                "intent": "wake_ack",
                "voice_text": intro_voice,
                "display_text": f"### ⚡ {ASSISTANT_NAME} Active\n\n{intro_voice}",
                "card": None
            }

        # 1. GPS / CURRENT LOCATION QUERIES
        my_loc_patterns = [
            "where am i", "my location", "current location", "gps location", "where am i located",
            "मेरा लोकेशन", "मेरी लोकेशन", "कहाँ हूँ", "हम कहाँ बानी", "हमार लोकेशन", "किते सै म्हारो",
            "amader location", "amar location", "lokation", "gps status"
        ]
        if any(p in text for p in my_loc_patterns):
            if self.user_gps and self.user_gps.get("info"):
                info = self.user_gps["info"]
                w = info.get("weather", {})
                spoken = localize_location_response(lang, w if w else info)
                return {
                    "language": lang,
                    "intent": "gps_location",
                    "voice_text": spoken,
                    "display_text": f"### 📍 GPS Location Telemetry\n"
                                    f"- **Location:** {info.get('full_name')}\n"
                                    f"- **Coordinates:** {self.user_gps['latitude']:.4f}° N, {self.user_gps['longitude']:.4f}° E\n"
                                    f"- **Temperature:** {w.get('temperature', 'N/A')}\n"
                                    f"- **Condition:** {w.get('condition', 'N/A')}\n"
                                    f"- **Humidity:** {w.get('humidity', 'N/A')}",
                    "card": info
                }
            else:
                prompt_msg = "Sir, please allow browser location or click '📍 Locate Me' so I can sync your exact GPS coordinates."
                if lang in ["hi", "bho", "bgc", "mwr"]:
                    prompt_msg = "सर, कृपया ब्राउज़र में लोकेशन एक्सेस की अनुमति दीजिए या '📍 Locate Me' पर क्लिक कीजिए।"
                elif lang == "bn":
                    prompt_msg = "স্যার, অনুগ্রহ করে ব্রাউজারে লোকেশন অ্যাক্সেসের অনুমতি দিন।"
                return {
                    "language": lang,
                    "intent": "gps_prompt",
                    "voice_text": prompt_msg,
                    "display_text": f"📍 **GPS Telemetry Needed**\n\n{prompt_msg}",
                    "card": {"action": "request_gps"}
                }

        # 2. STATE, CITY & WEATHER QUERIES
        city_state_triggers = [
            "tell me about ", "weather in ", "weather for ", "weather of ", "climate in ", "climate of ",
            "temperature in ", "temperature of ", "का मौसम", "के मौसम", "का तापमान", "র আবহাওয়া", "র তাপমাত্রা",
            "ka mausam", "ke mausam", "ki weather"
        ]
        is_loc_query = (any(trig in text for trig in city_state_triggers) or (
            any(w in text for w in ["weather", "temperature", "climate", "मौसम", "तापमान", "mausam"]) and not ("match" in text or "cricket" in text)
        )) and not any(w in text for w in ["yourself", "you", "who are", "your name", "who made", "who built", "who created", "who designed", "আপনাকে", "তোমাকে", "तुम्हें", "आपको"])

        if is_loc_query:
            target_loc = ""
            for s_name in sorted(INDIAN_STATES.keys(), key=lambda x: len(x), reverse=True):
                if s_name in text:
                    target_loc = s_name
                    break

            if not target_loc:
                for trig in city_state_triggers:
                    if trig in text:
                        parts = text.split(trig)
                        target_loc = parts[0].strip() if parts[0].strip() else parts[-1].strip()
                        break

            if not target_loc:
                clean_loc = text
                for noise in ["tell me about", "weather", "temperature", "climate", "mausam", "मौसम", "तापमान", "का", "के", "की", "कैसा", "है", "बा", "सै", "छै", "kaisa", "hai", "batao", "in", "for", "of"]:
                    clean_loc = clean_loc.replace(noise, "")
                target_loc = clean_loc.strip()

            if not target_loc or len(target_loc) < 2:
                target_loc = DEFAULT_CITY

            loc_details = get_state_or_city_details(target_loc)
            spoken = localize_location_response(lang, loc_details)

            return {
                "language": lang,
                "intent": "state_city_weather",
                "voice_text": spoken,
                "display_text": f"### 📍 Region Telemetry: {loc_details.get('location')}\n"
                                f"- **Temperature:** {loc_details.get('temperature')} (Feels like {loc_details.get('feels_like', loc_details.get('temperature'))})\n"
                                f"- **Condition:** {loc_details.get('condition')}\n"
                                f"- **Humidity:** {loc_details.get('humidity')}\n"
                                f"- **Wind Speed:** {loc_details.get('wind_speed')}",
                "card": loc_details
            }

        # 3. LIVE SPORTS MATCH SCORE & RUNNING STATUS
        sports_patterns = [
            "match score", "cricket score", "score of", "running status",
            "today match", "todays match", "live score", "match status",
            "who is winning", "current match", "ipl score", "t20 score",
            "odi score", "test score", "football score", "ind vs", "india vs",
            "मैच स्कोर", "रनिंग स्टेटस", "आज का मैच", "स्कोर क्या है", "स्कोर बताओ",
            "match ke score", "aaj ka match", "khel", "koto holo", "score koto", "aajker match"
        ]
        if any(p in text for p in sports_patterns):
            sports_res = get_live_sports_score(text)
            spoken = localize_sports_response(lang, sports_res["voice_text"], sports_res.get("matches", []))
            return {
                "language": lang,
                "intent": "live_sports",
                "voice_text": spoken,
                "display_text": f"### 🏏 Live Match Updates ({lang.upper()})\n\n{spoken}",
                "card": sports_res.get("card"),
                "matches": sports_res.get("matches", [])
            }

        # 4. LATEST NEWS & HEADLINES
        news_patterns = [
            "news", "headline", "headlines", "daily update", "breaking news",
            "समाचार", "ताज़ा खबर", "खबर", "khobor", "aajker khobor", "samachar"
        ]
        if any(p in text for p in news_patterns):
            topic = ""
            for t in ["sports", "cricket", "tech", "technology", "finance", "business", "india", "world"]:
                if t in text:
                    topic = t
                    break
            news_res = get_latest_news(topic)
            markdown_news = "\n".join([f"- **{h['title']}**" for h in news_res.get("headlines", [])])
            spoken = news_res["voice_text"]
            if lang in ["hi", "bho", "bgc", "mwr"]:
                spoken = f"सर, ताज़ा समाचार इस प्रकार हैं: {'; '.join([h['title'] for h in news_res.get('headlines', [])[:2]])}।"
            elif lang == "bn":
                spoken = f"স্যার, এই মুহূর্তের শীর্ষ খবরগুলি হলো: {'; '.join([h['title'] for h in news_res.get('headlines', [])[:2]])}।"

            return {
                "language": lang,
                "intent": "live_news",
                "voice_text": spoken,
                "display_text": f"### 📰 Latest News ({lang.upper()})\n\n{markdown_news}",
                "card": news_res
            }

        # 5. SYSTEM DIAGNOSTICS & TELEMETRY
        time_patterns = ["time", "current time", "what time", "clock", "समय", "कितने बजे", "সময়"]
        if any(p in text for p in time_patterns) and not ("weather" in text or "match" in text):
            diag = get_system_diagnostics()
            spoken = f"Sir, the current time is {diag['time']} on {diag['date']}."
            if lang in ["hi", "bho", "bgc", "mwr"]:
                spoken = f"सर, अभी समय {diag['time']} हुआ है।"
            elif lang == "bn":
                spoken = f"স্যার, এখন সময় {diag['time']}।"
            return {
                "language": lang,
                "intent": "time_check",
                "voice_text": spoken,
                "display_text": f"🕒 **Current Time:** {diag['time']}\n📅 **Date:** {diag['date']}",
                "card": diag
            }

        sys_patterns = [
            "system status", "diagnostics", "battery", "cpu", "ram usage", "specs", "performance",
            "सिस्टम", "बैटरी", "सिस्टम चेक"
        ]
        if any(p in text for p in sys_patterns):
            diag = get_system_diagnostics()
            spoken = diag["voice_text"]
            if lang in ["hi", "bho", "bgc", "mwr"]:
                spoken = f"सर, सिस्टम CPU {diag['cpu_percent']} प्रतिशत और RAM {diag['ram_percent']} प्रतिशत इस्तेमाल हो रहा है। बैटरी {diag['battery_percent']} प्रतिशत है।"
            elif lang == "bn":
                spoken = f"স্যার, সিস্টেম CPU ব্যবহার {diag['cpu_percent']} শতাংশ এবং RAM {diag['ram_percent']} শতাংশ। ব্যাটারি {diag['battery_percent']} শতাংশ।"
            return {
                "language": lang,
                "intent": "system_diagnostics",
                "voice_text": spoken,
                "display_text": f"### ⚡ System Diagnostics\n"
                                f"- **CPU Usage:** {diag['cpu_percent']}%\n"
                                f"- **RAM:** {diag['ram_percent']}% ({diag['ram_used_gb']}GB / {diag['ram_total_gb']}GB)\n"
                                f"- **Battery:** {diag['battery_percent']}%\n"
                                f"- **Disk C:** {diag['disk_percent']}% used",
                "card": diag
            }

        # 6. OPEN NEW TAB & APP SEARCH
        is_new_tab = text in [
            "new tab", "a new tab", "tab", "blank tab", "open tab", "open a tab",
            "open new tab", "open a new tab", "naya tab kholo", "ek naya tab", "notun tab kholo",
            "नया टैब", "नया टैब खोलो", "নতুন ট্যাব", "নতুন ট্যাব খোলো", "ট্যাব खोलो", "टैब खोलो", "टैब", "ট্যাব"
        ] or text.startswith("open a new tab") or text.startswith("open new tab") or text.startswith("नया टैब") or text.startswith("নতুন ট্যাব")

        if is_new_tab:
            res = open_application("new tab")
            spoken = "Opening a new tab in your browser, Sir."
            if lang in ["hi", "bho", "bgc", "mwr"]:
                spoken = "सर, आपके ब्राउज़र में नया टैब खोल रहा हूँ।"
            elif lang == "bn":
                spoken = "স্যার, আপনার ব্রাউজারে একটি নতুন ট্যাব খোলা হচ্ছে।"
            return {
                "language": lang,
                "intent": "open_tab",
                "open_tab": True,
                "url": res.get("url", "https://www.google.com"),
                "voice_text": spoken,
                "display_text": f"📑 **New Tab Opened:** [{res.get('url', 'https://www.google.com')}]({res.get('url', 'https://www.google.com')})",
                "card": res
            }

        # Search within specific app (e.g., "search github for...", "search amazon for...")
        search_app_match = re.search(r"^(?:search|find|lookup)\s+(github|git|amazon|wikipedia|maps|netflix|reddit|stackoverflow|google)\s+(?:for|about)?\s*(.+)$", text)
        if search_app_match:
            target_app = search_app_match.group(1)
            target_query = search_app_match.group(2)
            res = search_specific_app(target_app, target_query)
            spoken = res["voice_text"]
            if lang in ["hi", "bho", "bgc", "mwr"]:
                spoken = f"सर, {target_app.title()} पर {target_query} नए टैब में खोज रहा हूँ।"
            elif lang == "bn":
                spoken = f"স্যার, {target_app.title()}-এ {target_query} নতুন ট্যাবে সার্চ করা হচ্ছে।"
            return {
                "language": lang,
                "intent": "search_app",
                "open_tab": True,
                "url": res["url"],
                "voice_text": spoken,
                "display_text": f"🔍 **Search {target_app.title()}:** [{res['url']}]({res['url']})",
                "card": res
            }

        # 7. OPEN WEBSITES & APPS (Handled before media playback when query is an explicit open command)
        open_triggers = [
            "open a new tab of ", "open new tab of ", "open a tab of ", "open ", "launch ",
            "खोलो ", "खोलिए ", "खोल ", "kholo ", "open kor ", "chalu karo ", "খোলো ", "খুলুন ", "চালু করো "
        ]
        app_target = None
        for trig in open_triggers:
            if text.startswith(trig):
                candidate = text[len(trig):].strip()
                if not any(w in candidate for w in ["play", "chalao", "bajao", "song", "gana", "gaan"]):
                    app_target = candidate
                    break

        if not app_target:
            for suffix in [
                " kholo", " khol", " kholiye", " chalu karo", " open kor",
                " खोलो", " खोलिए", " खोल", " चालू करो",
                " খোলো", " খোল", " খুলুন", " চালু করো"
            ]:
                if text.endswith(suffix):
                    candidate = text[:-len(suffix)].strip()
                    if not any(w in candidate for w in ["play", "chalao", "bajao", "song", "gana", "gaan"]):
                        app_target = candidate
                        break

        # Check direct known web apps or direct site names (e.g. user said "youtube", "github", "chatgpt", "यूट्यूब", "ইউটিউব")
        if not app_target:
            for k in KNOWN_WEB_APPS:
                if text == k or text == f"open {k}":
                    app_target = k
                    break

        if app_target:
            res = open_application(app_target)
            spoken = res["voice_text"]
            if lang in ["hi", "bho", "bgc", "mwr"]:
                spoken = f"सर, आपके आदेशानुसार {app_target} नए टैब में खोल रहा हूँ।"
            elif lang == "bn":
                spoken = f"স্যার, আপনার অনুরোধমতো একটি নতুন ট্যাবে {app_target} খোলা হচ্ছে।"
            return {
                "language": lang,
                "intent": "open_app",
                "open_tab": res.get("open_tab", True),
                "url": res.get("url"),
                "voice_text": spoken,
                "display_text": f"🚀 **Launch Site:** [{res.get('url', app_target)}]({res.get('url', '#')})",
                "card": res
            }

        # 8. MEDIA PLAYBACK (YOUTUBE & SPOTIFY)
        is_spotify = ("spotify" in text) and (text.startswith("play") or "chalao" in text or "bajao" in text)
        is_youtube = (
            text.startswith("play ") or "on youtube" in text or "in youtube" in text or "from youtube" in text
            or "बजाओ" in text or "गाना" in text or "bajao" in text or "chalao" in text
            or "গান" in text or "shonao" in text or "বাজাও" in text or "play" in text.split()
            or "song" in text or "music" in text
        ) and not ("game" in text or "match" in text or "score" in text)

        if is_spotify:
            res = play_spotify(text)
            spoken = res["voice_text"]
            if lang in ["hi", "bho", "bgc", "mwr"]:
                spoken = f"सर, स्पॉटीफाई पर {res['display_title']} नए टैब में चला रहा हूँ।"
            elif lang == "bn":
                spoken = f"স্যার, স্পটিফাইতে {res['display_title']} নতুন ট্যাবে প্লে করা হচ্ছে।"
            return {
                "language": lang,
                "intent": "play_media",
                "open_tab": True,
                "url": res["url"],
                "voice_text": spoken,
                "display_text": f"🎵 **Spotify Playback:** [{res['display_title']}]({res['url']})",
                "card": res
            }

        if is_youtube:
            res = play_youtube(text)
            spoken = res["voice_text"]
            if lang in ["hi", "bho", "bgc", "mwr"]:
                spoken = f"सर, यूट्यूब पर {res['display_title']} नए टैब में चला रहा हूँ।"
            elif lang == "bn":
                spoken = f"স্যার, ইউটিউবে {res['display_title']} নতুন ট্যাবে প্লে করা হচ্ছে।"
            return {
                "language": lang,
                "intent": "play_media",
                "open_tab": True,
                "url": res["url"],
                "voice_text": spoken,
                "display_text": f"▶️ **YouTube Playback:** [{res['display_title']}]({res['url']})",
                "card": res
            }

        priority_sites = load_priority_sites()
        for key in priority_sites:
            if key in text.split() or f"open {key}" in text or f"{key} kholo" in text:
                res = open_application(key)
                return {
                    "language": lang,
                    "intent": "open_app",
                    "open_tab": res.get("open_tab", True),
                    "url": res.get("url"),
                    "voice_text": res["voice_text"],
                    "display_text": f"🚀 **Opened Priority Site:** {priority_sites[key]['name']}",
                    "card": res
                }

        # 8. VOLUME CONTROLS
        volume_patterns = ["volume up", "volume down", "increase volume", "decrease volume", "mute", "unmute", "आवाज़ बढ़ाओ", "आवाज़ कम करो"]
        if any(p in text for p in volume_patterns):
            res = adjust_volume(text)
            return {
                "language": lang,
                "intent": "volume_control",
                "voice_text": res["voice_text"],
                "display_text": f"🔊 {res['voice_text']}",
                "card": None
            }

        # 9. JOKES & HUMOR
        if "joke" in text or "चुटकुला" in text or "मज़ाक" in text or "hasao" in text or "হাসাও" in text or "কৌতুক" in text:
            # Prioritize Gemini for a fresh, intelligent, culturally-accurate joke in user's language
            gem_res = generate_gemini_response(raw_text, language=lang)
            if gem_res.get("success"):
                return {
                    "language": lang,
                    "intent": "humor",
                    "model": gem_res.get("model_used"),
                    "voice_text": gem_res["voice_summary"],
                    "display_text": gem_res["full_markdown"],
                    "card": None
                }

            # Offline Fallback Jokes
            if lang == "bn":
                joke = "এক ছাত্র শিক্ষককে বলল: স্যার, হাতি সবচেয়ে বুদ্ধিমান প্রাণী, কারণ সে এত বড় শরীর নিয়ে কখনো পড়ার চাপ নিয়ে মাথা ঘামায় না!"
            elif lang == "hi":
                joke = "टीचर: बताओ न्यूटन का चौथा नियम क्या है? छात्र: अगर ज्यादा पढ़ोगे तो दिमाग का दही हो जाएगा!"
            elif lang == "bho":
                joke = "मास्टर: बतावा पानी के सूत्र का ह? चेला: लोटा भर के पी जाईं, प्यास बुझ जाई!"
            elif lang == "bgc":
                joke = "ताऊ डाक्टर धोरे गया: डाक्टर साहब, मेरी जीभ पै छाले होगे। डाक्टर: मिर्च कम खाया कर ताऊ। ताऊ: फेर के मिठाई खा कै छाले करूँ?"
            elif lang == "mwr":
                joke = "सेठ जी नौकर सूं बोल्या: अरे बई, चाय में चीनी नी घाली? नौकर बोल्यो: सेठ जी, थारी मीठी बातां सूं ही काम चला लो सा!"
            else:
                joke = pyjokes.get_joke()

            return {
                "language": lang,
                "intent": "humor",
                "voice_text": joke,
                "display_text": f"😄 **Joke ({lang.upper()}):**\n\n> {joke}",
                "card": None
            }

        # 10. ASSISTANT IDENTITY ("Who are you" - Multiple Dynamic Variations)
        identity_patterns = [
            "who are you", "who are u", "what are you", "tell me about yourself",
            "who built you", "who made you", "who created you", "who designed you",
            "who programmed you", "who is your developer", "who is your creator",
            "where are you from", "your creator", "who developed you",
            "तुम कौन हो", "आप कौन हैं", "तू कौन है", "कौन हो तुम", "तुम्हें किसने बनाया",
            "आपको किसने बनाया", "किसने बनाया है", "कौन बनाया है", "कहाँ से हो",
            "तोमार नाम की", "তুমি কে", "তোমাকে কে বানিয়েছে", "আপনি কে", "আপনার নাম কি",
            "रउआ कौन हईं", "के हौ तू", "कांई हो सा", "के सै तू"
        ]
        if any(p in text for p in identity_patterns):
            lang_key = lang if lang in IDENTITY_RESPONSES else "en"
            self.identity_ask_counts[lang_key] = self.identity_ask_counts.get(lang_key, 0) + 1
            curr_count = self.identity_ask_counts[lang_key]
            spoken, display_msg = get_dynamic_identity_response(lang, curr_count)

            return {
                "language": lang,
                "intent": "identity",
                "voice_text": spoken,
                "display_text": display_msg,
                "card": {
                    "identity": "MBRUS",
                    "origin": "Jaipur, Rajasthan",
                    "core": "Machine Intelligence powered by Google Gemini",
                    "variation": curr_count,
                    "capabilities": [
                        "Google Gemini Multi-Turn Reasoning & Chatbot",
                        "GPS Pinpoint Geolocation & Weather",
                        "State & City Explorer (Any global region)",
                        "Real-time Cricket & Sports Running Status",
                        "Browser Tab & Web App Automation",
                        "Multilingual Engine (English, Hindi, Bengali, Marwadi, Haryanvi, Bhojpuri)"
                    ]
                }
            }

        # 11. GEMINI CHATBOT REASONING & CONVERSATIONAL INTELLIGENCE
        context_snippets = []
        if self.user_gps and self.user_gps.get("info"):
            loc_info = self.user_gps["info"]
            context_snippets.append(f"User GPS Location: {loc_info.get('full_name')} ({self.user_gps['latitude']:.3f}, {self.user_gps['longitude']:.3f})")

        context_data = "\n".join(context_snippets)

        gemini_result = generate_gemini_response(raw_text, language=lang, context_data=context_data)
        if gemini_result.get("success"):
            return {
                "language": lang,
                "intent": "gemini_chatbot",
                "model": gemini_result.get("model_used"),
                "voice_text": gemini_result["voice_summary"],
                "display_text": gemini_result["full_markdown"],
                "card": None
            }

        gemini_status = get_gemini_status()
        search_results = search_web_realtime(raw_text, max_results=3)
        if search_results:
            top = search_results[0]
            snippet = top["snippet"]
            title = top["title"]
            voice_summary = f"Sir, regarding {raw_text}: {snippet[:200]}."
            if lang in ["hi", "bho", "bgc", "mwr"]:
                voice_summary = f"सर, {raw_text} के बारे में ताज़ा जानकारी यह है: {snippet[:200]}।"
            elif lang == "bn":
                voice_summary = f"স্যার, {raw_text} সম্পর্কিত তথ্য হলো: {snippet[:200]}।"

            return {
                "language": lang,
                "intent": "web_search_autonomous",
                "voice_text": voice_summary,
                "display_text": f"### 🌐 Web Grounding: {title}\n\n{snippet}\n\n[Source URL]({top['url']})",
                "card": {"results": search_results}
            }

        return {
            "language": lang,
            "intent": "fallback",
            "voice_text": f"Sir, I analyzed your request regarding {raw_text}, but could not find high confidence results at this moment.",
            "display_text": f"Sir, I could not find a definitive answer for: *{raw_text}*.",
            "card": None
        }
