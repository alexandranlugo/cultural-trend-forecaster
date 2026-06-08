# cultural-trend-forecaster

## Pipeline Architecture

This project uses Apache Airflow to orchestrate a daily data pipeline
across three sources: Last.fm, YouTube Data API, and News API.

### Data Flow
Last.fm API → lastfm_daily DAG → PostgreSQL (lastfm_artists)
YouTube API → youtube_daily DAG → PostgreSQL (youtube_videos)
News API    → news_daily DAG   → PostgreSQL (news_headlines)

### Data Quality Checks
- Null filtering: records missing key fields are skipped and logged
- Deduplication: YouTube videos keyed on video_id, news on URL
- Zero-value filtering: artists with 0 listeners are excluded

### Schedule
All DAGs run on a @daily schedule. The Airflow scheduler
is managed via Docker Compose with a PostgreSQL metadata backend.

### Running Locally
1. cd airflow && docker compose up -d
2. Open http://localhost:8080 (admin/admin)
3. Trigger create_tables once, then enable the three daily DAGs