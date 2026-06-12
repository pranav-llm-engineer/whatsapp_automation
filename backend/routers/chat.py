from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
import httpx
from backend.config import SARVAM_API
from sqlalchemy.orm import Session as DBSession
from backend.db.database import get_db
from backend.db.models import Session, UserProfile
from backend.services.rag_service import retrieve_context
from backend.services.llm_service import build_system_prompt, call_llm, check_onboarding_intent, check_cancel_intent, extract_missing_fields, infer_urgency, detect_profile_updates
from backend.services.session_service import get_conversation_history, add_message
from backend.services.onboarding_service import update_profile_field
from backend.services.crm_service import upsert_lead
import asyncio

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    session_id: str
    message: str

@router.post("/")
async def chat_endpoint(request: ChatRequest, db: DBSession = Depends(get_db)):
    session = db.query(Session).filter(Session.id == request.session_id).first()
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    profile = db.query(UserProfile).filter(UserProfile.user_id == session.user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    user_msg = request.message
    add_message(db, request.session_id, "user", user_msg)

    # If completely done, always general
    if profile.onboarding_complete:
        mode = "general"
    else:
        # If not active, check intent to start
        if not profile.onboarding_active:
            wants_to_onboard = await check_onboarding_intent(user_msg)
            if wants_to_onboard:
                profile.onboarding_active = True
                db.commit()
                mode = "onboarding"
            else:
                mode = "general"
        else:
            # It's active, but maybe they want to cancel?
            wants_to_cancel = await check_cancel_intent(user_msg)
            if wants_to_cancel:
                profile.onboarding_active = False
                db.commit()
                bot_reply = "Okay, I've paused the registration process. We can always resume later. What else can I help you with?"
                add_message(db, request.session_id, "assistant", bot_reply)
                return {"reply": bot_reply, "mode": "general", "onboarding_active": False}
            else:
                mode = "onboarding"

    if mode == "onboarding":
        missing_fields = []
        if not profile.spaceType:
            missing_fields.append("spaceType")
        if not profile.seatRangeMin:
            missing_fields.append("seatRange")
        if not profile.location:
            missing_fields.append("location")
        if not profile.full_name:
            missing_fields.append("full_name")
                
        if missing_fields:
            extracted = await extract_missing_fields(user_msg, missing_fields)
            if extracted:
                for k, v in extracted.items():
                    if k in missing_fields and v:
                        update_profile_field(db, profile, k, v)
                        missing_fields.remove(k)
                        
        if not missing_fields and not profile.onboarding_complete:
            profile.onboarding_complete = True
            profile.onboarding_step = "Payment"
            db.commit()
            if not profile.urgency:
                full_history = get_conversation_history(db, request.session_id, limit=30)
                profile.urgency = await infer_urgency(full_history)
                db.commit()
            asyncio.create_task(upsert_lead(profile, session.user.phone))

        history = get_conversation_history(db, request.session_id, limit=6)
        context = retrieve_context(user_msg)
        
        sys_prompt = build_system_prompt(context, {"missing_fields": missing_fields}, mode)
        bot_reply = await call_llm(history, sys_prompt)
        add_message(db, request.session_id, "assistant", bot_reply)
        return {"reply": bot_reply, "mode": mode, "onboarding_complete": profile.onboarding_complete, "onboarding_active": True, "context": context}

    else:
        # General RAG Chat
        context = retrieve_context(user_msg)
        sys_prompt = build_system_prompt(context, {}, "general")
        history = get_conversation_history(db, request.session_id, limit=10)
        bot_reply = await call_llm(history, sys_prompt)
        
        # Detect if we need to sync updates to CRM
        if profile.onboarding_complete:
            updates = await detect_profile_updates(user_msg)
            if updates:
                updated = False
                for k, v in updates.items():
                    if hasattr(profile, k):
                        update_profile_field(db, profile, k, v)
                        updated = True
                if updated:
                    asyncio.create_task(upsert_lead(profile, session.user.phone))
        
        add_message(db, request.session_id, "assistant", bot_reply)
        return {"reply": bot_reply, "mode": "general", "onboarding_active": False, "context": context}

@router.get("/history")
def get_history(session_id: str, db: DBSession = Depends(get_db)):
    return get_conversation_history(db, session_id, limit=50)

@router.post("/transcribe/")
async def transcribe_audio(file: UploadFile = File(...)):
    if not SARVAM_API:
        raise HTTPException(status_code=500, detail="SARVAM_API key not configured")
        
    try:
        audio_bytes = await file.read()
        files = {"file": (file.filename, audio_bytes, file.content_type)}
        data = {
            "model": "saarika:v2.5"
        }
        headers = {
            "api-subscription-key": SARVAM_API
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.sarvam.ai/speech-to-text",
                files=files,
                data=data,
                headers=headers,
                timeout=30.0
            )
            
            response.raise_for_status()
            result = response.json()
            return {"transcript": result.get("transcript", "")}
            
    except Exception as e:
        print(f"Transcription error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to transcribe audio")
