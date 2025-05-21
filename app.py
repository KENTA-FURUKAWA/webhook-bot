from flask import Flask, request
import json

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.json
    print("📩 受信:", json.dumps(body, indent=2, ensure_ascii=False))

    # ユーザーIDの取得（最初の1件だけ表示）
    events = body.get("events", [])
    for event in events:
        user_id = event.get("source", {}).get("userId")
        print("👤 ユーザーID:", user_id)

    return "OK", 200

@app.route("/", methods=["GET"])
def root():
    return "LINE Webhook Bot is running.", 200
