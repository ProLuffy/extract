# AniCrew Job Manager - Create scraping jobs from anime lists
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import httpx
from bs4 import BeautifulSoup
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://wuwamuqo_db_user:NfhgBOs7LeRbSI6S@cluster0.zxqopbx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
ZENROWS_KEY = "700c782d212580adba1fd15d82df6257ecb8701c"

mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client.anicrew

async def zenrows_get(url):
    params = {'url': url, 'apikey': ZENROWS_KEY, 'mode': 'auto'}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.get('https://api.zenrows.com/v1/', params=params)
        return r.text if r.status_code == 200 else ""

async def create_jobs():
    print("📄 Creating jobs from anime lists...\n")
    
    sites = {
        "LORDSANIME": "https://www.lordsanime.in/all-anime-list/",
        "TPXSUB": "https://www.tpxsub.com/animes-in-hindi-sub/",
        "ANIMEDUBHINDI": "https://www.animedubhindi.me/",
    }
    
    for source, url in sites.items():
        print(f"Fetching {source}...")
        html = await zenrows_get(url)
        soup = BeautifulSoup(html, 'html.parser')
        
        links = soup.find_all('a', href=True)
        
        for link in links[:50]:  # First 50 anime
            text = link.get_text(strip=True)
            href = link.get('href', '')
            
            if len(text) > 5 and href.startswith('http'):
                # Determine priority (Hindi Dubbed > Hindi Sub)
                priority = 100 if 'dub' in text.lower() or 'hindi' in text.lower() else 50
                if 'sub' in text.lower():
                    priority = 50
                
                # Create job
                await db.jobs.update_one(
                    {'series_url': href},
                    {'$setOnInsert': {
                        'series_name': text[:100],
                        'series_url': href,
                        'source': source,
                        'priority': priority,
                        'status': 'pending',
                        'created_at': datetime.utcnow()
                    }},
                    upsert=True
                )
        
        print(f"✅ {source}: Jobs created\n")
    
    total_jobs = await db.jobs.count_documents({'status': 'pending'})
    print(f"\n📊 Total pending jobs: {total_jobs}")

if __name__ == "__main__":
    from datetime import datetime
    asyncio.run(create_jobs())
