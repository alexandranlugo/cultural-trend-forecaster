import pandas as pd
import shap
import joblib
import matplotlib.pyplot as plt
import os

def explain_model():
    model = joblib.load("src/models/xgb_model.pkl")
    scaler = joblib.load("src/models/scaler.pkl")
    feature_cols = joblib.load("src/models/feature_cols.pkl")

    df = pd.read_csv("data/processed/feature_matrix.csv")
    X = scaler.transform(df[feature_cols].values)

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    os.makedirs("data/processed/plots", exist_ok=True)

    # global feature importance
    plt.figure(figsize=(10, 6))
    shap.summary_plot(
        shap_values, X,
        feature_names=feature_cols,
        show=False
    )
    plt.tight_layout()
    plt.savefig("data/processed/plots/shap_summary.png", dpi=150)
    plt.close()
    print("Saved SHAP summary plot.")

    # per-artist explanation
    shap_df = pd.DataFrame(shap_values, columns=feature_cols)
    shap_df["artist_name"] = df["artist_name"].values
    shap_df.to_csv("data/processed/shap_values.csv", index=False)

    # print top drivers for top 3 predicted breakouts
    predictions = pd.read_csv("data/processed/predictions.csv")
    top3 = predictions.nlargest(3, "breakout_probability")["artist_name"].tolist()

    for artist in top3:
        idx = df[df["artist_name"]==artist].index[0]
        top_features = pd.Series(
            dict(zip(feature_cols, shap_values[idx]))
        ).abs().sort_values(ascending=False).head(3)
        print(f"\n{artist} — top drivers:")
        for feat, val in top_features.items():
            print(f"  {feat}: {val:.3f}")

if __name__ == "__main__":
    explain_model()