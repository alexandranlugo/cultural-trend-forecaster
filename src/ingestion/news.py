import requests
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

API_KEY = os.getenv("NEWS_API_KEY")
BASE_URL = "https://newsapi.org/v2/everything"

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.features.artist_list import ARTISTS as SEED_ARTISTS

def fetch_news(artist_name):
    from_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
    params = {
        "q": f'"{artist_name}"',
        "from": from_date,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 20,
        "apiKey": API_KEY
    }
    response = requests.get(BASE_URL, params=params)
    articles = response.json().get("articles", [])
    records = []
    for a in articles:
        records.append({
            "artist_name": artist_name,
            "headline": a["title"],
            "source": a["source"]["name"],
            "published_at": a["publishedAt"],
            "url": a["url"],
            "fetched_at": datetime.utcnow().isoformat()
        })
    return records

def run():
    all_records = []
    for name in SEED_ARTISTS:
        articles = fetch_news(name)
        all_records.extend(articles)
        print(f"Fetched {len(articles)} headlines for: {name}")
    df = pd.DataFrame(all_records)
    path = "data/raw/news_headlines.csv"
    df.to_csv(path, index=False)
    print(f"\nSaved {len(df)} records to {path}")

if __name__ == "__main__":
    run()