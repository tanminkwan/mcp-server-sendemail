import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL")
TOKEN = os.getenv("API_BEARER_TOKEN")
SSL_VERIFY = False

async def main():
    async with httpx.AsyncClient(verify=SSL_VERIFY) as client:
        headers = {"Authorization": f"Bearer {TOKEN}"}
        
        print(f"\nTesting /api/v1/knowledge/mdcontent/list...")
        try:
            res = await client.get(f"{API_BASE_URL}/api/v1/knowledge/mdcontent/list", headers=headers, params={"search_tags": "test_id", "max": 1})
            print(f"Status: {res.status_code}")
            print(f"Body: {res.text[:200]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
