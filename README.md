# 🎬 AniCrew Extraction Workers

**Distributed anime scraping system with job queue**

## ✨ Features

✅ **Job Queue System** - MongoDB-based task distribution  
✅ **Priority Processing** - Hindi Dubbed > Hindi Sub  
✅ **Parallel Workers** - Deploy 5-10 workers for 100+ episodes/day  
✅ **Auto Upload** - Direct upload to AniCrew.online  
✅ **ZenRows Integration** - Cloudflare bypass  
✅ **Series Organization** - Naruto episodes grouped together  

---

## 🚀 Quick Deploy

### Railway (Recommended)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

1. Click deploy button
2. Connect this repo
3. Add environment variables (see below)
4. Deploy!

### Heroku

```bash
heroku create anicrew-worker-1
heroku config:set ZENROWS_API_KEY=700c782d212580adba1fd15d82df6257ecb8701c
heroku config:set MONGO_URI=mongodb+srv://wuwamuqo_db_user:NfhgBOs7LeRbSI6S@cluster0.zxqopbx.mongodb.net/anicrew
heroku config:set WORKER_ID=worker-1
git push heroku main
```

### Render

1. New Web Service
2. Connect this repo
3. Build: `pip install -r requirements.txt`
4. Start: `python worker.py`
5. Add env vars

---

## ⚙️ Environment Variables

```env
ZENROWS_API_KEY=700c782d212580adba1fd15d82df6257ecb8701c
MONGO_URI=mongodb+srv://wuwamuqo_db_user:NfhgBOs7LeRbSI6S@cluster0.zxqopbx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
WORKER_ID=worker-1  # Change for each worker (worker-2, worker-3, etc)
```

---

## 📊 How It Works

### 1. Job Manager Creates Jobs

```bash
python job_manager.py
```

- Scrapes anime list pages
- Creates jobs in MongoDB
- **Priority:** Hindi Dubbed = 100, Hindi Sub = 50

### 2. Workers Process Jobs

```bash
python worker.py
```

- Claims next job from queue (highest priority)
- Scrapes series page for episodes
- Extracts video URLs
- Uploads to AniCrew.online automatically
- Marks job complete

### 3. MongoDB Collections

**jobs** - Anime series to process
```json
{
  "series_name": "Naruto Shippuden",
  "series_url": "https://...",
  "source": "LORDSANIME",
  "priority": 100,
  "status": "pending"  // pending, processing, completed, failed
}
```

**episodes** - Extracted episodes
```json
{
  "series_name": "Naruto Shippuden",
  "episode_number": 1,
  "video_url": "https://streamtape.com/...",
  "status": "uploaded"
}
```

---

## ⚡ Speed

| Workers | Episodes/Day | Month 1 | 6 Months |
|---------|-------------|---------|----------|
| 1 | 15-20 | 450-600 | 3K-4K |
| 5 | 75-100 | 2K-3K | 15K-20K |
| **10** | **150-200** | **4.5K-6K** | **30K-40K** |

---

## 🔄 Deploy Multiple Workers

**Railway:**
1. Deploy once
2. Clone service 5-10 times
3. Change `WORKER_ID` for each (worker-1, worker-2, etc)
4. All run in parallel!

**Heroku:**
```bash
# Deploy 5 workers
for i in {1..5}; do
  heroku create anicrew-worker-$i
  heroku config:set WORKER_ID=worker-$i -a anicrew-worker-$i
  git push heroku main -a anicrew-worker-$i
done
```

---

## 🎯 Sources

- **LordsAnime.in** - All anime list
- **TPXSub.com** - Hindi sub anime
- **AnimeDubHindi.me** - Multi-audio

---

## 🛠️ Maintenance

### Create Jobs
```bash
python job_manager.py
```

### Check Stats (MongoDB)
```python
from pymongo import MongoClient
client = MongoClient(MONGO_URI)
db = client.anicrew

print(f"Pending jobs: {db.jobs.count_documents({'status': 'pending'})}")
print(f"Completed: {db.jobs.count_documents({'status': 'completed'})}")
print(f"Total episodes: {db.episodes.count_documents({})}")
```

---

## 🎉 Results

**Episodes automatically appear on:** https://AniCrew.online

---

**Built with:** CodeWords Backend + Railway Workers + MongoDB + ZenRows
