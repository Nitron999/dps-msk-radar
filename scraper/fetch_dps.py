import os
import re
import time
import urllib.parse
import urllib.request
import json
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

SUPABASE_URL = "https://mobpdvfwfwpxbxehlumm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1vYnBkdmZ3ZndweGJ4ZWhsdW1tIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTUzNTQ3OTksImV4cCI6MjExMDkzMDc5OX0.lakkyjDl2aA9pfu3f8_VX5oFfGlnGs3is5cOkrB9hjM"

CHANNELS = [
    "dtp777",
    "moscowmap",
    "msk1_news",
    "moscow_dps",
    "DtRoad",
    "transportmos",
    "moscowach",
    "mosoblast",
    "podmoskovye",
    "msk_live",
]

KEYWORDS = [
    "дпс", "гибдд", "гаи", "экипаж", "пост", "стоят", "тормозят",
    "оформляют", "рейд", "засада", "патруль", "проверка", "нюхачи",
    "перекрыт", "перекрыли", "дтп", "авария", "инспектор"
]

LANDMARKS = {
    "мкад": (55.7558, 37.6173),
    "ттк": (55.7558, 37.6173),
    "садовое": (55.7558, 37.6173),
    "ленинградк": (55.8549, 37.4765),
    "ленинградское": (55.8549, 37.4765),
    "ярославк": (55.8752, 37.7163),
    "ярославское": (55.8752, 37.7163),
    "дмитровк": (55.8911, 37.5453),
    "дмитровское": (55.8911, 37.5453),
    "алтуфьев": (55.8986, 37.5872),
    "щёлков": (55.8105, 37.8012),
    "щелков": (55.8105, 37.8012),
    "энтузиастов": (55.7647, 37.7758),
    "рязанск": (55.7214, 37.7797),
    "волгоградск": (55.7027, 37.7661),
    "каширск": (55.6311, 37.6975),
    "варшавск": (55.6119, 37.6061),
    "симферопольск": (55.5342, 37.5931),
    "калужск": (55.5822, 37.4725),
    "киевск": (55.6378, 37.4192),
    "минск": (55.6897, 37.3619),
    "можайск": (55.7175, 37.4053),
    "рублёв": (55.7492, 37.4114),
    "рублев": (55.7492, 37.4114),
    "новорижск": (55.7925, 37.3519),
    "волоколамск": (55.8294, 37.4286),
    "пятницк": (55.8647, 37.3592),
    "химки": (55.8887, 37.4304),
    "мытищи": (55.9105, 37.7363),
    "королёв": (55.9222, 37.8546),
    "королев": (55.9222, 37.8546),
    "балашиха": (55.7963, 37.9382),
    "люберцы": (55.6772, 37.8932),
    "подольск": (55.4312, 37.5447),
    "одинцово": (55.6789, 37.2640),
    "красногорск": (55.8311, 37.3302),
    "домодедово": (55.4372, 37.7676),
    "зеленоград": (55.9919, 37.2144),
    "щелково": (55.9202, 37.9915),
    "пушкино": (56.0104, 37.8472),
    "раменское": (55.5673, 38.2258),
    "жуковский": (55.5953, 38.1203),
    "серпухов": (54.9135, 37.4112),
    "коломна": (55.0938, 38.7683),
    "ногинск": (55.8545, 38.4418),
    "электросталь": (55.7896, 38.4467),
    "чехов": (55.1429, 37.4545),
    "наро-фоминск": (55.3881, 36.7336),
    "истра": (55.9144, 36.8598),
    "солнечногорск": (56.1851, 36.9765),
    "клин": (56.3317, 36.7287),
    "дмитров": (56.3439, 37.5203),
    "сергиев посад": (56.3153, 38.1359),
    "орехово-зуево": (55.8067, 38.9618),
    "центральн": (55.7558, 37.6173),
    "северн": (55.8384, 37.5258),
    "южн": (55.6228, 37.6781),
    "западн": (55.7280, 37.4435),
    "восточн": (55.7877, 37.7756),
}


def geocode_address(text):
    clean = re.sub(r"http\S+|@\w+|#\w+", "", text)
    clean = re.sub(r"[^\w\s\-,.]", " ", clean).strip()
    query = urllib.parse.quote(f"Москва и Московская область, {clean[:120]}")
    url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1&viewbox=35.1,56.9,40.2,54.2&bounded=1"
    req = urllib.request.Request(url, headers={"User-Agent": "DpsMskRadarBot/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data:
                lat = float(data[0]["lat"])
                lng = float(data[0]["lon"])
                if 54.2 <= lat <= 56.9 and 35.1 <= lng <= 40.2:
                    return lat, lng
    except Exception:
        pass

    lower = text.lower()
    for key, coords in LANDMARKS.items():
        if key in lower:
            return coords
    return None


def send_to_supabase(lat, lng, comment, source_id):
    url = f"{SUPABASE_URL}/rest/v1/patrol_marks?on_conflict=source_id"
    payload = json.dumps({
        "lat": lat,
        "lng": lng,
        "type": "dps",
        "comment": comment[:250],
        "source_id": source_id,
    }).encode("utf-8")

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=ignore-duplicates",
    }
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"УСПЕХ [{source_id}]: {comment[:70]}")
    except Exception as e:
        print(f"ОШИБКА ЗАПИСИ [{source_id}]: {e}")


def fetch_channel(channel):
    url = f"https://t.me/s/{channel}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"Канал @{channel} недоступен: {e}")
        return

    soup = BeautifulSoup(html, "html.parser")
    messages = soup.find_all("div", class_="tgme_widget_message")
    print(f"Канал @{channel}: найдено сообщений на странице = {len(messages)}")
    now = datetime.now(timezone.utc)

    for msg in messages[-20:]:
        post_id = msg.get("data-post")
        text_div = msg.find("div", class_="tgme_widget_message_text")
        time_tag = msg.find("time")

        if not post_id or not text_div or not time_tag:
            continue

        dt_str = time_tag.get("datetime")
        if dt_str:
            try:
                msg_dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                if (now - msg_dt) > timedelta(hours=24):
                    continue
            except Exception:
                pass

        text = text_div.get_text(" ", strip=True)
        lower_text = text.lower()

        if not any(kw in lower_text for kw in KEYWORDS):
            continue

        coords = geocode_address(text)
        if coords:
            send_to_supabase(coords[0], coords[1], f"[{channel}] {text}", post_id)
            time.sleep(1.1)


if __name__ == "__main__":
    for ch in CHANNELS:
        fetch_channel(ch)
