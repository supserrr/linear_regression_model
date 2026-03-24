"""Build feature matrix rows matching multivariate.ipynb training pipeline."""
from __future__ import annotations

from typing import Any, Mapping

import pandas as pd


def build_feature_row(
    raw: Mapping[str, Any],
    feature_columns: list[str],
    top_brands: list[str],
    impute_medians: Mapping[str, float],
) -> pd.DataFrame:
    """
    raw keys: device_brand, os ('Android'|'iOS'), 4g, 5g ('yes'|'no'),
    screen_size, rear_camera_mp, front_camera_mp, internal_memory, ram,
    battery, weight, release_year, days_used, normalized_new_price
    """
    brand = raw["device_brand"]
    if brand not in top_brands:
        brand = "Other"

    row: dict[str, float] = {c: float(impute_medians[c]) for c in feature_columns}

    row["os"] = 0.0 if raw["os"] == "Android" else 1.0
    row["4g"] = 1.0 if raw["4g"] == "yes" else 0.0
    row["5g"] = 1.0 if raw["5g"] == "yes" else 0.0

    for key in (
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
    ):
        row[key] = float(raw[key])

    for c in feature_columns:
        if c.startswith("device_brand_"):
            row[c] = 0.0

    col_name = f"device_brand_{brand}"
    if col_name in row:
        row[col_name] = 1.0

    df = pd.DataFrame([row], columns=feature_columns)
    return df


def predict_array(
    features: pd.DataFrame,
    scaler: Any,
    model: Any,
    feature_columns: list[str],
) -> float:
    x = features[feature_columns]
    x_scaled = scaler.transform(x)
    pred = model.predict(x_scaled)
    return float(pred[0])
