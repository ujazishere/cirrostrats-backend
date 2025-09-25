from utils.tele import Tele_bot


def send_telegram_notification_service(message):
    # TODO VHP: Maybe move this function to the core or within the class utils.tele?
    # TODO LP: Setup continious loop to check for message on telegram for flight number request-
            # When received send back updates - NAS status, weather changes, pdc, gate changes etc.
            # This can serve as a proof concept.
    tb = Tele_bot()

    send_to = [tb.ISMAIL_CHAT_ID, tb.UJ_CHAT_ID]
    tb.send_message(chat_id=send_to,
                    MESSAGE=message,token=tb.TELE_MAIN_BOT_TOKEN)