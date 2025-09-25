import requests
from decouple import config

class Tele_bot:
    def __init__(self):

        """ 
            Telegram Bot API to send messages to a specific chat.
            The bot token is stored in the .env file.
            The chat ID is hardcoded for now, but can be changed - get it from the api. theyre unique to each chat/user
            f'https://api.telegram.org/bot{TELE_BOT_TOKEN}/getUpdates'
        
            """
        
        self.TELE_MAIN_BOT_TOKEN = config("TELE_MAIN_BOT_TOKEN")      # Telegram Bot Token from .env file
        self.TELE_EWR_TOKEN = config("TELE_EWR_TOKEN")      # Telegram Bot Token from .env file
        self.UJ_CHAT_ID = "8483981154"
        self.ISMAIL_CHAT_ID = "763268014"      # Group chat ID - get it from the api.

    def payload_prep(self, chat_id, MESSAGE):
        return {"chat_id": chat_id, "text": MESSAGE}
        
    def send_message(self, chat_id:list, MESSAGE,token):
        
        self.url = f"https://api.telegram.org/bot{token}/sendMessage"
        for each_user in chat_id:
            payload = self.payload_prep(each_user, MESSAGE)
            r = requests.post(self.url, data=payload)
            # print(r.json())
            # r here isthe result of the post request could use it as a log. or atleast condition for ok:false to log warning.
