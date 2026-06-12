import httpx
from backend.config import OPENROUTER_API_KEY, MODEL_ID
from typing import List, Dict
import json
from datetime import datetime, timezone, timedelta

FIELD_DESCRIPTIONS = {
    "full_name": "their full name",
    "spaceType": "the type of workspace they want (e.g., Day Pass, Private Cabin, Dedicated Desk)",
    "seatRange": "the NUMBER of people coming in or seats they need (e.g., 3 day passes for 3 employees, 5-10 people). Do NOT ask about seating areas like quiet zones.",
    "location": "which specific location they are from"
}

def build_system_prompt(context: str, profile_dict: dict, mode: str) -> str:
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(ist_tz)
    current_time_str = now.strftime("%I:%M %p, %A, %B %d, %Y")
    
    base = f"""You are Khushi, the friendly customer assistant for Hoblix Coworking Space in Najafgarh.
You help members with bookings, pricing, amenities, and onboarding.
Be warm, conversational, and professional. Never make up information.

CURRENT REAL-WORLD TIME: The current local time in Delhi is {current_time_str}. Use this to understand references like "today" or "tomorrow", and to tell the user if the space is currently open.

CONTEXT (from knowledge base):
{context}

RULES:
1. PRICING: You MUST only state prices, plans, or fees if the user EXPLICITLY asks for them. Do not proactively list prices. When asked, only use prices from the CONTEXT block. Never invent or estimate a price.
2. IMAGES: ONLY show images if the user EXPLICITLY asks to see photos or pictures. When asked, ONLY show images for the specific service/space they requested. Do NOT use markdown. Instead, output this exact tag format: `[SEND_IMAGE: <filename>]`.
Available image filenames:
- Conference Room: `hoblix_conference-room-1.png`, `hoblix_conference-room-2.png`
- Meeting Room: `hoblix_meeting-room-1.png`, `hoblix_meeting-room-2.png`
- Podcast Studio: `hoblix_podcast-room-1.png`, `hoblix_podcast-room-2.png`
- Private Cabin: `hoblix_private-cabin-1.png`, `hoblix_private-cabin-2.png`
- Workstation/Desk: `hoblix_workstation-1.png`, `hoblix_workstation-2.png`
Pick 1 or 2 relevant images and include their tags in your message. Do NOT invent image names.
3. CONCISENESS: Keep your responses and follow-up questions extremely direct, concise, and crisp. Avoid long paragraphs, overly enthusiastic filler, or unnecessary pleasantries.
4. PRIVATE CABINS: Do NOT proactively give a deep dive or breakdown of the different private cabin sizes (Director, Medium, Large) unless the user explicitly asks for details about private cabins.
5. NO HALLUCINATIONS: Do NOT generate fake booking summaries or payment links.
6. FORMATTING: Do NOT use Em Dashes (—) or En Dashes (–) anywhere in your replies. Use normal punctuation like commas or periods instead.
7. SPACE TYPES: If the user asks what spaces or space types are offered, ONLY list the physical spaces: 1. Workstations, 2. Private Cabins, 3. Meeting Rooms, 4. Conference Rooms, 5. Podcast Room. Do NOT list pricing plans or passes (like One-Day Pass) as space types.
"""

    if mode == "onboarding":
        missing_fields = profile_dict.get("missing_fields", [])
        if not missing_fields:
            base += "\nONBOARDING COMPLETE: You have collected all necessary details. Let the user know our team will reach out to them shortly to confirm their booking and process payment. Do not generate fake payment links."
        else:
            missing_desc = ", ".join([f"'{f}' ({FIELD_DESCRIPTIONS.get(f, f)})" for f in missing_fields])
            base += f"""
ONBOARDING MODE: You are collecting details for a booking. The following details are still missing, listed strictly in order of priority: {missing_desc}.
Your goal is to conversationally and naturally collect this missing information.
CRITICAL RULE: You MUST ONLY ask for the FIRST missing detail in the priority list. NEVER ask multiple questions or follow-up questions in the same message. Keep your response conversational and natural, but brief. Answer their question if they asked one, then ask for exactly ONE missing detail (the most important one missing). Do NOT ask for their email or phone number.
"""
    else:
        base += "\nIf the user expresses interest in booking, registering, becoming a lead, or starting a trial, gently let them know that you can help them with that right now, and that you'll just need a few details. Do NOT redirect them to another WhatsApp number, link, or team. YOU are the system that will collect their details."
    return base

async def call_llm(messages: List[Dict[str, str]], system_prompt: str) -> str:
    payload = {
        "model": MODEL_ID,
        "messages": [{"role": "system", "content": system_prompt}] + messages,
    }
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
                json=payload,
                timeout=30
            )
            r.raise_for_status()
            data = r.json()
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            else:
                return "I'm having trouble connecting to my brain right now. Please try again later."
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return "Sorry, I am facing technical difficulties. Please try again later."

async def check_onboarding_intent(user_msg: str) -> bool:
    sys_prompt = "You are a proactive sales intent classifier. Does the user show ANY buying signals or interest in the coworking space? This includes asking about pricing, availability, booking a tour, getting a pass, or exploring memberships. Reply ONLY with YES or NO."
    reply = await call_llm([{"role": "user", "content": user_msg}], sys_prompt)
    return "YES" in reply.upper()

async def check_cancel_intent(user_msg: str) -> bool:
    sys_prompt = "You are an intent classifier. Evaluate the user's message. Does the user EXPLICITLY ask to stop, cancel, or abort the current booking process? A simple 'yes' or 'no' answer to a previous question is NOT a cancellation. Reply ONLY with YES or NO."
    reply = await call_llm([{"role": "user", "content": user_msg}], sys_prompt)
    return "YES" in reply.upper()

async def extract_missing_fields(user_msg: str, missing_fields: List[str]) -> dict:
    fields_list = ", ".join(missing_fields)
    sys_prompt = f"You are a data extractor. Look at the user's message and see if they provided values for any of these missing fields: {fields_list}. Return a JSON object with the extracted values (e.g. {{\"full_name\": \"John Doe\", \"location\": \"Delhi\"}}). Return {{}} if none are found. Reply ONLY with valid JSON."
    reply = await call_llm([{"role": "user", "content": user_msg}], sys_prompt)
    try:
        start = reply.find("{")
        end = reply.rfind("}") + 1
        if start != -1 and end != 0:
            return json.loads(reply[start:end])
    except Exception:
        pass
    return {}

async def infer_urgency(history: List[Dict[str, str]]) -> str:
    sys_prompt = "You are an urgency classifier. Based on the conversation history, classify the user's urgency to book/start as one of: 'low', 'medium', 'high', 'immediate'. Reply ONLY with the exact word."
    reply = await call_llm(history, sys_prompt)
    reply = reply.strip().lower()
    if reply in ["low", "medium", "high", "immediate"]:
        return reply
    return "medium" # default fallback

async def detect_profile_updates(user_msg: str) -> dict:
    sys_prompt = """You are an intent and data extractor. Check if the user is asking to update their 'spaceType', 'seatRange', 'location', or 'urgency'.
If yes, output a JSON object with the new values, e.g., {"spaceType": "Private Cabin", "seatRange": "10-15"}. If no updates, output {}. Reply ONLY with valid JSON."""
    reply = await call_llm([{"role": "user", "content": user_msg}], sys_prompt)
    try:
        start = reply.find("{")
        end = reply.rfind("}") + 1
        if start != -1 and end != 0:
            return json.loads(reply[start:end])
    except Exception:
        pass
    return {}
