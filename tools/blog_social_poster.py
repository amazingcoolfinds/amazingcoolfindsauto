#!/usr/bin/env python3
"""
Blog Article Social Poster
Shares blog articles to Reddit, Facebook, X, and Pinterest
"""
import os
import sys
import json
import requests
from datetime import datetime

BLOG_URL = "https://article-generator.amazingcoolfinds.workers.dev/api/articles"
UPLOAD_POST_API = "https://api.upload-post.com/api/upload_text"
API_KEY = os.getenv("UPLOADPOST_API_KEY")
USER = "AmazingCoolFinds"

def get_latest_articles(count=5):
    """Fetch latest articles from blog"""
    try:
        resp = requests.get(BLOG_URL, timeout=10)
        if resp.ok:
            articles = resp.json()
            return sorted(articles, key=lambda x: x.get('createdAt', ''), reverse=True)[:count]
    except Exception as e:
        print(f"Error fetching articles: {e}")
    return []

def post_to_social(article):
    """Post article to Reddit, X, Facebook, Pinterest"""
    if not API_KEY:
        print("❌ UPLOADPOST_API_KEY not set")
        return False
    
    title = article.get('title', '')[:200]
    slug = article.get('slug', '')
    article_url = f"https://amazing-cool-finds.com/articles?id={slug}"
    
    # Create post content
    content = f"""
{article.get('excerpt', article.get('metaDescription', '')[:300])}...

🔗 Read more: {article_url}
#blog #lifestyle #gadgets #amazonfinds
    """.strip()
    
    headers = {"Authorization": f"Apikey {API_KEY}"}
    
    # Try X (Twitter) first - simplest platform
    try:
        data = {
            "user": USER,
            "platform[]": ["x"],
            "title": f"{title}\n\n🔗 {article_url}",
        }
        resp = requests.post(UPLOAD_POST_API, data=data, headers=headers, timeout=60)
        result = resp.json()
        
        if result.get('success'):
            print(f"✅ Posted to X: {title[:50]}...")
            for platform, info in result.get('results', {}).items():
                if info.get('success'):
                    print(f"   ✅ {platform}: {info.get('url', 'OK')}")
                else:
                    print(f"   ⚠️ {platform}: {info.get('error', 'Failed')}")
            return True
        else:
            print(f"❌ Failed: {result.get('message')}")
            print(f"   Response: {result}")
    except Exception as e:
        print(f"❌ Error posting: {e}")
    
    return False

def main():
    print("📝 Blog Article Social Poster")
    print("=" * 40)
    
    # Get articles to post
    articles = get_latest_articles(3)
    
    if not articles:
        print("❌ No articles found")
        return
    
    print(f"📰 Found {len(articles)} latest articles\n")
    
    for i, article in enumerate(articles, 1):
        print(f"\n[{i}/{len(articles)}] Posting: {article.get('title', '')[:60]}...")
        post_to_social(article)
    
    print("\n" + "=" * 40)
    print("✅ Done!")

if __name__ == "__main__":
    main()
