import pandas as pd
import joblib
import json
from xgboost import XGBClassifier
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.preprocessing import StandardScaler

FEATURE_COLS = joblib.load("src/models/feature_cols.pkl")

def tune_model():
    df = pd.read_csv("data/processed/feature_matrix.csv")
    X = df[FEATURE_COLS].values
    y = df["breakout"].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    param_grid = {
        "n_estimators": [50, 100, 200],
        "max_depth": [2, 3, 4],
        "learning_rate": [0.05, 0.1, 0.2],
        "subsample": [0.8, 1.0]
    }

    base_model = XGBClassifier(
        scale_pos_weight=(y==0).sum() / y.sum(),
        eval_metric="logloss",
        random_state=42
    )

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    grid_search = GridSearchCV(
        base_model, param_grid,
        cv=cv, scoring="roc_auc",
        n_jobs=-1, verbose=1
    )

    grid_search.fit(X_scaled, y)

    print(f"\nBest params: {grid_search.best_params_}")
    print(f"Best ROC-AUC: {grid_search.best_score_:.3f}")

    # save tuned model
    joblib.dump(grid_search.best_estimator_, "src/models/xgb_model_tuned.pkl")
    joblib.dump(scaler, "src/models/scaler.pkl")

    with open("src/models/best_params.json", "w") as f:
        json.dump(grid_search.best_params_, f)

    print("Tuned model saved.")

if __name__ == "__main__":
    tune_model()