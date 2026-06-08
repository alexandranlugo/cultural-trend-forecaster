from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta, timezone
import requests
import psycopg2
import os

SEED_ARTISTS = [
    "Chappell Roan", "Sabrina Carpenter", "Doechii",
    "Benson Boone", "Gracie Abrams", "Teddy Swims",
    "Noah Kahan", "Rema", "Ice Spice", "Tyla",
    "Tinashe", "Mk.gee", "Clairo", "FKA Twigs", "Ethel Cain"
]

def fetch_youtube():
    API_KEY = os.environ["YOUTUBE_API_KEY"]
    BASE_URL = "https://www.googleapis.com/youtube/v3"
    conn = psycopg2.connect(
        host="postgres",
        dbname="airflow",
        user="airflow",
        password="airflow"
    )
    cur = conn.cursor()
    inserted = skipped = 0

    for name in SEED_ARTISTS:
        published_after = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y-%m-%dT%H:%M:%SZ")
        search_r = requests.get(f"{BASE_URL}/search", params={
            "part": "snippet", "q": name, "type": "video",
            "videoCategoryId": "10", "publishedAfter": published_after,
            "maxResults": 10, "order": "viewCount", "key": API_KEY
        })
        items = search_r.json().get("items", [])
        video_ids = [v["id"]["videoId"] for v in items if "videoId" in v.get("id", {})]
        if not video_ids:
            continue

        stats_r = requests.get(f"{BASE_URL}/videos", params={
            "part": "statistics,snippet",
            "id": ",".join(video_ids),
            "key": API_KEY
        })

        for item in stats_r.json().get("items", []):
            s = item.get("statistics", {})
            snippet = item.get("snippet", {})
            view_count = int(s.get("viewCount", 0))
            like_count = int(s.get("likeCount", 0))
            comment_count = int(s.get("commentCount", 0))

            # data quality: skip videos with 0 views
            if view_count == 0:
                skipped += 1
                continue

            published = snippet.get("publishedAt", "")
            try:
                pub_date = datetime.fromisoformat(published.replace("Z", "+00:00"))
                days_live = max((datetime.now(timezone.utc) - pub_date).days, 1)
                views_per_day = round(view_count / days_live, 2)
            except Exception:
                views_per_day = None

            # deduplication: skip if video_id already exists
            cur.execute("SELECT 1 FROM youtube_videos WHERE video_id = %s", (item["id"],))
            if cur.fetchone():
                skipped += 1
                continue

            cur.execute("""
                INSERT INTO youtube_videos
                  (artist_name, video_id, video_title, channel_name,
                   published_at, view_count, like_count, comment_count,
                   views_per_day, fetched_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                name, item["id"],
                snippet.get("title", ""),
                snippet.get("channelTitle", ""),
                published, view_count, like_count,
                comment_count, views_per_day,
                datetime.now()
            ))
            inserted += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"Inserted {inserted} YouTube records. Skipped {skipped}.")

default_args = {"retries": 1, "retry_delay": timedelta(minutes=5)}

with DAG(
    dag_id="youtube_daily",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=["ingestion"]
) as dag:
    PythonOperator(
        task_id="fetch_youtube_data",
        python_callable=fetch_youtube
    )