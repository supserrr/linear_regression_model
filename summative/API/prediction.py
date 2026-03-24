"""Load model artifacts and run inference (used by FastAPI routes)."""
from __future__ import annotations

import json
import logging
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from preprocess import build_feature_row, predict_array

logger = logging.getLogger(__name__)


@dataclass
class Artifacts:
    meta: dict[str, Any]
    scaler: Any
    model: Any


def load_artifacts(model_dir: Path, model_file: str) -> Artifacts:
    meta_path = model_dir / "model_metadata.json"
    scaler_path = model_dir / "scaler.pkl"
    model_path = model_dir / model_file

    for p in (meta_path, scaler_path, model_path):
        if not p.is_file():
            raise FileNotFoundError(f"Missing artifact: {p}")

    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)

    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)

    with open(model_path, "rb") as f:
        model = pickle.load(f)

    logger.info("Loaded model artifacts from %s (%s)", model_dir, model_file)
    return Artifacts(meta=meta, scaler=scaler, model=model)


def predict_from_raw(raw: Mapping[str, Any], art: Artifacts) -> float:
    features = build_feature_row(
        raw,
        art.meta["feature_columns"],
        art.meta["top_brands"],
        art.meta["impute_medians"],
    )
    return predict_array(
        features,
        art.scaler,
        art.model,
        art.meta["feature_columns"],
    )
