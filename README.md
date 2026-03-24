# Linear Regression Model

## Mission

My mission is to use technology as a tool for inclusion and empowerment in Africa. I believe software should not only solve technical problems but also address the unique social challenges of our communities.

## Problem

This project tackles a **linear regression** use case aligned with that mission: **predicting used handheld device prices** from device and usage features. The goal is to support transparency and affordability in device markets—relevant to inclusion and access in communities where second-hand devices are often the primary path to connectivity. The use case is specific (used device pricing and features), is **not** generic, and is **not** the house-prediction example from class.

**Dataset:** [Used Handheld Device Data (Kaggle)](https://www.kaggle.com/datasets/ahsan81/used-handheld-device-data)

## Repository structure

- **summative/linear_regression/** — Task 1: notebook (`multivariate.ipynb`), dataset (`used_device_data.csv`), training outputs under `output/` (models, scaler, plots, `model_metadata.json`).
- **summative/API/** — Task 2: FastAPI service that loads `best_model.pkl`, `scaler.pkl`, and `model_metadata.json`, exposes `/predict` and `/health`, OpenAPI at `/docs`.
- **summative/FlutterApp/** — Task 3: Flutter app with a form that POSTs to the API and shows the predicted normalized used price.

## API metadata export (after training)

The API needs column order and imputation values from training. From `summative/linear_regression/` run:

```bash
python3 export_model_metadata.py
```

This writes `output/model_metadata.json`. Re-run whenever you change preprocessing or retrain. The notebook includes a short section pointing to this script.

## Run the API (Task 2)

From the repo root (or `summative/API/`):

```bash
cd summative/API
python3 -m pip install -r requirements.txt
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Use those as **two separate lines**. If `pip` fails with `Invalid requirement: '#'`, something on the install line was passed as an extra argument (for example a trailing `# ...` that your shell did not treat as a comment). Run only `python3 -m pip install -r requirements.txt` with no other tokens on that line.

- **Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Artifacts path:** by default `../linear_regression/output/`. Override with `MODEL_DIR` if you move the files.

Pickles were saved with scikit-learn **1.6.1**. If you see unpickling warnings, use a matching version (see `requirements.txt`).

## Run the Flutter app (Task 3)

```bash
cd summative/FlutterApp
flutter pub get
flutter run
```

**API base URL:** if you do not pass `API_BASE_URL`, the app defaults to **`http://10.0.2.2:8000` on Android** (emulator alias for your host machine) and **`http://127.0.0.1:8000` elsewhere** (iOS Simulator, desktop, etc.). Override anytime with `--dart-define`:

| Environment | Example |
|-------------|---------|
| Physical phone on same Wi‑Fi as your laptop | `flutter run --dart-define=API_BASE_URL=http://YOUR_LAN_IP:8000` (find IP in System Settings / `ipconfig`) |

**Connection refused to `127.0.0.1` on Android emulator** means the app was talking to the emulator itself, not your Mac; use the default above or `10.0.2.2` explicitly. Keep the API bound with `--host 0.0.0.0` so the emulator can reach it.

The app enables cleartext HTTP on Android for local development; use HTTPS in production.

## Deploy the API on Render

This repo includes [`render.yaml`](render.yaml) for a **Web Service** with **root directory** `summative/API`.

1. **Commit artifacts** so the deploy has models: add and push `summative/linear_regression/output/` (`best_model.pkl`, `scaler.pkl`, `model_metadata.json`, etc.). Render builds from Git; untracked files are not deployed.
2. In [Render](https://dashboard.render.com): **New** → **Blueprint** → connect this repository and apply the blueprint (or **New** → **Web Service**, set **Root Directory** to `summative/API`, **Build** `pip install -r requirements.txt`, **Start** `uvicorn main:app --host 0.0.0.0 --port $PORT`, **Health Check Path** `/health`).
3. After deploy, open `https://<your-service>.onrender.com/docs`. Point the Flutter app at it:

   ```bash
   flutter run --dart-define=API_BASE_URL=https://<your-service>.onrender.com
   ```

**Note:** With `rootDir: summative/API`, Render only **auto-rebuilds** when files under `summative/API/` change. If you update only `summative/linear_regression/output/`, trigger a **manual deploy** (or touch a file under `summative/API/`) so the new artifacts ship.

On the **free** tier the service **spins down** after idle time; the first request after sleep can take ~30–60s (cold start).

## Optional: other hosts

You can also run the same FastAPI app on Railway, Fly.io, etc.; set `MODEL_DIR` if artifacts are not beside `summative/linear_regression/output/` in the checkout, and use `API_BASE_URL` for the Flutter client.

## Task 4 (video)

Record the API running, the Flutter app calling `/predict`, and a short explanation of the regression workflow and metrics from the notebook.
