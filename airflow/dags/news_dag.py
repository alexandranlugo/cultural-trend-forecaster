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

def fetch_news():
    API_KEY = os.environ["NEWS_API_KEY"]
    BASE_URL = "https://newsapi.org/v2/everything"
    conn = psycopg2.connect(
        host="postgres",
        dbname="airflow",
        user="airflow",
        password="airflow"
    )
    cur = conn.cursor()
    inserted = skipped = 0

    from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    for name in SEED_ARTISTS:
        r = requests.get(BASE_URL, params={
            "q": f'"{name}"',
            "from": from_date,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 20,
            "apiKey": API_KEY
        })
        articles = r.json().get("articles", [])

        for a in articles:
            # data quality: skip if headline or url is missing
            if not a.get("title") or not a.get("url"):
                skipped += 1
                continue

            # deduplication: skip if url already exists
            cur.execute("SELECT 1 FROM news_headlines WHERE url = %s", (a["url"],))
            if cur.fetchone():
                skipped += 1
                continue

            cur.execute("""
                INSERT INTO news_headlines
                  (artist_name, headline, source, published_at, url, fetched_at)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (
                name,
                a["title"],
                a["source"]["name"],
                a.get("publishedAt"),
                a["url"],
                datetime.now()
            ))
            inserted += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"Inserted {inserted} news records. Skipped {skipped} duplicates/nulls.")

default_args = {"retries": 1, "retry_delay": timedelta(minutes=5)}

with DAG(
    dag_id="news_daily",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=["ingestion"]
) as dag:
    PythonOperator(
        task_id="fetch_news_data",
        python_callable=fetch_news
    )