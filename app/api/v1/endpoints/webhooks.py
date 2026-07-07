from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.core.config import settings
from app.services import user_service
from app.services.telegram import edit_telegram_message

router = APIRouter()

@router.post("/telegram/{secret}")
async def telegram_webhook(secret: str, request: Request, db: Session = Depends(get_db)):
    if not settings.TELEGRAM_WEBHOOK_SECRET or secret != settings.TELEGRAM_WEBHOOK_SECRET:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid webhook secret")
    
    update = await request.json()
    
    if "callback_query" not in update:
        return {"status": "ignored"}
        
    callback_query = update["callback_query"]
    message = callback_query.get("message")
    data = callback_query.get("data")
    
    if not message or not data:
        return {"status": "ignored"}
        
    chat_id = message.get("chat", {}).get("id")
    
    if str(chat_id) != str(settings.TELEGRAM_ADMIN_CHAT_ID):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized chat ID")
        
    message_id = message.get("message_id")
    
    if data.startswith("approve_user:"):
        user_id_str = data.split(":")[1]
        try:
            user_id = int(user_id_str)
            user = user_service.get_user_by_id(db, user_id)
            if user:
                user_service.approve_user(db, user)
                await edit_telegram_message(message_id, chat_id, f"✅ Usuário {user.name} aprovado com sucesso!")
            else:
                await edit_telegram_message(message_id, chat_id, f"⚠️ Usuário {user_id} não encontrado.")
        except ValueError:
            pass
            
    elif data.startswith("reject_user:"):
        user_id_str = data.split(":")[1]
        try:
            user_id = int(user_id_str)
            user = user_service.get_user_by_id(db, user_id)
            if user:
                user_service.reject_user(db, user)
                await edit_telegram_message(message_id, chat_id, f"❌ Usuário {user.name} rejeitado/suspenso.")
            else:
                await edit_telegram_message(message_id, chat_id, f"⚠️ Usuário {user_id} não encontrado.")
        except ValueError:
            pass
            
    return {"status": "ok"}
