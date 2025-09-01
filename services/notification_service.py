from utils.tele import Tele_bot


def send_telegram_notification_service(message):
    
    tb = Tele_bot()

    send_to = [tb.ISMAIL_CHAT_ID, tb.UJ_CHAT_ID]
    tb.send_message(chat_id=send_to,
                    MESSAGE=message,token=tb.TELE_MAIN_BOT_TOKEN)