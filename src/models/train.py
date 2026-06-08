import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.preprocessing import StandardScaler
import joblib
import json

FEATURE_COLS = [
    "log_listeners", "log_playcount", "plays_per_listener",
    "log_total_views", "log_avg_vpd", "max_views_per_day",
    "engagement_rate", "video_count",
    "headline_count", "sentiment_score", "avg_sentiment_confidence"
]

def train_model():
    df = pd.read_csv("data/processed/feature_matrix.csv")

    X = df[FEATURE_COLS].values
    y = df["breakout"].values

    print(f"Training on {len(df)} artists")
    print(f"Breakout: {y.sum()} | Non-breakout: {(y==0).sum()}")

    # scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # XGBoost with class weighting for imbalanced labels
    model = XGBClassifier(
        n_estimators=100,
        max_depth=3,
        learning_rate=0.1,
        scale_pos_weight=(y==0).sum() / y.sum(),
        eval_metric="logloss",
        random_state=42
    )

    # stratified k-fold cross validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_results = cross_validate(
        model, X_scaled, y, cv=cv,
        scoring=["accuracy", "precision", "recall", "roc_auc"],
        return_train_score=True
    )

    print("\n=== Cross-Validation Results ===")
    for metric in ["accuracy", "precision", "recall", "roc_auc"]:
        scores = cv_results[f"test_{metric}"]
        print(f"{metric:12}: {scores.mean():.3f} (+/- {scores.std():.3f})")

    # fit on full dataset and save
    model.fit(X_scaled, y)

    # predict probabilities for all artists
    df["breakout_probability"] = model.predict_proba(X_scaled)[:, 1].round(3)
    df["predicted_breakout"] = model.predict(X_scaled)

    print("\n=== Breakout Probability Rankings ===")
    ranking = df[["artist_name","breakout_probability","breakout"]].sort_values(
        "breakout_probability", ascending=False)
    print(ranking.to_string(index=False))

    # save model and scaler
    joblib.dump(model, "src/models/xgb_model.pkl")
    joblib.dump(scaler, "src/models/scaler.pkl")
    joblib.dump(FEATURE_COLS, "src/models/feature_cols.pkl")

    # save predictions
    df.to_csv("data/processed/predictions.csv", index=False)

    # save cv metrics for dashboard later
    metrics = {m: round(cv_results[f"test_{m}"].mean(), 3) for m in
               ["accuracy","precision","recall","roc_auc"]}
    with open("src/models/metrics.json", "w") as f:
        json.dump(metrics, f)

    print(f"\nModel saved. Metrics: {metrics}")
    return model, scaler

if __name__ == "__main__":
    train_model()