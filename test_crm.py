import httpx
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
CRM_API = os.getenv("CRM_API", "")

async def test_crm():
    print(f"Using CRM_API key length: {len(CRM_API)}")
    
    url_post = "https://hoblix-crm-api.onrender.com/api/public/leads"
    
    payload = {
        "externalId": "wa-test-0000000000",
        "customerName": "Test Developer",
        "mobileNumber": "0000000000",
        "source": "organic_website",
        "spaceType": "day_pass",
        "seatRangeMin": 1,
        "seatRangeMax": 1,
        "urgency": "medium",
        "location": "Najafgarh",
        "spaceId": 1
    }

    headers = {
        "Authorization": f"Bearer {CRM_API}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        print(f"\n--- Testing POST to {url_post} ---")
        try:
            response = await client.post(url_post, json=payload, headers=headers, timeout=10)
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {response.headers}")
            print(f"Body: {response.text}")
            
            if response.status_code == 409:
                print("\nReceived 409 Conflict (Lead already exists). Testing PATCH fallback...")
                url_patch = f"https://hoblix-crm-api.onrender.com/api/public/leads/{payload['externalId']}"
                patch_response = await client.patch(url_patch, json=payload, headers=headers, timeout=10)
                print(f"PATCH Status Code: {patch_response.status_code}")
                print(f"PATCH Body: {patch_response.text}")
                patch_response.raise_for_status()
            else:
                response.raise_for_status()
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_crm())
