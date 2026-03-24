"""FastAPI service for used-device normalized price prediction (best model from training)."""
from __future__ import annotations

import asyncio
import io
import json
import logging
import os
import sys
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Literal

import pandas as pd

_sys_lr = Path(__file__).resolve().parent.parent / "linear_regression"
if str(_sys_lr) not in sys.path:
    sys.path.insert(0, str(_sys_lr))

from training_pipeline import REQUIRED_RAW_COLUMNS, train_from_csv  # noqa: E402
from fastapi import FastAPI, File, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from prediction import Artifacts, load_artifacts, predict_from_raw

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_DEFAULT_DIR = Path(__file__).resolve().parent.parent / "linear_regression" / "output"
MODEL_DIR = Path(os.environ.get("MODEL_DIR", str(_DEFAULT_DIR))).resolve()
MODEL_FILE = os.environ.get("MODEL_FILE", "best_model.pkl")
LINEAR_REG_DATA_DIR = Path(__file__).resolve().parent.parent / "linear_regression"
CANONICAL_CSV = LINEAR_REG_DATA_DIR / "used_device_data.csv"

_DEFAULT_CORS = (
    "http://127.0.0.1:8000,http://localhost:8000,"
    "https://linear-regression-model-0nn0.onrender.com"
)
_cors_raw = os.environ.get("CORS_ORIGINS", _DEFAULT_CORS)
CORS_ORIGINS = [o.strip() for o in _cors_raw.split(",") if o.strip()]

_artifacts: Artifacts | None = None
_retrain_lock = threading.Lock()


def _reload_artifacts() -> None:
    global _artifacts
    _artifacts = load_artifacts(MODEL_DIR, MODEL_FILE)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        _reload_artifacts()
    except FileNotFoundError as e:
        logger.error("%s", e)
        raise
    yield


app = FastAPI(
    title="Used device price API",
    description="Predicts normalized used price; serves the best test-MSE model (RF / tree / linear).",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Retrain-Key", "Accept"],
)


class PredictRequest(BaseModel):
    device_brand: str = Field(..., max_length=128)
    os: Literal["Android", "iOS"]
    four_g: Literal["yes", "no"] = Field(alias="4g")
    five_g: Literal["yes", "no"] = Field(alias="5g")
    screen_size: float = Field(..., ge=5.0, le=31.0)
    rear_camera_mp: float = Field(..., ge=0.0, le=50.0)
    front_camera_mp: float = Field(..., ge=0.0, le=35.0)
    internal_memory: float = Field(..., ge=0.01, le=2048.0)
    ram: float = Field(..., ge=0.02, le=16.0)
    battery: float = Field(..., ge=400.0, le=10000.0)
    weight: float = Field(..., ge=60.0, le=900.0)
    release_year: int = Field(..., ge=2012, le=2021)
    days_used: int = Field(..., ge=80, le=1200)
    normalized_new_price: float = Field(..., ge=2.5, le=8.5)

    model_config = ConfigDict(populate_by_name=True)


class PredictResponse(BaseModel):
    normalized_used_price: float


class MetricsResponse(BaseModel):
    model: str
    test_mse: float
    test_r2: float


def _run_retrain_sync(
    raw: bytes,
    mode: Literal["replace", "append"],
) -> dict[str, Any]:
    with _retrain_lock:
        try:
            new_df = pd.read_csv(io.BytesIO(raw))
        except Exception as e:
            raise ValueError(f"Invalid CSV: {e}") from e

        missing = [c for c in REQUIRED_RAW_COLUMNS if c not in new_df.columns]
        if missing:
            raise ValueError(f"CSV missing columns: {missing}")

        if mode == "append" and CANONICAL_CSV.is_file():
            existing = pd.read_csv(CANONICAL_CSV)
            combined = pd.concat([existing, new_df], ignore_index=True)
            combined.to_csv(CANONICAL_CSV, index=False)
        else:
            CANONICAL_CSV.parent.mkdir(parents=True, exist_ok=True)
            new_df.to_csv(CANONICAL_CSV, index=False)

        result = train_from_csv(CANONICAL_CSV, MODEL_DIR)
        _reload_artifacts()
        return result


@app.get("/health")
def health() -> dict[str, str]:
    ok = _artifacts is not None
    return {"status": "ok" if ok else "not_ready"}


@app.get("/metrics", response_model=MetricsResponse)
def metrics() -> MetricsResponse:
    path = MODEL_DIR / "training_metrics.json"
    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="training_metrics.json not found; run training_pipeline",
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
    if _artifacts is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    raw = body.model_dump(by_alias=True)
    try:
        value = predict_from_raw(raw, _artifacts)
    except Exception:
        logger.exception("Prediction failed")
        raise HTTPException(
            status_code=500,
            detail="Prediction failed. Check inputs and server logs.",
        ) from None

    return PredictResponse(normalized_used_price=value)


@app.post("/retrain")
async def retrain(
    file: UploadFile = File(..., description="Training CSV (same schema as used_device_data.csv)"),
    mode: Literal["replace", "append"] = Query(
        "replace",
        description="replace: use upload as full dataset; append: add rows then retrain",
    ),
    x_retrain_key: str | None = Header(default=None, alias="X-Retrain-Key"),
) -> dict[str, Any]:
    key = os.environ.get("RETRAIN_API_KEY", "").strip()
    if key and x_retrain_key != key:
        raise HTTPException(status_code=403, detail="Invalid or missing X-Retrain-Key")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        result = await asyncio.to_thread(_run_retrain_sync, raw, mode)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception:
        logger.exception("Retrain failed")
        raise HTTPException(
            status_code=500,
            detail="Retrain failed. Check server logs.",
        ) from None

    return {"status": "ok", **result}
