import os
import requests
import openai
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

def get_today_avg_temp_and_rain(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric&lang=ja"
    res = requests.get(url).json()
    from datetime import datetime, timedelta
    now = datetime.utcnow() + timedelta(hours=9)
    today_str = now.strftime("%Y-%m-%d")

    temps = []
    pops = []

    for entry in res["list"]:
        dt_txt = entry["dt_txt"]
        if today_str in dt_txt:
            hour = int(dt_txt.split()[1].split(":")[0])
            if 9 <= hour <= 18:
                temps.append(entry["main"]["temp"])
                pops.append(entry.get("pop", 0))

    if temps:
        avg_temp = sum(temps) / len(temps)
        max_pop = max(pops) if pops else 0
        return round(avg_temp, 1), int(max_pop * 100)
    else:
        return None, None

def get_weather_description(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric&lang=ja"
    res = requests.get(url).json()
    return res["weather"][0]["description"]

def generate_suggestion(temp, rain_prob, weather):
    openai.api_key = OPENAI_API_KEY
    prompt = f"""
1歳と3歳の子どもに、今日の天気「{weather}」、平均気温「{temp}℃」、降水確率「{rain_prob}%」に合った服装を親に提案してください。
やさしく親しみやすい日本語で、1〜2文のLINEメッセージとして書いてください。
"""
    res = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content.strip()

def reply_to_line(reply_token, text):
    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": text}]
    }
    requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=body)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    events = data.get("events", [])
    for event in events:
        msg = event.get("message", {})
        reply_token = event.get("replyToken")
        if msg.get("type") == "location":
            lat = msg["latitude"]
            lon = msg["longitude"]
            temp, rain_prob = get_today_avg_temp_and_rain(lat, lon)
            weather = get_weather_description(lat, lon)
            if temp is not None:
                suggestion = generate_suggestion(temp, rain_prob, weather)
                message = f"📍 現在地の天気：{weather}\n🌡 平均気温：{temp}℃\n☔ 降水確率：{rain_prob}%\n\n{suggestion}"
            else:
                message = "天気予報データが取得できませんでした。"
            reply_to_line(reply_token, message)
    return "ok"
