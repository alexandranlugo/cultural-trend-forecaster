import requests
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")
BASE_URL = "https://www.googleapis.com/youtube/v3"

SEED_ARTISTS = [
    "Chappell Roan", "Sabrina Carpenter", "Doechii",
    "Benson Boone", "Gracie Abrams", "Teddy Swims",
    "Noah Kahan", "Rema", "Ice Spice", "Tyla",
    "Tinashe", "Mk.gee", "Clairo", "FKA Twigs", "Ethel Cain"
]

def search_artist_videos(artist_name, max_results=10):
    published_after = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y-%m-%dT%H:%M:%SZ")
    params = {
        "part": "snippet",
        "q": artist_name,
        "type": "video",
        "videoCategoryId": "10",  # music category
        "publishedAfter": published_after,
        "maxResults": max_results,
        "order": "viewCount",
        "key": API_KEY
    }
    response = requests.get(f"{BASE_URL}/search", params=params)
    return response.json().get("items", [])

def get_video_stats(video_ids):
    params = {
        "part": "statistics,snippet",
        "id": ",".join(video_ids),
        "key": API_KEY
    }
    response = requests.get(f"{BASE_URL}/videos", params=params)
    return response.json().get("items", [])

def fetch_artist_data(artist_name):
    videos = search_artist_videos(artist_name)
    if not videos:
        return []

    video_ids = [v["id"]["videoId"] for v in videos if "videoId" in v.get("id", {})]
    if not video_ids:
        return []

    stats = get_video_stats(video_ids)
    records = []
    for item in stats:
        s = item.get("statistics", {})
        snippet = item.get("snippet", {})
        published = snippet.get("publishedAt", "")
        view_count = int(s.get("viewCount", 0))
        like_count = int(s.get("likeCount", 0))
        comment_count = int(s.get("commentCount", 0))

        # view velocity: views per day since publish
        try:
            pub_date = datetime.fromisoformat(published.replace("Z", "+00:00"))
            days_live = max((datetime.now(timezone.utc) - pub_date).days, 1)
            views_per_day = round(view_count / days_live, 2)
        except Exception:
            views_per_day = None

        records.append({
            "artist_name": artist_name,
            "video_id": item["id"],
            "video_title": snippet.get("title", ""),
            "channel_name": snippet.get("channelTitle", ""),
            "published_at": published,
            "view_count": view_count,
            "like_count": like_count,
            "comment_count": comment_count,
            "views_per_day": views_per_day,
            "fetched_at": datetime.utcnow().isoformat()
        })
    return records

def run():
    all_records = []
    for name in SEED_ARTISTS:
        records = fetch_artist_data(name)
        all_records.extend(records)
        total_views = sum(r["view_count"] for r in records)
        print(f"Fetched {len(records)} videos for {name} — {total_views:,} total views")

    df = pd.DataFrame(all_records)
    path = "data/raw/youtube_videos.csv"
    df.to_csv(path, index=False)
    print(f"\nSaved {len(df)} records to {path}")

if __name__ == "__main__":
    run()