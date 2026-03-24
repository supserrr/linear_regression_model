# Linear Regression Model

## Mission

My mission is to use technology as a tool for inclusion and empowerment in Africa. I believe software should not only solve technical problems but also address the unique social challenges of our communities.

## Problem

This project tackles a **linear regression** use case aligned with that mission: **predicting used handheld device prices** from device and usage features. The goal is to support transparency and affordability in device markets—relevant to inclusion and access in communities where second-hand devices are often the primary path to connectivity. The use case is specific (used device pricing and features), is **not** generic, and is **not** the house-prediction example from class.

**Dataset:** [Used Handheld Device Data (Kaggle)](https://www.kaggle.com/datasets/ahsan81/used-handheld-device-data)

## Repository structure

| Path | Contents |
|------|----------|
| `summative/linear_regression/` | Task 1: `multivariate.ipynb`, `used_device_data.csv`, `output/` (model, scaler, metrics, plots) |
| `summative/API/` | Task 2: FastAPI — `POST /predict`, `GET /health`, `GET /metrics`, `/docs` |
| `summative/FlutterApp/` | Task 3: Flutter client (defaults to deployed API below) |

## Task 1 — Linear regression

Notebook: [`summative/linear_regression/multivariate.ipynb`](summative/linear_regression/multivariate.ipynb). Data cleaning, EDA, train/test split, **linear regression**; metrics on the test set (see notebook or `output/training_metrics.json`). Current `output/training_metrics.json` (linear model, test set): **test MSE ≈ 0.0526**, **test R² ≈ 0.8378** (re-run notebook/export if you retrain).

After changing preprocessing, from `summative/linear_regression/`: `python3 export_model_metadata.py` (updates `output/model_metadata.json` and `training_metrics.json`).

## Task 2 — API (deployed + Docker)

**Live API:** `https://linear-regression-model-0nn0.onrender.com` — [Swagger `/docs`](https://linear-regression-model-0nn0.onrender.com/docs), [`/health`](https://linear-regression-model-0nn0.onrender.com/health), [`/metrics`](https://linear-regression-model-0nn0.onrender.com/metrics), `POST /predict`. Free tier may cold-start (~30–60s).

**Docker Hub:** publish your container image here and fill the link in the table above. Typical run (adjust image name and ensure model files are available, e.g. mount or copy `summative/linear_regression/output/`):

```bash
docker pull <your-dockerhub-user>/<your-api-image>:<tag>
docker run -p 8000:8000 <your-dockerhub-user>/<your-api-image>:<tag>
```

**Local (no Docker):** `cd summative/API && python3 -m pip install -r requirements.txt && python3 -m uvicorn main:app --host 0.0.0.0 --port 8000` — docs at `http://127.0.0.1:8000/docs`. Artifacts: `../linear_regression/output/` (override with `MODEL_DIR`). scikit-learn **1.6.1** for pickles.

Render blueprint: [`render.yaml`](render.yaml).

## Task 3 — Flutter

```bash
cd summative/FlutterApp && flutter pub get && flutter run
```

Default API: `https://linear-regression-model-0nn0.onrender.com`. Local API: `flutter run --dart-define=API_BASE_URL=http://127.0.0.1:8000` (emulator: `http://10.0.2.2:8000`).

## Task 4 — Video

Show notebook/analysis, API (Docker or deployed), Flutter calling `/predict`, brief workflow. Guide: [docs/guides/video-demo-checklist.md](docs/guides/video-demo-checklist.md).
