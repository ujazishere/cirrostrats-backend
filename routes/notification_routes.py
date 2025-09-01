from fastapi import APIRouter
from services.notification_service import send_telegram_notification_service
router = APIRouter()

@router.post("/sendTelegramNotification")
def send_telegram_notification(message):
    return send_telegram_notification_service(message)