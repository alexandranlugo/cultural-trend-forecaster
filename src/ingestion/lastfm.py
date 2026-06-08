import requests
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

API_KEY = os.getenv("LASTFM_API_KEY")
BASE_URL = "https://ws.audioscrobbler.com/2.0/"

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.features.artist_list import ARTISTS as SEED_ARTISTS

def get_artist_info(artist_name):
    params = {
        "method": "artist.getinfo",
        "artist": artist_name,
        "api_key": API_KEY,
        "format": "json"
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()
    if "error" in data:
        print(f"  Error for {artist_name}: {data.get('message')}")
        return None
    return data.get("artist", {})

def get_similar_artists(artist_name):
    params = {
        "method": "artist.getsimilar",
        "artist": artist_name,
        "limit": 5,
        "api_key": API_KEY,
        "format": "json"
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()
    similar = data.get("similarartists", {}).get("artist", [])
    return ", ".join([a["name"] for a in similar])

def get_top_tags(artist_name):
    params = {
        "method": "artist.gettoptags",
        "artist": artist_name,
        "api_key": API_KEY,
        "format": "json"
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()
    tags = data.get("toptags", {}).get("tag", [])
    return ", ".join([t["name"] for t in tags[:5]])

def fetch_artist_data(artist_name):
    info = get_artist_info(artist_name)
    if not info:
        return None

    stats = info.get("stats", {})
    listeners = int(stats.get("listeners", 0))
    playcount = int(stats.get("playcount", 0))

    # plays per listener is a signal of how deeply fans are engaging
    plays_per_listener = round(playcount / listeners, 2) if listeners > 0 else 0

    similar = get_similar_artists(artist_name)
    tags = get_top_tags(artist_name)

    return {
        "artist_name": info.get("name", artist_name),
        "listeners": listeners,
        "playcount": playcount,
        "plays_per_listener": plays_per_listener,
        "similar_artists": similar,
        "tags": tags,
        "lastfm_url": info.get("url", ""),
        "fetched_at": datetime.utcnow().isoformat()
    }

def run():
    records = []
    for name in SEED_ARTISTS:
        print(f"Fetching: {name}")
        data = fetch_artist_data(name)
        if data:
            records.append(data)
            print(f"  {data['listeners']:,} listeners | {data['playcount']:,} plays | {data['plays_per_listener']} plays/listener")
            print(f"  Tags: {data['tags']}")

    df = pd.DataFrame(records)
    path = "data/raw/lastfm_artists.csv"
    df.to_csv(path, index=False)
    print(f"\nSaved {len(df)} records to {path}")

if __name__ == "__main__":
    run()