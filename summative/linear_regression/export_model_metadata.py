"""
Export training metadata and test metrics for the FastAPI predictor.
Delegates full training + artifact export to training_pipeline (matches multivariate.ipynb).
Run from this directory: python3 export_model_metadata.py
"""
from __future__ import annotations

from pathlib import Path

from training_pipeline import train_from_csv

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
CSV_PATH = Path(__file__).resolve().parent / "used_device_data.csv"


def main() -> None:
    result = train_from_csv(CSV_PATH, OUTPUT_DIR)
    print(
        f"Wrote model_metadata.json, training_metrics.json, pickles under {OUTPUT_DIR} "
        f"(best: {result['best_model_name']}, test_mse={result['test_mse']:.6f}, "
        f"n_rows={result['n_rows']})"
    )


if __name__ == "__main__":
    main()
