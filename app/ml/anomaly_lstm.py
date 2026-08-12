import joblib
import numpy as np
import tensorflow as tf
from pathlib import Path

MODEL_DIR = Path(__file__).parent.parent.parent / "models"
WINDOW = 40

try:
    _model = tf.keras.models.load_model(MODEL_DIR / "lstm_autoencoder_finetuned.keras")
    _thresholds = joblib.load(MODEL_DIR / "lstm_thresholds_finetuned.joblib")
except Exception:
    _model = tf.keras.models.load_model(MODEL_DIR / "lstm_autoencoder.keras")
    _thresholds = joblib.load(MODEL_DIR / "lstm_thresholds.joblib")

_scaler = joblib.load(MODEL_DIR / "lstm_scaler.joblib")
FEATURES = joblib.load(MODEL_DIR / "lstm_features.joblib")


def classify_anomaly_window(rows: list[dict]) -> dict:
    """rows: list of WINDOW dicts, each with keys matching FEATURES, real units."""
    if len(rows) != WINDOW:
        raise ValueError(f"Expected exactly {WINDOW} rows, got {len(rows)}")

    raw = np.array([[r[f] for f in FEATURES] for r in rows], dtype=float)
    scaled = _scaler.transform(raw)

    recon = _model.predict(np.expand_dims(scaled, axis=0), verbose=0)[0]
    error = float(np.mean(np.abs(recon - scaled)))

    if error >= _thresholds["critical"]:
        status = "Critical"
    elif error >= _thresholds["warning"]:
        status = "Warning"
    else:
        status = "Normal"

    return {"status": status, "reconstruction_error": error, "thresholds": _thresholds}
