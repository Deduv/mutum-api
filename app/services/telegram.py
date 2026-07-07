import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

async def send_telegram_message(text: str, reply_markup: dict = None):
    """
    Sends a message to the configured Telegram Admin Chat ID.
    """
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_ADMIN_CHAT_ID:
        logger.warning("Telegram credentials not configured. Skipping notification.")
        return

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": settings.TELEGRAM_ADMIN_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }
    
    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            response.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")

async def notify_new_user_pending(user):
    """
    Helper function to be run as a background task.
    Formats the notification and sends it asynchronously.
    """
    text = (
        f"🔔 *MUTUM — NEW USER PENDING*\n"
        f"👤 *Name:* {user.name}\n"
        f"📧 *Email:* {user.email}\n"
        f"🆔 *ID:* {user.id}"
    )
    
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "✅ Approve", "callback_data": f"approve_user:{user.id}"},
                {"text": "❌ Reject", "callback_data": f"reject_user:{user.id}"}
            ]
        ]
    }

    await send_telegram_message(text, reply_markup=reply_markup)
