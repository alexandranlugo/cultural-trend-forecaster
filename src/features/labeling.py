import pandas as pd

def assign_breakout_labels(lastfm_df):
    """
    Automated labeling strategy:
    An artist is labeled a breakout (1) if they meet TWO conditions:
      1. listeners >= 1,500,000  (wide reach threshold)
      2. plays_per_listener >= 40 (depth/engagement threshold)

    This avoids purely popularity-based labeling by requiring both
    breadth (many listeners) AND depth (fans who replay obsessively).
    Artists with high listeners but low replays are likely one-hit
    wonders. Artists with high replays but few listeners are cult
    favorites not yet crossed over. True breakouts have both.
    """
    df = lastfm_df.copy()

    df["breakout"] = (
        (df["listeners"] >= 1_500_000) &
        (df["plays_per_listener"] >= 40)
    ).astype(int)

    print("Label distribution:")
    print(df["breakout"].value_counts())
    print("\nBreakout artists:")
    print(df[df["breakout"]==1]["artist_name"].tolist())
    print("\nNon-breakout artists:")
    print(df[df["breakout"]==0]["artist_name"].tolist())

    return df

if __name__ == "__main__":
    df = pd.read_csv("data/raw/lastfm_artists.csv")
    # keep most recent record per artist
    df = df.sort_values("fetched_at").drop_duplicates("artist_name", keep="last")
    labeled = assign_breakout_labels(df)
    labeled.to_csv("data/processed/labeled_artists.csv", index=False)
    print("\nSaved to data/processed/labeled_artists.csv")