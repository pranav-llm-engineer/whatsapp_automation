import httpx
from backend.config import CRM_API
from backend.db.models import UserProfile
import asyncio

async def upsert_lead(profile: UserProfile, phone: str):
    """
    Upserts the lead to the CRM. If the lead doesn't exist, it creates it using
    all the required fields. If it does exist, it updates any changed fields.
    """
    if not CRM_API:
        print("CRM_API key not found, skipping CRM sync.")
        return

    def map_space_type(val):
        if not val: return "workstation"
        val = str(val).lower()
        if "private" in val or "cabin" in val: return "private_cabin"
        if "5" in val and "day" in val: return "five_days_pass"
        if "7" in val and "day" in val: return "seven_days_pass"
        if "day" in val: return "day_pass"
        if "meeting" in val: return "meeting_room"
        if "podcast" in val: return "podcast_room"
        if "conference" in val: return "conference_room"
        return "workstation"

    def map_urgency(val):
        if not val: return "medium"
        val = str(val).lower()
        if "low" in val: return "low"
        if "high" in val: return "high"
        if "immediate" in val or "now" in val or "urgent" in val: return "immediate"
        return "medium"

    payload = {
        "externalId": f"wa-{phone}",
        "customerName": profile.full_name,
        "mobileNumber": phone,
        "source": "organic_website",
        "spaceType": map_space_type(profile.spaceType),
        "seatRangeMin": profile.seatRangeMin or 1,
        "seatRangeMax": profile.seatRangeMax or 1,
        "urgency": map_urgency(profile.urgency),
        "location": profile.location or "Unknown",
        "spaceId": profile.spaceId or 1
    }

    url_post = "https://hoblix-crm-api.onrender.com/api/public/leads"
    headers = {
        "Authorization": f"Bearer {CRM_API}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        try:
            # Attempt POST first
            response = await client.post(url_post, json=payload, headers=headers, timeout=10)
            if response.status_code == 409:
                # If it already exists, gracefully fallback to PATCH for progressive updates
                url_patch = f"https://hoblix-crm-api.onrender.com/api/public/leads/{payload['externalId']}"
                patch_response = await client.patch(url_patch, json=payload, headers=headers, timeout=10)
                patch_response.raise_for_status()
                print(f"CRM Sync (PATCH) successful for {phone}: {patch_response.json()}")
            else:
                response.raise_for_status()
                print(f"CRM Sync (POST) successful for {phone}: {response.json()}")
        except Exception as e:
            print(f"Failed to sync with CRM for {phone}: {e}")
