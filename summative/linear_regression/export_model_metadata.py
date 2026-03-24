"""
One-time export of training metadata for the FastAPI predictor.
Replicates preprocessing in multivariate.ipynb (random_state=42).
Run from this directory: python export_model_metadata.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
CSV_PATH = Path(__file__).resolve().parent / "used_device_data.csv"


def main() -> None:
    np.random.seed(42)
    df = pd.read_csv(CSV_PATH)

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
    impute_medians = {c: float(df_model[c].median()) for c in num_cols}

    for col in num_cols:
        df_model[col] = df_model[col].fillna(df_model[col].median())

    target = "normalized_used_price"
    features = [col for col in df_model.columns if col != target]
    x = df_model[features]
    y = df_model[target]
    x_train, _x_test, _y_train, _y_test = train_test_split(
        x, y, test_size=0.2, random_state=42
    )

    feature_medians = {k: impute_medians[k] for k in features}

    meta = {
        "target": target,
        "feature_columns": list(x_train.columns),
        "top_brands": top_brands,
        "impute_medians": feature_medians,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / "model_metadata.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"Wrote {out_path} ({len(meta['feature_columns'])} features)")


if __name__ == "__main__":
    main()
