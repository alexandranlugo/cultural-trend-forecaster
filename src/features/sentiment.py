import pandas as pd
from transformers import pipeline
from datetime import datetime

def compute_sentiment_features(news_df):
    """
    Uses HuggingFace's distilbert-base-uncased-finetuned-sst-2-english
    to score each headline as POSITIVE or NEGATIVE.
    We then compute per-artist:
      - sentiment_score: % of headlines that are positive (0 to 1)
      - headline_count: total press coverage volume
      - sentiment_momentum: proxy for buzz quality, not just quantity
    """
    print("Loading sentiment model...")
    sentiment_pipe = pipeline(
        "sentiment-analysis",
        model="distilbert-base-uncased-finetuned-sst-2-english",
        truncation=True,
        max_length=512
    )

    df = news_df.copy()
    df = df.dropna(subset=["headline"])

    print(f"Scoring {len(df)} headlines...")
    results = sentiment_pipe(df["headline"].tolist(), batch_size=32)

    df["sentiment_label"] = [r["label"] for r in results]
    df["sentiment_confidence"] = [r["score"] for r in results]
    df["is_positive"] = (df["sentiment_label"] == "POSITIVE").astype(int)

    # aggregate per artist
    agg = df.groupby("artist_name").agg(
        headline_count=("headline", "count"),
        positive_headlines=("is_positive", "sum"),
        avg_sentiment_confidence=("sentiment_confidence", "mean")
    ).reset_index()

    agg["sentiment_score"] = (
        agg["positive_headlines"] / agg["headline_count"]
    ).round(3)

    print(agg[["artist_name","headline_count","sentiment_score"]].sort_values(
        "sentiment_score", ascending=False).to_string(index=False))

    return agg

if __name__ == "__main__":
    news_df = pd.read_csv("data/raw/news_headlines.csv")
    features = compute_sentiment_features(news_df)
    features.to_csv("data/processed/sentiment_features.csv", index=False)
    print("\nSaved to data/processed/sentiment_features.csv")