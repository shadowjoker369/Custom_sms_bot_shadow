# -*- coding: utf-8 -*-
import os
import requests
import urllib.parse
from flask import Flask, request

# -----------------------------
# Environment Variables
# -----------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Render এ এড করবেন
SMS_API_URL = os.environ.get("SMS_API_URL")  # যেমন: https://hl-hadi.mooo.com/ss/sms.php
SMS_API_KEY = os.environ.get("SMS_API_KEY")  # যেমন: 4eea4424

WEBHOOK_URL = f"https://custom-sms-bot-shadow.onrender.com/{BOT_TOKEN}"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

app = Flask(__name__)
user_state = {}  # User memory

# -----------------------------
# Send Telegram Message
# -----------------------------
def send_message(chat_id, text, buttons=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if buttons:
        payload["reply_markup"] = {"inline_keyboard": buttons}
    requests.post(API_URL + "sendMessage", json=payload)

# -----------------------------
# Send SMS via Custom API
# -----------------------------
def send_sms(number, message):
    try:
        number = urllib.parse.quote(number)
        message = urllib.parse.quote(message)
        url = f"{SMS_API_URL}?key={SMS_API_KEY}&number={number}&message={message}"
        res = requests.get(url, timeout=10)

        # Clean response
        try:
            data = res.json()
            if data.get("status") == "success":
                return "✅ SMS সফলভাবে পাঠানো হয়েছে"
            else:
                return f"❌ Error: {data.get('message', 'Unknown error')}"
        except:
            return res.text
    except Exception as e:
        return f"⚠ Exception: {e}"

# -----------------------------
# Flask Routes
# -----------------------------
@app.route("/")
def home():
    return "🤖 Custom SMS Bot Running!"

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()

    # Normal Message
    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")

        # /start → Bot info + Send Message button
        if text == "/start":
            msg_table = """
╔══════════════════════╗
║   🤖 Bot Info Table  ║
╠══════════════════════╣
║ 🔹 Name   : SHADOW JOKER
║ 🔹 Age    : 25
║ 🔹 Status : ✅ Active
╚══════════════════════╝

🤖 Bot Credit: *SHADOW JOKER*
            """
            buttons = [
                [{"text": "📩 Send Message", "callback_data": "start_send"}]
            ]
            send_message(chat_id, msg_table, buttons)

    # Callback Query (Button click)
    elif "callback_query" in update:
        query = update["callback_query"]
        chat_id = query["message"]["chat"]["id"]
        data = query["data"]

        if data == "start_send":
            send_message(chat_id, "📲 দয়া করে নাম্বার লিখুন:")
            user_state[chat_id] = {"step": "awaiting_number"}

    # Handle number or message input
    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")

        if chat_id in user_state:
            step = user_state[chat_id].get("step")

            if step == "awaiting_number":
                user_state[chat_id]["phone"] = text
                user_state[chat_id]["step"] = "awaiting_message"
                send_message(chat_id, "💬 এখন আপনার কাস্টম মেসেজ লিখুন:")

            elif step == "awaiting_message":
                phone = user_state[chat_id]["phone"]
                custom_message = text

                result = send_sms(phone, custom_message)
                send_message(
                    chat_id,
                    f"📞 নাম্বার: {phone}\n💬 মেসেজ: {custom_message}\n\nStatus: {result}"
                )

                user_state.pop(chat_id, None)

    return "ok"

# -----------------------------
# Webhook setup
# -----------------------------
def set_webhook():
    res = requests.get(API_URL + "setWebhook", params={"url": WEBHOOK_URL})
    print("Webhook setup response:", res.json())

# -----------------------------
if __name__ == "__main__":
    set_webhook()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
