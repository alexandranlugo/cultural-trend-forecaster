from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
import psycopg2
import os

SEED_ARTISTS = [
    "Chappell Roan", "Sabrina Carpenter", "Doechii",
    "Benson Boone", "Gracie Abrams", "Teddy Swims",
    "Noah Kahan", "Rema", "Ice Spice", "Tyla",
    "Tinashe", "Mk.gee", "Clairo", "FKA Twigs", "Ethel Cain"
]

def fetch_lastfm():
    API_KEY = os.environ["LASTFM_API_KEY"]
    BASE_URL = "https://ws.audioscrobbler.com/2.0/"
    conn = psycopg2.connect(
    host="postgres",
    dbname="airflow",
    user="airflow",
    password="airflow"
)
    cur = conn.cursor()
    inserted = 0

    for name in SEED_ARTISTS:
        r = requests.get(BASE_URL, params={
            "method": "artist.getinfo",
            "artist": name,
            "api_key": API_KEY,
            "format": "json"
        })
        data = r.json().get("artist", {})
        if not data:
            continue

        stats = data.get("stats", {})
        listeners = int(stats.get("listeners", 0))
        playcount = int(stats.get("playcount", 0))
        plays_per_listener = round(playcount / listeners, 2) if listeners > 0 else 0

        tags_r = requests.get(BASE_URL, params={
            "method": "artist.gettoptags",
            "artist": name,
            "api_key": API_KEY,
            "format": "json"
        })
        tags = ", ".join([t["name"] for t in tags_r.json().get("toptags", {}).get("tag", [])[:5]])

        sim_r = requests.get(BASE_URL, params={
            "method": "artist.getsimilar",
            "artist": name,
            "limit": 5,
            "api_key": API_KEY,
            "format": "json"
        })
        similar = ", ".join([a["name"] for a in sim_r.json().get("similarartists", {}).get("artist", [])])

        # data quality: skip if listeners is 0
        if listeners == 0:
            print(f"Skipping {name} — no listener data")
            continue

        cur.execute("""
            INSERT INTO lastfm_artists
              (artist_name, listeners, playcount, plays_per_listener,
               similar_artists, tags, lastfm_url, fetched_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            data.get("name", name),
            listeners, playcount, plays_per_listener,
            similar, tags,
            data.get("url", ""),
            datetime.now()
        ))
        inserted += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"Inserted {inserted} Last.fm records.")

default_args = {"retries": 1, "retry_delay": timedelta(minutes=5)}

with DAG(
    dag_id="lastfm_daily",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=["ingestion"]
) as dag:
    PythonOperator(
        task_id="fetch_lastfm_data",
        python_callable=fetch_lastfm
    )