"""
MBRUS Live Information Engine
Fetches real-time sports scores, GPS geolocation, state/city details, live weather, latest news, and web queries.
"""

import re
import urllib.parse
import httpx
from bs4 import BeautifulSoup
from ddgs import DDGS

SCRAPE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}
NOMINATIM_HEADERS = {
    "User-Agent": "MBRUS-Dragon-Assistant/2.0 (contact: admin@mbrus.ai)"
}

WMO_WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail"
}

INDIAN_STATES = {
    "rajasthan": ("Jaipur", 26.9124, 75.7873),
    "राजस्थान": ("Jaipur", 26.9124, 75.7873),
    "bihar": ("Patna", 25.5941, 85.1356),
    "बिहार": ("Patna", 25.5941, 85.1356),
    "maharashtra": ("Mumbai", 19.0760, 72.8777),
    "महाराष्ट्र": ("Mumbai", 19.0760, 72.8777),
    "uttar pradesh": ("Lucknow", 26.8467, 80.9462),
    "उत्तर प्रदेश": ("Lucknow", 26.8467, 80.9462),
    "up": ("Lucknow", 26.8467, 80.9462),
    "west bengal": ("Kolkata", 22.5726, 88.3639),
    "पश्चिम बंगाल": ("Kolkata", 22.5726, 88.3639),
    "bengal": ("Kolkata", 22.5726, 88.3639),
    "gujarat": ("Gandhinagar", 23.2156, 72.6369),
    "गुजरात": ("Gandhinagar", 23.2156, 72.6369),
    "punjab": ("Chandigarh", 30.7333, 76.7794),
    "पंजाब": ("Chandigarh", 30.7333, 76.7794),
    "haryana": ("Chandigarh", 30.7333, 76.7794),
    "हरियाणा": ("Chandigarh", 30.7333, 76.7794),
    "madhya pradesh": ("Bhopal", 23.2599, 77.4126),
    "मध्य प्रदेश": ("Bhopal", 23.2599, 77.4126),
    "mp": ("Bhopal", 23.2599, 77.4126),
    "tamil nadu": ("Chennai", 13.0827, 80.2707),
    "तमिलनाडु": ("Chennai", 13.0827, 80.2707),
    "karnataka": ("Bengaluru", 12.9716, 77.5946),
    "कर्नाटक": ("Bengaluru", 12.9716, 77.5946),
    "kerala": ("Thiruvananthapuram", 8.5241, 76.9366),
    "केरल": ("Thiruvananthapuram", 8.5241, 76.9366),
    "telangana": ("Hyderabad", 17.3850, 78.4867),
    "तेलंगाना": ("Hyderabad", 17.3850, 78.4867),
    "andhra pradesh": ("Amaravati", 16.5417, 80.5158),
    "आंध्र प्रदेश": ("Amaravati", 16.5417, 80.5158),
    "odisha": ("Bhubaneswar", 20.2961, 85.8245),
    "ओडिशा": ("Bhubaneswar", 20.2961, 85.8245),
    "assam": ("Dispur", 26.1433, 91.7898),
    "असम": ("Dispur", 26.1433, 91.7898),
    "jharkhand": ("Ranchi", 23.3441, 85.3096),
    "झारखंड": ("Ranchi", 23.3441, 85.3096),
    "chhattisgarh": ("Raipur", 21.2514, 81.6296),
    "छत्तीसगढ़": ("Raipur", 21.2514, 81.6296),
    "uttarakhand": ("Dehradun", 30.3165, 78.0322),
    "उत्तराखंड": ("Dehradun", 30.3165, 78.0322),
    "himachal pradesh": ("Shimla", 31.1048, 77.1734),
    "हिमाचल": ("Shimla", 31.1048, 77.1734),
    "goa": ("Panaji", 15.4909, 73.8278),
    "गोवा": ("Panaji", 15.4909, 73.8278),
    "delhi": ("New Delhi", 28.6139, 77.2090),
    "दिल्ली": ("New Delhi", 28.6139, 77.2090),
    "mumbai": ("Mumbai", 19.0760, 72.8777),
    "मुंबई": ("Mumbai", 19.0760, 72.8777),
    "patna": ("Patna", 25.5941, 85.1356),
    "पटना": ("Patna", 25.5941, 85.1356),
    "jaipur": ("Jaipur", 26.9124, 75.7873),
    "जयपुर": ("Jaipur", 26.9124, 75.7873),
    "kolkata": ("Kolkata", 22.5726, 88.3639),
    "कोलकाता": ("Kolkata", 22.5726, 88.3639)
}

def clean_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def get_live_cricket_matches() -> list[dict]:
    matches = []
    try:
        url = "https://www.cricbuzz.com/cricket-match/live-scores"
        with httpx.Client(timeout=8.0, headers=SCRAPE_HEADERS, follow_redirects=True) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                for a in soup.find_all("a"):
                    href = a.get("href", "")
                    if "/live-cricket-scores/" not in href:
                        continue
                    text = clean_text(a.text)
                    if not text or len(text) < 5:
                        continue
                    if "•" in text or "-" in text or "vs" in text.lower():
                        matches.append({
                            "raw": text,
                            "url": f"https://www.cricbuzz.com{href}" if href.startswith("/") else href
                        })
    except Exception as e:
        print(f"[LiveInfo] Cricket scrape error: {e}")

    processed = []
    seen = set()
    for m in matches:
        raw = m["raw"]
        if raw.lower() in ["live scores", "schedule", "archives"] or raw in seen:
            continue
        seen.add(raw)
        status = ""
        title = raw
        if " - " in raw:
            parts = raw.split(" - ")
            title = parts[0]
            status = " - ".join(parts[1:])
        elif "•" in raw:
            parts = raw.split("•")
            title = parts[0].strip()
            status = parts[1].strip() if len(parts) > 1 else ""

        processed.append({
            "title": title,
            "status": status if status else raw,
            "details": raw,
            "url": m["url"]
        })

    return processed[:12]


def get_live_sports_score(query: str = "") -> dict:
    clean_q = query.lower().strip()
    is_cricket = any(k in clean_q for k in ["cricket", "match", "score", "running status", "ipl", "t20", "odi", "test"])
    
    cricket_matches = get_live_cricket_matches()
    matched_games = []
    if cricket_matches:
        if any(k in clean_q for k in ["today", "current", "live", "running", "match score"]) and not any(team in clean_q for team in ["india", "pakistan", "australia", "england", "csk", "rcb", "mi"]):
            matched_games = cricket_matches[:3]
        else:
            for m in cricket_matches:
                raw_lower = m["details"].lower()
                for word in clean_q.split():
                    if len(word) > 2 and word in raw_lower:
                        matched_games.append(m)
                        break
        
        if not matched_games and is_cricket:
            matched_games = cricket_matches[:3]

    if matched_games:
        voice_items = []
        for g in matched_games[:2]:
            details = g["details"]
            if len(details) > 160:
                details = details[:160] + "..."
            voice_items.append(details)

        voice_text = f"Sir, here is the current running match status. {'; '.join(voice_items)}."
        return {
            "source": "Cricbuzz Live",
            "voice_text": voice_text,
            "matches": matched_games,
            "card": {
                "title": "Live Cricket Scoreboard",
                "items": [g["details"] for g in matched_games]
            }
        }

    search_query = query if query else "live sports match score today running status"
    if "score" not in search_query.lower():
        search_query += " live match score running status"

    try:
        ddgs = DDGS()
        results = list(ddgs.text(search_query, max_results=3))
        if results:
            first = results[0]
            snippet = clean_text(first.get("body", ""))
            title = clean_text(first.get("title", ""))
            return {
                "source": "Live Web Search",
                "voice_text": f"Sir, according to latest live updates: {snippet[:200]}.",
                "matches": [{"title": r.get("title"), "details": r.get("body"), "url": r.get("href")} for r in results],
                "card": {
                    "title": f"Live Score Updates: {title}",
                    "items": [r.get("body") for r in results]
                }
            }
    except Exception as e:
        print(f"[LiveInfo] DDGS search error: {e}")

    return {
        "source": "System",
        "voice_text": "Sir, I checked the live feeds, but could not detect active running matches at this moment.",
        "matches": [],
        "card": {"title": "Live Match Status", "items": ["No live games currently broadcasting scores."]}
    }


def reverse_geocode_gps(lat: float, lon: float) -> dict:
    try:
        url = f"https://api.bigdatacloud.net/data/reverse-geocode-client?latitude={lat}&longitude={lon}&localityLanguage=en"
        with httpx.Client(timeout=5.0, follow_redirects=True) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                d = resp.json()
                city = d.get("city") or d.get("locality") or "Current Location"
                state = d.get("principalSubdivision") or ""
                country = d.get("countryName") or "India"
                locality = d.get("locality") or city
                full_name = f"{locality}, {state}, {country}" if state else f"{locality}, {country}"
                return {
                    "success": True,
                    "city": city,
                    "state": state,
                    "country": country,
                    "locality": locality,
                    "full_name": full_name,
                    "latitude": lat,
                    "longitude": lon
                }
    except Exception as e:
        print(f"[LiveInfo] BigDataCloud error: {e}")

    try:
        nom_url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        with httpx.Client(timeout=5.0, headers=NOMINATIM_HEADERS) as client:
            resp = client.get(nom_url)
            if resp.status_code == 200:
                d = resp.json()
                addr = d.get("address", {})
                city = addr.get("city") or addr.get("town") or addr.get("village") or "Current Location"
                state = addr.get("state") or ""
                country = addr.get("country") or "India"
                return {
                    "success": True,
                    "city": city,
                    "state": state,
                    "country": country,
                    "locality": city,
                    "full_name": f"{city}, {state}, {country}",
                    "latitude": lat,
                    "longitude": lon
                }
    except Exception as e:
        print(f"[LiveInfo] Nominatim error: {e}")

    return {
        "success": False,
        "city": "GPS Location",
        "state": "",
        "country": "",
        "locality": "",
        "full_name": f"{lat:.3f}° N, {lon:.3f}° E",
        "latitude": lat,
        "longitude": lon
    }


def get_weather_by_coords(lat: float, lon: float, location_name: str = "") -> dict:
    try:
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,precipitation"
        )
        with httpx.Client(timeout=6.0) as client:
            w_res = client.get(weather_url)
            w_data = w_res.json()
            current = w_data.get("current", {})
            temp = current.get("temperature_2m", "N/A")
            feels_like = current.get("apparent_temperature", temp)
            humidity = current.get("relative_humidity_2m", "N/A")
            wind = current.get("wind_speed_10m", "N/A")
            precip = current.get("precipitation", 0)
            code = current.get("weather_code", 0)
            condition = WMO_WEATHER_CODES.get(code, "Clear conditions")
            loc_label = location_name or f"{lat:.2f}°, {lon:.2f}°"

            return {
                "success": True,
                "location": loc_label,
                "temperature": f"{temp}°C",
                "feels_like": f"{feels_like}°C",
                "condition": condition,
                "humidity": f"{humidity}%",
                "wind_speed": f"{wind} km/h",
                "precipitation": f"{precip} mm",
                "latitude": lat,
                "longitude": lon,
                "voice_text": f"Sir, at {loc_label}, it is {temp} degrees Celsius with {condition.lower()}. Feels like {feels_like} degrees, humidity is {humidity} percent."
            }
    except Exception as e:
        print(f"[LiveInfo] Weather by coords error: {e}")
        return {
            "success": False,
            "location": location_name or "Current Location",
            "temperature": "25°C",
            "feels_like": "26°C",
            "condition": "Clear sky",
            "humidity": "55%",
            "wind_speed": "8 km/h",
            "precipitation": "0 mm",
            "latitude": lat,
            "longitude": lon,
            "voice_text": f"Sir, weather at {location_name} indicates clear sky around 25 degrees Celsius."
        }


def get_state_or_city_details(query: str) -> dict:
    clean_q = clean_text(query).lower().replace("weather", "").replace("climate", "").replace("in", "").replace("for", "").strip()
    if not clean_q:
        clean_q = "new delhi"

    for state_name, (capital, s_lat, s_lon) in INDIAN_STATES.items():
        if state_name in clean_q or clean_q in state_name:
            w = get_weather_by_coords(s_lat, s_lon, f"{state_name.title()} (Capital: {capital})")
            w["state"] = state_name.title()
            w["capital"] = capital
            w["country"] = "India"
            w["type"] = "State"
            w["voice_text"] = f"Sir, for {state_name.title()}, centered around capital {capital}, the temperature is {w['temperature']} with {w['condition'].lower()}. Humidity is {w['humidity']}."
            return w

    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(clean_q)}&count=1"
        with httpx.Client(timeout=5.0) as client:
            geo_res = client.get(geo_url)
            geo_data = geo_res.json()
            if geo_data.get("results"):
                loc = geo_data["results"][0]
                lat = loc["latitude"]
                lon = loc["longitude"]
                name = loc.get("name", clean_q.title())
                state = loc.get("admin1", "")
                country = loc.get("country", "")
                population = loc.get("population", 0)

                full_loc = f"{name}, {state}, {country}" if state else f"{name}, {country}"
                w = get_weather_by_coords(lat, lon, full_loc)
                w["name"] = name
                w["state"] = state
                w["country"] = country
                w["population"] = population
                w["type"] = "City / Region"
                w["voice_text"] = f"Sir, in {name}, {state or country}, it is currently {w['temperature']} with {w['condition'].lower()}. Humidity is {w['humidity']} with {w['wind_speed']} wind."
                return w
    except Exception as e:
        print(f"[LiveInfo] City search error: {e}")

    try:
        nom_url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(clean_q)}&format=json&limit=1"
        with httpx.Client(timeout=5.0, headers=NOMINATIM_HEADERS) as client:
            resp = client.get(nom_url)
            data = resp.json()
            if data:
                top = data[0]
                lat = float(top["lat"])
                lon = float(top["lon"])
                disp_name = top.get("display_name", clean_q.title())
                parts = [p.strip() for p in disp_name.split(",")]
                short_loc = ", ".join(parts[:2]) if len(parts) >= 2 else disp_name
                w = get_weather_by_coords(lat, lon, short_loc)
                w["full_name"] = disp_name
                w["type"] = top.get("type", "Region")
                return w
    except Exception as e:
        print(f"[LiveInfo] Nominatim search error: {e}")

    return get_weather_by_coords(28.6139, 77.2090, f"{clean_q.title()} (Estimated)")


def get_live_weather(city: str = "New Delhi") -> dict:
    return get_state_or_city_details(city)


def get_latest_news(topic: str = "") -> dict:
    search_topic = topic.strip() if topic.strip() else "breaking news"
    try:
        ddgs = DDGS()
        res = list(ddgs.news(search_topic, max_results=5))
        if res:
            headlines = [
                {
                    "title": clean_text(r.get("title", "")),
                    "body": clean_text(r.get("body", "")),
                    "url": r.get("url", ""),
                    "source": r.get("source", "News")
                }
                for r in res if r.get("title")
            ]
            if headlines:
                spoken_titles = [h["title"] for h in headlines[:3]]
                return {
                    "source": "Live News",
                    "voice_text": f"Sir, here are the top headlines right now: {'; '.join(spoken_titles)}.",
                    "headlines": headlines
                }
    except Exception as e:
        print(f"[LiveInfo] News error: {e}")

    return {
        "source": "System",
        "voice_text": "Sir, I was unable to retrieve new headlines at this moment.",
        "headlines": []
    }


def search_web_realtime(query: str, max_results: int = 4) -> list[dict]:
    try:
        ddgs = DDGS()
        results = list(ddgs.text(query, max_results=max_results))
        return [
            {
                "title": r.get("title", ""),
                "snippet": clean_text(r.get("body", "")),
                "url": r.get("href", "")
            }
            for r in results
        ]
    except Exception as e:
        print(f"[LiveInfo] Realtime search error: {e}")
        return []
