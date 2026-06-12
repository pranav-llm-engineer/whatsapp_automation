from fastapi import APIRouter, Request, Depends, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse
from backend.config import WHATSAPP_VERIFY_TOKEN, SARVAM_API
from sqlalchemy.orm import Session as DBSession
from backend.db.database import get_db
from backend.db.models import User, UserProfile, Session as DBSessionModel
from backend.routers.chat import chat_endpoint, ChatRequest
from backend.services.whatsapp_service import send_whatsapp_message, send_whatsapp_image, download_whatsapp_media
import uuid
import httpx
import re
import os

router = APIRouter(prefix="/webhook", tags=["whatsapp"])

async def transcribe_audio_bytes(audio_bytes: bytes) -> str:
    if not SARVAM_API or not audio_bytes:
        return ""
    try:
        files = {"file": ("audio.ogg", audio_bytes, "audio/ogg")}
        data = {"model": "saarika:v2.5"}
        headers = {"api-subscription-key": SARVAM_API}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.sarvam.ai/speech-to-text",
                files=files,
                data=data,
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json().get("transcript", "")
    except Exception as e:
        print(f"Transcription error: {e}")
        return ""

@router.get("/")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
            return PlainTextResponse(content=challenge, status_code=200)
        else:
            raise HTTPException(status_code=403, detail="Verification token mismatch")
    raise HTTPException(status_code=400, detail="Missing parameters")

async def process_whatsapp_message(wa_id: str, message_text: str, db: DBSession):
    user = db.query(User).filter(User.phone == wa_id).first()
    if not user:
        user = User(phone=wa_id, password_hash="whatsapp_auth")
        db.add(user)
        db.commit()
        db.refresh(user)
        
        profile = UserProfile(user_id=user.id)
        db.add(profile)
        db.commit()

    session = db.query(DBSessionModel).filter(DBSessionModel.user_id == user.id).first()
    if not session:
        session = DBSessionModel(id=str(uuid.uuid4()), user_id=user.id)
        db.add(session)
        db.commit()

    try:
        chat_req = ChatRequest(session_id=session.id, message=message_text)
        response_dict = await chat_endpoint(chat_req, db)
        reply = response_dict.get("reply", "Sorry, I am facing technical difficulties.")
        
        # Parse image tags: [SEND_IMAGE: filename.png]
        image_tags = re.findall(r'\[SEND_IMAGE:\s*([^\]]+)\]', reply)
        clean_reply = re.sub(r'\[SEND_IMAGE:\s*[^\]]+\]', '', reply).strip()
        
        # Send text reply
        if clean_reply:
            await send_whatsapp_message(wa_id, clean_reply)
            
        # Send images (Requires PUBLIC_URL on Render)
        public_url = os.getenv("PUBLIC_URL", "https://your-render-app.onrender.com")
        for img in image_tags:
            img_url = f"{public_url}/images/{img.strip()}"
            await send_whatsapp_image(wa_id, img_url)
            
    except Exception as e:
        print(f"Error processing WhatsApp message: {e}")

async def process_whatsapp_audio(wa_id: str, media_id: str, db: DBSession):
    audio_bytes = await download_whatsapp_media(media_id)
    if audio_bytes:
        transcript = await transcribe_audio_bytes(audio_bytes)
        if transcript:
            await process_whatsapp_message(wa_id, transcript, db)
        else:
            await send_whatsapp_message(wa_id, "I couldn't clearly hear your voice note. Could you type it out?")
    else:
        await send_whatsapp_message(wa_id, "Sorry, I had trouble downloading your voice note.")

@router.post("/")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks, db: DBSession = Depends(get_db)):
    body = await request.json()
    
    if body.get("object") == "whatsapp_business_account":
        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                if "messages" in value:
                    for message in value["messages"]:
                        wa_id = message.get("from")
                        if message.get("type") == "text":
                            message_text = message["text"]["body"]
                            background_tasks.add_task(process_whatsapp_message, wa_id, message_text, db)
                        elif message.get("type") == "audio":
                            media_id = message["audio"]["id"]
                            background_tasks.add_task(process_whatsapp_audio, wa_id, media_id, db)
        return {"status": "ok"}
    raise HTTPException(status_code=404, detail="Not Found")
