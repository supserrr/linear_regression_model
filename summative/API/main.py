"""FastAPI service for used-device normalized price prediction (linear regression)."""
from __future__ import annotations

import json
import logging
import os
import pickle
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from preprocess import build_feature_row, predict_array

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_DEFAULT_DIR = Path(__file__).resolve().parent.parent / "linear_regression" / "output"
MODEL_DIR = Path(os.environ.get("MODEL_DIR", str(_DEFAULT_DIR))).resolve()
MODEL_FILE = os.environ.get("MODEL_FILE", "linear_regression_model.pkl")

_meta: dict[str, Any] | None = None
_scaler: Any = None
_model: Any = None


def _load_artifacts() -> None:
    global _meta, _scaler, _model
    meta_path = MODEL_DIR / "model_metadata.json"
    scaler_path = MODEL_DIR / "scaler.pkl"
    model_path = MODEL_DIR / MODEL_FILE

    for p in (meta_path, scaler_path, model_path):
        if not p.is_file():
            raise FileNotFoundError(f"Missing artifact: {p}")

    with open(meta_path, encoding="utf-8") as f:
        _meta = json.load(f)

    with open(scaler_path, "rb") as f:
        _scaler = pickle.load(f)

    with open(model_path, "rb") as f:
        _model = pickle.load(f)

    logger.info("Loaded model artifacts from %s (%s)", MODEL_DIR, MODEL_FILE)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        _load_artifacts()
    except FileNotFoundError as e:
        logger.error("%s", e)
        raise
    yield


app = FastAPI(
    title="Used device price API",
    description="Predicts normalized used price from device features (linear regression).",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictRequest(BaseModel):
    device_brand: str
    os: Literal["Android", "iOS"]
    four_g: Literal["yes", "no"] = Field(alias="4g")
    five_g: Literal["yes", "no"] = Field(alias="5g")
    screen_size: float
    rear_camera_mp: float
    front_camera_mp: float
    internal_memory: float
    ram: float
    battery: float
    weight: float
    release_year: int
    days_used: int
    normalized_new_price: float

    model_config = ConfigDict(populate_by_name=True)


class PredictResponse(BaseModel):
    normalized_used_price: float


class MetricsResponse(BaseModel):
    model: str
    test_mse: float
    test_r2: float


@app.get("/health")
def health() -> dict[str, str]:
    ok = _meta is not None and _scaler is not None and _model is not None
    return {"status": "ok" if ok else "not_ready"}


@app.get("/metrics", response_model=MetricsResponse)
def metrics() -> MetricsResponse:
    path = MODEL_DIR / "training_metrics.json"
    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="training_metrics.json not found; run export_model_metadata.py",
        )
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return MetricsResponse(
        model=str(data["model"]),
        test_mse=float(data["test_mse"]),
        test_r2=float(data["test_r2"]),
    )


@app.post("/predict", response_model=PredictResponse)
def predict(body: PredictRequest) -> PredictResponse:
    if _meta is None or _scaler is None or _model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    raw = body.model_dump(by_alias=True)
    try:
        features = build_feature_row(
            raw,
            _meta["feature_columns"],
            _meta["top_brands"],
            _meta["impute_medians"],
        )
        value = predict_array(
            features,
            _scaler,
            _model,
            _meta["feature_columns"],
        )
    except Exception:
        logger.exception("Prediction failed")
        raise HTTPException(
            status_code=500,
            detail="Prediction failed. Check inputs and server logs.",
        ) from None

    return PredictResponse(normalized_used_price=value)
