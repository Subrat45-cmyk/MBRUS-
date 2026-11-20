"""
MBRUS System Control Engine
Automates Windows applications, priority websites, volume, browser shortcuts, media playback, and hardware diagnostics.
"""

import os
import re
import json
import subprocess
import webbrowser
import urllib.parse
import datetime
from pathlib import Path
import psutil
import pyautogui

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "priority_sites.json"

KNOWN_WEB_APPS = {
    "youtube": {"name": "YouTube", "url": "https://www.youtube.com", "icon": "▶️"},
    "yt": {"name": "YouTube", "url": "https://www.youtube.com", "icon": "▶️"},
    "github": {"name": "GitHub", "url": "https://github.com", "icon": "🐙"},
    "git": {"name": "GitHub", "url": "https://github.com", "icon": "🐙"},
    "gmail": {"name": "Gmail", "url": "https://mail.google.com", "icon": "✉️"},
    "mail": {"name": "Gmail", "url": "https://mail.google.com", "icon": "✉️"},
    "email": {"name": "Gmail", "url": "https://mail.google.com", "icon": "✉️"},
    "chatgpt": {"name": "ChatGPT", "url": "https://chatgpt.com", "icon": "🤖"},
    "chat gpt": {"name": "ChatGPT", "url": "https://chatgpt.com", "icon": "🤖"},
    "openai": {"name": "ChatGPT", "url": "https://chatgpt.com", "icon": "🤖"},
    "spotify": {"name": "Spotify", "url": "https://open.spotify.com", "icon": "🎵"},
    "whatsapp": {"name": "WhatsApp Web", "url": "https://web.whatsapp.com", "icon": "💬"},
    "twitter": {"name": "X (Twitter)", "url": "https://x.com", "icon": "🐦"},
    "x": {"name": "X (Twitter)", "url": "https://x.com", "icon": "✖️"},
    "netflix": {"name": "Netflix", "url": "https://www.netflix.com", "icon": "🍿"},
    "reddit": {"name": "Reddit", "url": "https://www.reddit.com", "icon": "🔴"},
    "canva": {"name": "Canva", "url": "https://www.canva.com", "icon": "🎨"},
    "amazon": {"name": "Amazon", "url": "https://www.amazon.in", "icon": "📦"},
    "linkedin": {"name": "LinkedIn", "url": "https://www.linkedin.com", "icon": "💼"},
    "maps": {"name": "Google Maps", "url": "https://maps.google.com", "icon": "🗺️"},
    "google maps": {"name": "Google Maps", "url": "https://maps.google.com", "icon": "🗺️"},
    "google": {"name": "Google", "url": "https://www.google.com", "icon": "🔍"},
    "new tab": {"name": "New Tab", "url": "https://www.google.com", "icon": "📑"},
    "a new tab": {"name": "New Tab", "url": "https://www.google.com", "icon": "📑"},
    "tab": {"name": "New Tab", "url": "https://www.google.com", "icon": "📑"},
    "blank tab": {"name": "New Tab", "url": "https://www.google.com", "icon": "📑"},
    "नया टैब": {"name": "New Tab", "url": "https://www.google.com", "icon": "📑"},
    "নতুন ট্যাব": {"name": "New Tab", "url": "https://www.google.com", "icon": "📑"},
    "टैब": {"name": "New Tab", "url": "https://www.google.com", "icon": "📑"},
    "ট্যাব": {"name": "New Tab", "url": "https://www.google.com", "icon": "📑"},
    "यूट्यूब": {"name": "YouTube", "url": "https://www.youtube.com", "icon": "▶️"},
    "ইউটিউব": {"name": "YouTube", "url": "https://www.youtube.com", "icon": "▶️"},
    "व्हाट्सएप": {"name": "WhatsApp Web", "url": "https://web.whatsapp.com", "icon": "💬"},
    "হোয়াটসঅ্যাপ": {"name": "WhatsApp Web", "url": "https://web.whatsapp.com", "icon": "💬"},
    "जीमेल": {"name": "Gmail", "url": "https://mail.google.com", "icon": "✉️"},
    "জিমেল": {"name": "Gmail", "url": "https://mail.google.com", "icon": "✉️"},
    "गूगल": {"name": "Google", "url": "https://www.google.com", "icon": "🔍"},
    "গুগল": {"name": "Google", "url": "https://www.google.com", "icon": "🔍"},
    "गिटहब": {"name": "GitHub", "url": "https://github.com", "icon": "🐙"},
    "গিটহাব": {"name": "GitHub", "url": "https://github.com", "icon": "🐙"},
    "stackoverflow": {"name": "Stack Overflow", "url": "https://stackoverflow.com", "icon": "💻"},
    "wikipedia": {"name": "Wikipedia", "url": "https://www.wikipedia.org", "icon": "📖"},
    "instagram": {"name": "Instagram", "url": "https://www.instagram.com", "icon": "📸"},
    "facebook": {"name": "Facebook", "url": "https://www.facebook.com", "icon": "📘"}
}

def load_priority_sites() -> dict:
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[SystemControl] Error reading priority sites: {e}")
    return {}


def save_priority_sites(sites: dict) -> bool:
    try:
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(sites, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[SystemControl] Error saving priority sites: {e}")
        return False


def add_priority_site(key: str, name: str, url: str, icon: str = "🌐", category: str = "Custom") -> dict:
    sites = load_priority_sites()
    clean_key = key.lower().strip()
    clean_url = url if url.startswith("http") else f"https://{url}"
    sites[clean_key] = {
        "name": name or clean_key.title(),
        "url": clean_url,
        "icon": icon,
        "category": category
    }
    save_priority_sites(sites)
    return {"success": True, "message": f"Added {name} to priority list", "site": sites[clean_key]}


def remove_priority_site(key: str) -> dict:
    sites = load_priority_sites()
    clean_key = key.lower().strip()
    if clean_key in sites:
        deleted = sites.pop(clean_key)
        save_priority_sites(sites)
        return {"success": True, "message": f"Removed {deleted['name']} from priority list"}
    return {"success": False, "message": "Site not found in priority list"}


def get_system_diagnostics() -> dict:
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("C:\\")
    battery = psutil.sensors_battery()
    now = datetime.datetime.now()

    bat_status = "Not plugged in"
    bat_pct = 100
    if battery:
        bat_pct = round(battery.percent)
        bat_status = "Charging" if battery.power_plugged else "Discharging"

    time_str = now.strftime("%I:%M %p")
    date_str = now.strftime("%A, %B %d, %Y")

    voice_summary = (
        f"Sir, system CPU is at {cpu} percent, memory usage is at {mem.percent} percent. "
        f"Battery is at {bat_pct} percent and currently {bat_status.lower()}. "
        f"The time is {time_str} on {now.strftime('%A')}."
    )

    return {
        "cpu_percent": cpu,
        "ram_percent": mem.percent,
        "ram_used_gb": round(mem.used / (1024 ** 3), 1),
        "ram_total_gb": round(mem.total / (1024 ** 3), 1),
        "disk_percent": disk.percent,
        "battery_percent": bat_pct,
        "battery_charging": battery.power_plugged if battery else True,
        "time": time_str,
        "date": date_str,
        "voice_text": voice_summary
    }


def open_application(target: str) -> dict:
    clean_target = target.lower().strip()
    # Strip common command prefixes
    for prefix in ["open a new tab in ", "open new tab in ", "open a tab for ", "open new tab ", "open a new tab ", "open tab ", "open a ", "open ", "launch ", "go to "]:
        if clean_target.startswith(prefix):
            clean_target = clean_target[len(prefix):].strip()
            break

    # 1. Check Known Web Applications & New Tab requests
    if clean_target in KNOWN_WEB_APPS:
        app_info = KNOWN_WEB_APPS[clean_target]
        url = app_info["url"]
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"[SystemControl] webbrowser open warning: {e}")
        return {
            "success": True,
            "open_tab": True,
            "url": url,
            "site": app_info,
            "voice_text": f"Opening {app_info['name']} in a new tab for you, Sir.",
            "action": f"Navigated to {url}"
        }

    # Partial match for Known Web Apps (e.g. 'yt', 'whatsapp', 'chatgpt')
    for key, app_info in KNOWN_WEB_APPS.items():
        if key == clean_target or f" {key} " in f" {clean_target} ":
            url = app_info["url"]
            try:
                webbrowser.open(url)
            except Exception as e:
                print(f"[SystemControl] webbrowser open warning: {e}")
            return {
                "success": True,
                "open_tab": True,
                "url": url,
                "site": app_info,
                "voice_text": f"Opening {app_info['name']} in a new tab for you, Sir.",
                "action": f"Navigated to {url}"
            }

    # 2. Check User-saved Priority Sites
    priority_sites = load_priority_sites()
    for key, site in priority_sites.items():
        if key in clean_target or clean_target in key or site["name"].lower() in clean_target:
            try:
                webbrowser.open(site["url"])
            except Exception as e:
                print(f"[SystemControl] webbrowser open warning: {e}")
            return {
                "success": True,
                "open_tab": True,
                "url": site["url"],
                "voice_text": f"Opening {site['name']} in a new tab for you, Sir.",
                "action": f"Navigated to {site['url']}",
                "site": site
            }

    # 3. Check Native Windows Applications
    native_apps = {
        "calculator": "calc.exe",
        "calc": "calc.exe",
        "notepad": "notepad.exe",
        "cmd": "cmd.exe",
        "command prompt": "cmd.exe",
        "terminal": "powershell.exe",
        "powershell": "powershell.exe",
        "vs code": "code",
        "code": "code",
        "file explorer": "explorer.exe",
        "files": "explorer.exe",
        "chrome": "chrome.exe",
        "spotify": "spotify.exe"
    }

    for key, binary in native_apps.items():
        if key == clean_target or key in clean_target:
            try:
                subprocess.Popen(binary, shell=True)
                return {
                    "success": True,
                    "open_tab": False,
                    "voice_text": f"Launching {key.title()} on your system, Sir.",
                    "action": f"Executed {binary}"
                }
            except Exception as e:
                print(f"[SystemControl] App error: {e}")

    # 4. Direct domain URL (e.g. 'github.com', 'google.com', 'facebook.com')
    if "." in clean_target and " " not in clean_target:
        url = clean_target if clean_target.startswith("http") else f"https://{clean_target}"
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"[SystemControl] webbrowser open warning: {e}")
        return {
            "success": True,
            "open_tab": True,
            "url": url,
            "voice_text": f"Opening {clean_target} in a new tab, Sir.",
            "action": f"Navigated to {url}"
        }

    # 5. Fallback Web Search in New Tab
    search_url = f"https://www.google.com/search?q={urllib.parse.quote(clean_target)}"
    try:
        webbrowser.open(search_url)
    except Exception as e:
        print(f"[SystemControl] webbrowser open warning: {e}")
    return {
        "success": True,
        "open_tab": True,
        "url": search_url,
        "voice_text": f"Opening web search for {clean_target} in a new tab, Sir.",
        "action": f"Navigated to {search_url}"
    }


def play_youtube(query: str) -> dict:
    # Clean query from command phrasing
    raw = query.lower()
    noise_pattern = (
        r"\b(play|on youtube|in youtube|from youtube|youtube|that song|some song|a song|"
        r"or something|or anything|something|anything|song|songs|video|music|track|"
        r"or|and|that|this|some|a|an|the|in|on|to|for|me|"
        r"gaan|gaana|gana|chalao|bajao|baja do|shonao|kholo|chalav)\b|"
        r"(गाना|बजाओ|चलाओ|गीत|গান|শোনাও|বাজাও)"
    )
    clean_q = re.sub(noise_pattern, " ", raw, flags=re.IGNORECASE).strip()
    clean_q = re.sub(r"\s+", " ", clean_q).strip()

    # If query is empty or purely generic (like "play that song or something on youtube")
    if not clean_q or len(clean_q) < 2 or clean_q in ["that", "this", "or", "and", "something"]:
        display_title = "Trending Top Hits"
        search_query = "trending top hits music songs"
        url = "https://www.youtube.com/results?search_query=trending+top+hits+music+songs"
    else:
        display_title = clean_q.title()
        search_query = clean_q
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(clean_q)}"

    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"[SystemControl] webbrowser open warning: {e}")

    return {
        "success": True,
        "open_tab": True,
        "url": url,
        "query": search_query,
        "display_title": display_title,
        "voice_text": f"Playing {display_title} on YouTube in a new tab, Sir."
    }


def play_spotify(query: str) -> dict:
    raw = query.lower()
    noise_pattern = r"\b(play|on spotify|in spotify|from spotify|spotify|that song|some song|a song|something|song|songs|music|track|chalao|bajao)\b"
    clean_q = re.sub(noise_pattern, " ", raw, flags=re.IGNORECASE).strip()
    clean_q = re.sub(r"\s+", " ", clean_q).strip()

    if not clean_q or len(clean_q) < 2:
        display_title = "Top Hits"
        url = "https://open.spotify.com"
    else:
        display_title = clean_q.title()
        url = f"https://open.spotify.com/search/{urllib.parse.quote(clean_q)}"

    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"[SystemControl] webbrowser open warning: {e}")

    return {
        "success": True,
        "open_tab": True,
        "url": url,
        "query": clean_q,
        "display_title": display_title,
        "voice_text": f"Playing {display_title} on Spotify in a new tab, Sir."
    }


def search_specific_app(app_name: str, query: str) -> dict:
    clean_q = query.strip()
    app_key = app_name.lower().strip()

    search_urls = {
        "github": f"https://github.com/search?q={urllib.parse.quote(clean_q)}",
        "git": f"https://github.com/search?q={urllib.parse.quote(clean_q)}",
        "amazon": f"https://www.amazon.in/s?k={urllib.parse.quote(clean_q)}",
        "wikipedia": f"https://en.wikipedia.org/wiki/Special:Search?search={urllib.parse.quote(clean_q)}",
        "maps": f"https://www.google.com/maps/search/{urllib.parse.quote(clean_q)}",
        "netflix": f"https://www.netflix.com/search?q={urllib.parse.quote(clean_q)}",
        "reddit": f"https://www.reddit.com/search/?q={urllib.parse.quote(clean_q)}",
        "stackoverflow": f"https://stackoverflow.com/search?q={urllib.parse.quote(clean_q)}",
        "google": f"https://www.google.com/search?q={urllib.parse.quote(clean_q)}"
    }

    url = search_urls.get(app_key, f"https://www.google.com/search?q={urllib.parse.quote(clean_q)}")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"[SystemControl] webbrowser open warning: {e}")

    return {
        "success": True,
        "open_tab": True,
        "url": url,
        "query": clean_q,
        "voice_text": f"Searching {app_name.title()} for {clean_q} in a new tab, Sir."
    }


def search_google(query: str) -> dict:
    clean_q = query.replace("search for", "").replace("search", "").replace("google", "").strip()
    url = f"https://www.google.com/search?q={urllib.parse.quote(clean_q)}"
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"[SystemControl] webbrowser open warning: {e}")
    return {
        "success": True,
        "open_tab": True,
        "voice_text": f"Searching Google for {clean_q} in a new tab, Sir.",
        "query": clean_q,
        "url": url
    }


def adjust_volume(action: str) -> dict:
    action = action.lower()
    try:
        if "up" in action or "increase" in action:
            for _ in range(5):
                pyautogui.press("volumeup")
            return {"voice_text": "Increasing volume, Sir."}
        elif "down" in action or "decrease" in action or "lower" in action:
            for _ in range(5):
                pyautogui.press("volumedown")
            return {"voice_text": "Lowering volume, Sir."}
        elif "mute" in action or "unmute" in action or "silence" in action:
            pyautogui.press("volumemute")
            return {"voice_text": "Toggling mute, Sir."}
    except Exception as e:
        print(f"[SystemControl] Volume error: {e}")

    return {"voice_text": "Volume command processed, Sir."}
