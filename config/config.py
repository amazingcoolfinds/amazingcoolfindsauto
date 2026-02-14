#!/usr/bin/env python3
"""
Configuration module for LivItUpDeals
Centralizes all configuration and environment variables
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ─── BASE PATHS ────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

# ─── AMAZON API CREDENTIALS ────────────────────────────────
AMAZON_ACCESS_KEY = os.getenv("AMAZON_ACCESS_KEY", "")
AMAZON_SECRET_KEY = os.getenv("AMAZON_SECRET_KEY", "")
AMAZON_ASSOCIATE_TAG = os.getenv("AMAZON_ASSOCIATE_TAG", "amazingcoolfinds-20")

# ─── AI API CREDENTIALS ─────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ─── DIRECTORY STRUCTURE ────────────────────────────────────
# Allow custom DATA_DIR for hosting (e.g., point to public_html/data/)
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
VIDEOS_DIR = BASE_DIR / "output_videos"
IMAGES_DIR = BASE_DIR / "output_images"
LOGS_DIR = BASE_DIR / "logs"
ASSETS_DIR = BASE_DIR / "assets"
GOOGLE_CREDS_DIR = BASE_DIR / "google_credentials"

# Create directories if they don't exist
for directory in [DATA_DIR, VIDEOS_DIR, IMAGES_DIR, LOGS_DIR, ASSETS_DIR, GOOGLE_CREDS_DIR]:
    directory.mkdir(exist_ok=True, parents=True)

# ─── PIPELINE SETTINGS ──────────────────────────────────────
ITEMS_PER_SEARCH = int(os.getenv("ITEMS_PER_SEARCH", "3"))
MAX_UPLOADS_PER_RUN = int(os.getenv("MAX_UPLOADS_PER_RUN", "3"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# ─── VIDEO SETTINGS ─────────────────────────────────────────
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30
VIDEO_DURATION_SECS = 15

# ─── PRODUCT TARGETS ────────────────────────────────────────
PRODUCT_TARGETS = [
    {"category": "Beauty", "keywords": "luxury beauty skincare premium", "commission": "10%"},
    {"category": "Beauty", "keywords": "luxury perfume fragrance high end", "commission": "10%"},
    {"category": "Electronics", "keywords": "premium tech gadgets 2025", "commission": "4%"},
    {"category": "Clothing", "keywords": "luxury fashion men premium jacket", "commission": "4%"},
    {"category": "Clothing", "keywords": "luxury fashion women premium dress", "commission": "4%"},
    {"category": "Home", "keywords": "premium home decor luxury modern", "commission": "3%"},
    {"category": "Electronics", "keywords": "premium laptop high end 2025", "commission": "3%"},
    {"category": "Electronics", "keywords": "luxury smartwatch premium 2025", "commission": "4%"},
]

# ─── FILE PATHS ─────────────────────────────────────────────
BACKGROUND_MUSIC = ASSETS_DIR / "background_music.mp3"
GOOGLE_CLIENT_SECRET = GOOGLE_CREDS_DIR / "client_secret.json"
PRODUCTS_JSON = DATA_DIR / "products.json"
PIPELINE_LOG = LOGS_DIR / "pipeline.log"

def validate_required_env():
    """
    Validate that all required environment variables are set.
    Returns tuple: (is_valid, missing_vars)
    """
    required = {
        "AMAZON_ACCESS_KEY": AMAZON_ACCESS_KEY,
        "AMAZON_SECRET_KEY": AMAZON_SECRET_KEY,
        "AMAZON_ASSOCIATE_TAG": AMAZON_ASSOCIATE_TAG,
        "GEMINI_API_KEY": GEMINI_API_KEY,
    }
    
    missing = [key for key, value in required.items() if not value]
    return (len(missing) == 0, missing)
