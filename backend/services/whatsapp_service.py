import httpx
from backend.config import WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID

async def send_whatsapp_message(to_phone: str, text: str):
    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        print("WhatsApp credentials not configured.")
        return

    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_phone,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": text
        }
    }
    
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(url, headers=headers, json=payload, timeout=10.0)
            r.raise_for_status()
        except Exception as e:
            print(f"Failed to send WhatsApp message to {to_phone}: {e}")

async def send_whatsapp_image(to_phone: str, image_url: str):
    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        print("WhatsApp credentials not configured.")
        return

    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_phone,
        "type": "image",
        "image": {
            "link": image_url
        }
    }
    
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(url, headers=headers, json=payload, timeout=10.0)
            r.raise_for_status()
        except Exception as e:
            print(f"Failed to send WhatsApp image to {to_phone}: {e}")

async def download_whatsapp_media(media_id: str) -> bytes:
    if not WHATSAPP_ACCESS_TOKEN:
        return b""
        
    url = f"https://graph.facebook.com/v19.0/{media_id}"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # Step 1: Get media URL
            r = await client.get(url, headers=headers, timeout=10.0)
            r.raise_for_status()
            media_url = r.json().get("url")
            
            if not media_url:
                return b""
                
            # Step 2: Download the actual binary data
            r_media = await client.get(media_url, headers=headers, timeout=20.0)
            r_media.raise_for_status()
            return r_media.content
        except Exception as e:
            print(f"Failed to download WhatsApp media {media_id}: {e}")
            return b""
