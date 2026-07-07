import httpx
import logging
from app.core.config import settings
from app.models.user import User

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
            data = response.json()
            return data.get("result", {}).get("message_id")
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return None

async def answer_telegram_callback_query(callback_query_id: str, text: str, show_alert: bool = True):
    """
    Answers a callback query, showing a popup alert to the user.
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        return

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/answerCallbackQuery"
    payload = {
        "callback_query_id": callback_query_id,
        "text": text,
        "show_alert": show_alert
    }
    
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload, timeout=10.0)
    except Exception as e:
        logger.error(f"Failed to answer Telegram callback query: {e}")

async def edit_telegram_message(message_id: int, chat_id: int, text: str):
    """
    Edits an existing Telegram message.
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        return

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/editMessageText"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "Markdown",
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            response.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to edit Telegram message: {e}")

async def notify_new_user_pending(user_id: int):
    """
    Helper function to be run as a background task.
    Formats the notification and sends it asynchronously.
    """
    from sqlalchemy.exc import OperationalError
    from app.db.database import SessionLocal
    
    try:
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return
                
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
    
            message_id = await send_telegram_message(text, reply_markup=reply_markup)
            if message_id:
                user.telegram_message_id = message_id
                db.commit()
        finally:
            db.close()
    except OperationalError:
        logger.warning("Could not connect to database in background task (likely in test environment).")
    except Exception as e:
        logger.error(f"Error in background task: {e}")
