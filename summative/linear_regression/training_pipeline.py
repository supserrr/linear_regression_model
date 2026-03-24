"""
Train LR / DecisionTree / RandomForest on the used-device pipeline (matches multivariate.ipynb).
Writes scaler, per-model pickles, best_model.pkl, model_metadata.json, training_metrics.json.

The linear model saved here is sklearn's LinearRegression (ordinary least squares). For the
assignment requirement to optimize a linear formulation with gradient descent, see
multivariate.ipynb: section "SGD (gradient descent)" and "## 6. Loss Curve" (SGDRegressor,
train vs test MSE per epoch, and the saved loss-curve figure).
"""
from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor

TARGET = "normalized_used_price"
REQUIRED_RAW_COLUMNS = [
    "device_brand",
    "os",
    "4g",
    "5g",
    "screen_size",
    "rear_camera_mp",
    "front_camera_mp",
    "internal_memory",
    "ram",
    "battery",
    "weight",
    "release_year",
    "days_used",
    "normalized_new_price",
    "normalized_used_price",
]


def _preprocess_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str], dict[str, float]]:
    df_model = df.copy()
    df_model["4g"] = df_model["4g"].map({"yes": 1, "no": 0})
    df_model["5g"] = df_model["5g"].map({"yes": 1, "no": 0})
    df_model["os"] = df_model["os"].map({"Android": 0, "iOS": 1})

    top_brands = df_model["device_brand"].value_counts().nlargest(10).index.tolist()
    df_model["device_brand"] = df_model["device_brand"].apply(
        lambda x: x if x in top_brands else "Other"
    )
    df_model = pd.get_dummies(df_model, columns=["device_brand"], drop_first=True)

    bool_cols = df_model.select_dtypes(include=["bool"]).columns
    df_model[bool_cols] = df_model[bool_cols].astype(int)

    num_cols = df_model.select_dtypes(include=["float64", "int64"]).columns
    for col in num_cols:
        df_model[col] = df_model[col].fillna(df_model[col].median())

    impute_medians = {c: float(df_model[c].median()) for c in df_model.select_dtypes(include=["float64", "int64"]).columns}

    features = [col for col in df_model.columns if col != TARGET]
    feature_medians = {k: impute_medians[k] for k in features}
    return df_model, top_brands, feature_medians


def train_from_csv(
    csv_path: Path,
    output_dir: Path,
    *,
    random_state: int = 42,
) -> dict[str, Any]:
    """
    Fit models, pick best by test MSE, persist artifacts under output_dir.
    Returns dict with keys: best_model_name, test_mse, test_r2, n_rows.
    """
    np.random.seed(random_state)
    df = pd.read_csv(csv_path)
    missing = [c for c in REQUIRED_RAW_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"CSV missing columns: {missing}")

    df_model, top_brands, feature_medians = _preprocess_dataframe(df)
    features = [col for col in df_model.columns if col != TARGET]
    x = df_model[features]
    y = df_model[TARGET]

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=random_state
    )

    numeric_features = x_train.select_dtypes(include=[np.number]).columns.tolist()
    scaler = StandardScaler()
    x_train_scaled = x_train.copy()
    x_test_scaled = x_test.copy()
    x_train_scaled[numeric_features] = scaler.fit_transform(x_train[numeric_features])
    x_test_scaled[numeric_features] = scaler.transform(x_test[numeric_features])

    lr_model = LinearRegression()
    lr_model.fit(x_train_scaled, y_train)
    lr_test_pred = lr_model.predict(x_test_scaled)
    lr_test_loss = mean_squared_error(y_test, lr_test_pred)
    lr_r2 = r2_score(y_test, lr_test_pred)

    tree_model = DecisionTreeRegressor(
        max_depth=8, min_samples_leaf=5, random_state=random_state
    )
    tree_model.fit(x_train_scaled, y_train)
    tree_test_pred = tree_model.predict(x_test_scaled)
    tree_test_loss = mean_squared_error(y_test, tree_test_pred)
    tree_r2 = r2_score(y_test, tree_test_pred)

    rf_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=random_state,
        n_jobs=-1,
    )
    rf_model.fit(x_train_scaled, y_train)
    rf_test_pred = rf_model.predict(x_test_scaled)
    rf_test_loss = mean_squared_error(y_test, rf_test_pred)
    rf_r2 = r2_score(y_test, rf_test_pred)

    best_test_mse = min(lr_test_loss, tree_test_loss, rf_test_loss)
    if best_test_mse == rf_test_loss:
        best_model, best_name = rf_model, "RandomForestRegressor"
    elif best_test_mse == tree_test_loss:
        best_model, best_name = tree_model, "DecisionTreeRegressor"
    else:
        best_model, best_name = lr_model, "LinearRegression"

    best_r2 = r2_score(
        y_test,
        best_model.predict(x_test_scaled),
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "target": TARGET,
        "feature_columns": list(x_train.columns),
        "top_brands": top_brands,
        "impute_medians": feature_medians,
    }
    with open(output_dir / "model_metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    metrics = {
        "model": best_name,
        "test_mse": float(best_test_mse),
        "test_r2": float(best_r2),
    }
    with open(output_dir / "training_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    with open(output_dir / "scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)
    with open(output_dir / "linear_regression_model.pkl", "wb") as f:
        pickle.dump(lr_model, f)
    with open(output_dir / "decision_tree_model.pkl", "wb") as f:
        pickle.dump(tree_model, f)
    with open(output_dir / "random_forest_model.pkl", "wb") as f:
        pickle.dump(rf_model, f)
    with open(output_dir / "best_model.pkl", "wb") as f:
        pickle.dump(best_model, f)

    return {
        "best_model_name": best_name,
        "test_mse": float(best_test_mse),
        "test_r2": float(best_r2),
        "n_rows": len(df),
        "linear_test_mse": float(lr_test_loss),
        "tree_test_mse": float(tree_test_loss),
        "rf_test_mse": float(rf_test_loss),
    }


def main() -> None:
    root = Path(__file__).resolve().parent
    csv_path = root / "used_device_data.csv"
    out = root / "output"
    result = train_from_csv(csv_path, out)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
