# AniCrew Distributed Worker - Job Queue System
import os
import asyncio
import json
import httpx
from datetime import datetime
from bs4 import BeautifulSoup
import re
from motor.motor_asyncio import AsyncIOMotorClient

# Config
ZENROWS_KEY = os.getenv("ZENROWS_API_KEY", "700c782d212580adba1fd15d82df6257ecb8701c")
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://wuwamuqo_db_user:NfhgBOs7LeRbSI6S@cluster0.zxqopbx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
CODEWORDS_UPLOAD_API = "https://runtime.codewords.ai/anicrew_admin_panel_55416e72/admin/update-video-link"
WORKER_ID = os.getenv("WORKER_ID", "worker-1")

mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client.anicrew

print(f"🤖 Worker {WORKER_ID} starting...")

# ZenRows fetcher
async def zenrows_get(url, mode='premium'):
    params = {'url': url, 'apikey': ZENROWS_KEY}
    if mode == 'auto':
        params['mode'] = 'auto'
    else:
        params['premium_proxy'] = 'true'
        params['js_render'] = 'true'
        params['wait'] = '2000'
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.get('https://api.zenrows.com/v1/', params=params)
        return r.text if r.status_code == 200 else ""

# Extract video URL from episode page
async def extract_video_url(episode_url):
    html = await zenrows_get(episode_url)
    if not html:
        return None
    soup = BeautifulSoup(html, 'html.parser')
    # Look for video iframes/links
    for iframe in soup.find_all('iframe'):
        src = iframe.get('src', '')
        if src and ('streamtape' in src or 'dood' in src or 'player' in src):
            return src
    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        if href.endswith(('.mp4', '.mkv')) or 'download' in link.get_text(strip=True).lower():
            return href
    return None

# Upload to CodeWords backend
async def upload_to_backend(slug, video_url):
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            r = await client.post(CODEWORDS_UPLOAD_API, json={
                'slug': slug,
                'video_embed_url': video_url
            })
            return r.status_code == 200
        except:
            return False

# Process one anime series
async def process_anime_job(job):
    series_name = job['series_name']
    series_url = job['series_url']
    source = job['source']
    
    print(f"\n🎬 Processing: {series_name} ({source})")
    
    # Mark job as processing
    await db.jobs.update_one(
        {'_id': job['_id']},
        {'$set': {'status': 'processing', 'worker_id': WORKER_ID, 'started_at': datetime.utcnow()}}
    )
    
    try:
        # Scrape series page
        html = await zenrows_get(series_url)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find episodes
        links = soup.find_all('a', href=True)
        episodes = []
        
        for link in links:
            text = link.get_text(strip=True)
            href = link.get('href', '')
            if 'episode' in text.lower():
                ep_match = re.search(r'(\d+)', text)
                if ep_match:
                    episodes.append({'number': int(ep_match.group(1)), 'url': href, 'text': text})
        
        print(f"  📺 Found {len(episodes)} episodes")
        
        processed = 0
        for ep in episodes[:20]:  # Process first 20 per run
            # Extract video
            video_url = await extract_video_url(ep['url'])
            
            if video_url:
                # Generate slug
                slug = f"{series_name.lower().replace(' ', '-')}-ep{ep['number']}"
                
                # Upload to backend
                success = await upload_to_backend(slug, video_url)
                
                if success:
                    processed += 1
                    print(f"  ✅ Episode {ep['number']}: Uploaded!")
                    
                    # Save to MongoDB
                    await db.episodes.update_one(
                        {'series_name': series_name, 'episode_number': ep['number']},
                        {'$set': {'video_url': video_url, 'status': 'uploaded', 'uploaded_at': datetime.utcnow()}},
                        upsert=True
                    )
                else:
                    print(f"  ❌ Episode {ep['number']}: Upload failed")
            else:
                print(f"  ⚠️  Episode {ep['number']}: No video found")
            
            await asyncio.sleep(1)  # Rate limit
        
        # Mark job complete
        await db.jobs.update_one(
            {'_id': job['_id']},
            {'$set': {
                'status': 'completed',
                'processed_episodes': processed,
                'completed_at': datetime.utcnow()
            }}
        )
        
        print(f"  ✅ {series_name}: {processed} episodes uploaded!")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        await db.jobs.update_one(
            {'_id': job['_id']},
            {'$set': {'status': 'failed', 'error': str(e)}}
        )

# Main worker loop
async def worker_loop():
    print("="*70)
    print(f"🚀 Worker {WORKER_ID} - Waiting for jobs...")
    print("="*70)
    
    while True:
        # Get next job from queue (PRIORITY: Hindi Dubbed > Hindi Sub)
        job = await db.jobs.find_one_and_update(
            {'status': 'pending'},
            {'$set': {'status': 'claimed', 'worker_id': WORKER_ID}},
            sort=[('priority', -1), ('created_at', 1)]  # Highest priority first
        )
        
        if job:
            await process_anime_job(job)
        else:
            print("⏸️  No jobs available, waiting 30s...")
            await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(worker_loop())
