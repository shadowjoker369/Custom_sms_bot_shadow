import os
import requests
from flask import Flask, request

# -----------------------------
# Environment Variables
# -----------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Render   
SMS_API_URL = os.environ.get("SMS_API_URL")  #  URL 

WEBHOOK_URL = f"https://your-app-name.onrender.com/{BOT_TOKEN}"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

app = Flask(__name__)
user_state = {}

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
        # Example: https://smsapi.com/send?to=NUMBER&msg=MESSAGE
        url = f"{SMS_API_URL}?to={number}&msg={message}"
        res = requests.get(url, timeout=5)
        return res.text
    except Exception as e:
        return str(e)

# -----------------------------
# Flask Routes
# -----------------------------
@app.route("/")
def home():
    return " Custom SMS Bot Running!"

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()

    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")

        # /start command
        if text == "/start":
            msg_table = """
ษออออออออออออออออออออออป
บ    Bot Info Table  บ
ฬออออออออออออออออออออออน
บ  Name   : SHADOW JOKER
บ  Age    : 25
บ  Status :  Active
ศออออออออออออออออออออออผ

 Bot Credit: *SHADOW JOKER*
            """
            send_message(chat_id, msg_table)

        # /sendmessage flow
        elif text == "/sendmessage":
            send_message(chat_id, "    :")
            user_state[chat_id] = {"step": "awaiting_number"}

        # number input
        elif chat_id in user_state and user_state[chat_id].get("step") == "awaiting_number":
            user_state[chat_id]["phone"] = text
            user_state[chat_id]["step"] = "awaiting_message"
            send_message(chat_id, "     :")

        # message input
        elif chat_id in user_state and user_state[chat_id].get("step") == "awaiting_message":
            user_state[chat_id]["message"] = text
            user_state[chat_id]["step"] = "confirm"

            phone = user_state[chat_id]["phone"]
            custom_message = user_state[chat_id]["message"]

            buttons = [
                [{"text": " Send SMS", "callback_data": "send"}],
                [{"text": " Cancel", "callback_data": "cancel"}]
            ]

            send_message(
                chat_id,
                f" : `{phone}`\n : {custom_message}\n\n  ?",
                buttons
            )

    elif "callback_query" in update:
        query = update["callback_query"]
        chat_id = query["message"]["chat"]["id"]
        data = query["data"]

        if data == "send":
            phone = user_state[chat_id]["phone"]
            custom_message = user_state[chat_id]["message"]

            result = send_sms(phone, custom_message)
            send_message(chat_id, f" SMS  !\n\n {phone}\n {custom_message}\n\nAPI Response: `{result}`")

            user_state.pop(chat_id, None)

        elif data == "cancel":
            send_message(chat_id, "   ")
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