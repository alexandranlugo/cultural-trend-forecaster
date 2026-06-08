from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.base import BaseHook
from datetime import datetime
import psycopg2
import os

def create_tables():
    conn = psycopg2.connect(
        host="postgres",
        dbname="airflow",
        user="airflow",
        password="airflow"
    )
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS lastfm_artists (
            id SERIAL PRIMARY KEY,
            artist_name TEXT NOT NULL,
            listeners INTEGER,
            playcount INTEGER,
            plays_per_listener FLOAT,
            similar_artists TEXT,
            tags TEXT,
            lastfm_url TEXT,
            fetched_at TIMESTAMP,
            inserted_at TIMESTAMP DEFAULT NOW()
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS youtube_videos (
            id SERIAL PRIMARY KEY,
            artist_name TEXT NOT NULL,
            video_id TEXT UNIQUE,
            video_title TEXT,
            channel_name TEXT,
            published_at TIMESTAMP,
            view_count INTEGER,
            like_count INTEGER,
            comment_count INTEGER,
            views_per_day FLOAT,
            fetched_at TIMESTAMP,
            inserted_at TIMESTAMP DEFAULT NOW()
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS news_headlines (
            id SERIAL PRIMARY KEY,
            artist_name TEXT NOT NULL,
            headline TEXT,
            source TEXT,
            published_at TIMESTAMP,
            url TEXT UNIQUE,
            fetched_at TIMESTAMP,
            inserted_at TIMESTAMP DEFAULT NOW()
        );
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("All tables created successfully.")

with DAG(
    dag_id="create_tables",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["setup"]
) as dag:
    PythonOperator(
        task_id="create_tables",
        python_callable=create_tables
    )