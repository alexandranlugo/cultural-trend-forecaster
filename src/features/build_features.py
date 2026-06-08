import pandas as pd

def build_feature_matrix():
    # load all data sources
    lastfm = pd.read_csv("data/processed/labeled_artists.csv")
    youtube = pd.read_csv("data/raw/youtube_videos.csv")
    sentiment = pd.read_csv("data/processed/sentiment_features.csv")

    # --- Last.fm features ---
    lastfm_features = lastfm[[
        "artist_name", "listeners", "playcount",
        "plays_per_listener", "breakout"
    ]].copy()

    # log-transform skewed count features
    import numpy as np
    lastfm_features["log_listeners"] = np.log1p(lastfm_features["listeners"])
    lastfm_features["log_playcount"] = np.log1p(lastfm_features["playcount"])

    # --- YouTube features ---
    yt_agg = youtube.groupby("artist_name").agg(
        total_views=("view_count", "sum"),
        avg_views_per_day=("views_per_day", "mean"),
        max_views_per_day=("views_per_day", "max"),
        total_likes=("like_count", "sum"),
        total_comments=("comment_count", "sum"),
        video_count=("video_id", "count")
    ).reset_index()

    # engagement rate: likes + comments relative to views
    yt_agg["engagement_rate"] = (
        (yt_agg["total_likes"] + yt_agg["total_comments"]) /
        yt_agg["total_views"].replace(0, 1)
    ).round(4)

    yt_agg["log_total_views"] = np.log1p(yt_agg["total_views"])
    yt_agg["log_avg_vpd"] = np.log1p(yt_agg["avg_views_per_day"])

    # --- merge everything ---
    features = lastfm_features.merge(yt_agg, on="artist_name", how="left")
    features = features.merge(
        sentiment[["artist_name","headline_count","sentiment_score","avg_sentiment_confidence"]],
        on="artist_name", how="left"
    )

    # fill missing values for artists with no YouTube/news data
    features = features.fillna(0)

    print(f"Feature matrix shape: {features.shape}")
    print(f"Breakout distribution:\n{features['breakout'].value_counts()}")
    print(f"\nFeatures: {[c for c in features.columns if c not in ['artist_name','breakout']]}")

    features.to_csv("data/processed/feature_matrix.csv", index=False)
    print("\nSaved to data/processed/feature_matrix.csv")
    return features

if __name__ == "__main__":
    build_feature_matrix()