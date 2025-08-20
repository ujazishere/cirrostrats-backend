import requests
from decouple import config


class Tele_bot:
    def __init__(self):
        BOT_TOKEN = config("TELE_BOT_TOKEN")      # Telegram Bot Token from .env file
        self.url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        self.CHAT_ID = "8483981154"

    def send_message(self, MESSAGE):
        payload = {"chat_id": self.CHAT_ID, "text": MESSAGE}
        r = requests.post(self.url, data=payload)
        print(r.json())
