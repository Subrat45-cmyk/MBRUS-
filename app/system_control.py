"""
MBRUS System Control Engine
Automates Windows applications, priority websites, volume, browser shortcuts, media playback, and hardware diagnostics.
"""

import os
import json
import subprocess
import webbrowser
import urllib.parse
import datetime
from pathlib import Path
import psutil
import pyautogui

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "priority_sites.json"

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

    priority_sites = load_priority_sites()
    for key, site in priority_sites.items():
        if key in clean_target or clean_target in key or site["name"].lower() in clean_target:
            webbrowser.open(site["url"])
            return {
                "success": True,
                "voice_text": f"Opening your priority site {site['name']} in your web browser now, Sir.",
                "action": f"Navigated to {site['url']}",
                "site": site
            }

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
        if key in clean_target:
            try:
                subprocess.Popen(binary, shell=True)
                return {
                    "success": True,
                    "voice_text": f"Launching {key.title()} on your system, Sir.",
                    "action": f"Executed {binary}"
                }
            except Exception as e:
                print(f"[SystemControl] App error: {e}")

    if "." in clean_target and " " not in clean_target:
        url = clean_target if clean_target.startswith("http") else f"https://{clean_target}"
        webbrowser.open(url)
        return {
            "success": True,
            "voice_text": f"Opening {clean_target} in your browser, Sir.",
            "action": f"Navigated to {url}"
        }

    search_url = f"https://www.google.com/search?q={urllib.parse.quote(clean_target)}"
    webbrowser.open(search_url)
    return {
        "success": True,
        "voice_text": f"Opening web search for {clean_target} in your browser, Sir.",
        "action": f"Navigated to {search_url}"
    }


def play_youtube(query: str) -> dict:
    clean_q = query.replace("play", "").replace("on youtube", "").replace("youtube", "").strip()
    if not clean_q:
        webbrowser.open("https://www.youtube.com")
        return {"voice_text": "Opening YouTube for you, Sir."}

    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(clean_q)}"
    webbrowser.open(url)
    return {
        "voice_text": f"Playing {clean_q} on YouTube right now, Sir.",
        "query": clean_q,
        "url": url
    }


def search_google(query: str) -> dict:
    clean_q = query.replace("search for", "").replace("search", "").replace("google", "").strip()
    url = f"https://www.google.com/search?q={urllib.parse.quote(clean_q)}"
    webbrowser.open(url)
    return {
        "voice_text": f"Searching Google for {clean_q}, Sir.",
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
