# 🏆 LivItUpDeals — Automated Affiliate Video System

**Amazon Products → AI Scripts → Videos → YouTube Shorts → $$$**

---

## 📦 What You're Getting

A fully automated pipeline that:
1. Fetches luxury/premium products from Amazon using the Creators API
2. Generates viral video scripts with Claude AI
3. Compiles product videos with FFmpeg (text animations + music)
4. Auto-uploads to YouTube Shorts with optimized metadata
5. Logs everything to a JSON database that powers your landing page
6. Landing page at liveitupdeals.com reads that JSON and displays products live

---

## 🗺️ Project Structure

```
liveitupdeals/
├── pipeline.py              ← Main automation engine (run this)
├── index.html               ← Landing page (deploy to liveitupdeals.com)
├── requirements.txt         ← Python dependencies
├── .env.example             ← Template for your secrets
├── .env                     ← YOUR ACTUAL KEYS (create this, never commit)
├── google_credentials/
│   └── client_secret.json   ← YouTube OAuth file (download from Google)
├── assets/
│   └── background_music.mp3 ← Royalty-free music (download below)
├── data/
│   └── products.json        ← Auto-generated product database
├── output_videos/           ← Generated .mp4 files
├── output_images/           ← Downloaded product images
└── logs/
    └── pipeline.log         ← Full execution log
```

---

## ⚡ SETUP: Start Today (Step by Step)

### STEP 1 — Install System Dependencies

**FFmpeg** (video compiler — essential):
```bash
# Linux / Bluehost SSH:
sudo apt-get update && sudo apt-get install -y ffmpeg

# macOS:
brew install ffmpeg

# Windows:
# Download from https://ffmpeg.org/download.html → add to PATH
```

### STEP 2 — Clone & Install Python

```bash
# 1. Put all files in your project folder
cd liveitupdeals

# 2. Install Python packages
pip install -r requirements.txt
```

### STEP 3 — Amazon API Keys

1. Go to **associates.amazon.com** → Sign in
2. Click your name → **API Settings**
3. You'll see your **Access Key ID** and **Secret Access Key**
4. Your **Associate Tag** looks like `yourname-20`

### STEP 4 — Anthropic API Key (for AI scripts)

1. Go to **console.anthropic.com** → Sign up (free tier available)
2. Click **API Keys** → Create new key
3. Copy the key (starts with `sk-ant-`)
4. The pipeline uses `claude-haiku-3` which is extremely cheap (~$0.25/1M tokens)
   - At 3 videos/day, you'll spend roughly **$0.01/day** on AI

### STEP 5 — Create Your .env File

```bash
cp .env.example .env
# Open .env and fill in your real values
```

### STEP 6 — YouTube OAuth Setup (one-time, ~5 minutes)

1. Go to **console.cloud.google.com**
2. Create a new project (any name)
3. Click **APIs & Services** → **Library**
4. Search `YouTube Data API v3` → **Enable**
5. Click **APIs & Services** → **Credentials**
6. Click **Create Credentials** → **OAuth client ID**
7. Select **Desktop application**
8. Click **Create** → **Download JSON**
9. Rename the downloaded file to `client_secret.json`
10. Move it into: `google_credentials/client_secret.json`

**First run note:** The first time you run the pipeline, a browser window will open
asking you to authorize. Click through — this creates a token that auto-renews.

### STEP 7 — Background Music

Download a free royalty-free track (15-30 seconds, upbeat/luxury feel):
- **Pixabay Music**: https://pixabay.com/music/ → search "luxury"
- **YouTube Audio Library**: https://studio.youtube.com → Audio Library
- Save as `assets/background_music.mp3`

### STEP 8 — Validate Everything

```bash
python pipeline.py --setup
```

This checks all your keys, packages, and files. Fix anything marked ❌.

### STEP 9 — RUN IT! 🚀

```bash
python pipeline.py --run
```

Watch the logs — you'll see products being fetched, scripts generated, and videos uploading.

---

## 🤖 Automate Daily Execution

### Option A: Cron Job (Linux / Bluehost SSH)
```bash
crontab -e
# Add this line — runs every day at 9:00 AM:
0 9 * * * /usr/bin/python3 /path/to/liveitupdeals/pipeline.py --run >> /path/to/logs/cron.log 2>&1
```

### Option B: Task Scheduler (Windows)
- Open **Task Scheduler** → Create Basic Task
- Set trigger: Daily, 9:00 AM
- Action: Start program → `python` with arguments `pipeline.py --run`

---

## 🌐 Deploy the Landing Page

### On Bluehost (your hosting):
1. SSH into your Bluehost account
2. Navigate to the public_html folder for liveitupdeals.com
3. Upload: `index.html`, and create the `data/` folder
4. The pipeline writes `products.json` to `data/` — copy this after each run
   (or better: point the pipeline's DATA_DIR to your public_html/data/)

### Auto-sync option:
In `pipeline.py`, change the DATA_DIR to point directly to your Bluehost web root
so products.json updates live after every pipeline run.

---

## 🚀 Deployment to Hosting

**Ready to deploy? Check out the complete guide:**

👉 **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** — Guía completa en español

The guide covers:
- ✅ Hosting compartido sin Python (pipeline local + FTP upload)
- ✅ VPS o hosting con Python (deployment completo automatizado)
- ✅ Configuración específica para Bluehost
- ✅ Scripts de deployment automatizados
- ✅ Troubleshooting común

**Quick deployment:**
```bash
# Option 1: Update products.json only (no video generation)
python pipeline.py --update-website

# Option 2: Deploy to hosting with script
./deploy.sh

# Option 3: Full pipeline with videos (requires FFmpeg + YouTube auth)
python pipeline.py --run
```

---

---

## 💰 Revenue Math (Realistic Projections)

| Scenario | Views/Day | CTR | Conversions | Avg Order | Commission | Daily Revenue |
|----------|-----------|-----|-------------|-----------|------------|---------------|
| Conservative | 500 | 2% | 0.5% | $80 | 5% | $0.40 |
| Growing | 5,000 | 3% | 1% | $100 | 7% | $10.50 |
| Scaled | 50,000 | 4% | 1.5% | $120 | 8% | $288 |

**Key insight:** YouTube Shorts can go viral overnight. One video hitting 1M views
with even 0.5% conversion at $50 avg = $2,500 from a single video.

---

## 🎯 Product Strategy (Optimized by Commission)

| Category | Commission | Why Target It |
|----------|------------|---------------|
| Luxury Beauty | **10%** | Highest commission + huge search volume |
| Amazon Games | 20% | Niche but high-converting |
| Handmade Items | 5% | Unique, shareable content |
| Fashion/Watches | 4% | High ticket = big dollar commissions |
| Premium Tech | 3-4% | Massive volume, always trending |
| Home/Kitchen | 3% | Evergreen content, year-round demand |

---

## 📟 Configuration Quick Reference

Edit these in `pipeline.py`:

| Setting | Default | What It Does |
|---------|---------|--------------|
| `PRODUCT_TARGETS` | 8 categories | What products to search |
| `ITEMS_PER_SEARCH` | 3 | Products per keyword |
| `max_uploads_per_run` | 3 | YouTube daily upload limit (stay safe) |
| `VIDEO_DURATION_SECS` | 15 | Sweet spot for Shorts algorithm |

---

## ⚠️ Important Rules

- **YouTube**: Don't upload more than 3-5 Shorts/day on a new channel (spam detection)
- **Amazon**: API rate limit is 1 request/second — the pipeline respects this
- **Attribution**: Always include Amazon affiliate disclosure (already in your landing page)
- **Images**: Amazon product images are for promotional use via their affiliate program — this is permitted

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| "amazon_creatorsapi not found" | Run `pip install python-amazon-paapi` |
| "FFmpeg not found" | Install FFmpeg (see Step 1) |
| YouTube auth browser doesn't open | Delete `google_credentials/token.pkl` and re-run |
| "ItemNotAccessible" from Amazon | Some products are restricted — pipeline skips them automatically |
| Video has no audio | Download background music to `assets/background_music.mp3` |
