import requests
import os
from dotenv import load_dotenv
load_dotenv()

# === CONFIG ===
KLAVIYO_API_KEY = os.getenv("KLAVIYO_API_KEY")  # or paste your private API key directly here
BASE_URL = "https://a.klaviyo.com/api"
HEADERS = {
    "Authorization": f"Klaviyo-API-Key {KLAVIYO_API_KEY}",
    "revision": "2023-10-15",  # Latest as of now
    "Content-Type": "application/json"
}

def get_flows(limit=25):
    url = f"{BASE_URL}/flows/?page[size]={limit}"

    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        flows = data.get("data", [])
        print(f"\n🔍 Found {len(flows)} flows:\n")

        for flow in flows:
            print(f"📩 Flow Name: {flow['attributes']['name']}")
            print(f"   ➤ ID: {flow['id']}")
            print(f"   ➤ Status: {flow['attributes']['status']}")
            print("-" * 40)

        return flows

    except requests.exceptions.RequestException as e:
        print("❌ Error fetching flows:", e)
        return []

if __name__ == "__main__":
    # For testing without env vars, uncomment below and paste your key
    # KLAVIYO_API_KEY = "YOUR_API_KEY_HERE"
    
    get_flows()
