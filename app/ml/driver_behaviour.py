import joblib
import numpy as np
import pandas as pd
from pathlib import Path

MODEL_DIR = Path(__file__).parent.parent.parent / "models"

# Load model + scaler
_kmeans = joblib.load(MODEL_DIR / "kmeans_driver_behavior_model.joblib")
_scaler = joblib.load(MODEL_DIR / "standard_scaler_driver_behavior.joblib")

# Correct cluster mapping (based on train_kmeans_driver.py output)
CLUSTER_MAP = {
    1: "Economical",
    0: "Moderate",
    2: "Harsh"
}

# ONLY these features (IMPORTANT)
FEATURE_COLUMNS = [
    'Engine RPM [RPM]_std',
    'Engine RPM [RPM]_mad',
    'Vehicle Speed Sensor [km/h]_mad',
    'acceleration_std',
    'acceleration_range',
    'Absolute Throttle Position [%]_std'
]


def _compute_features(rpm, speed, throttle):
    rpm = np.array(rpm, dtype=float)
    speed = np.array(speed, dtype=float)
    throttle = np.array(throttle, dtype=float)

    # acceleration = diff(speed)
    acceleration = np.diff(speed, prepend=speed[0])

    def std(x): return float(np.std(x))
    def mad(x): return float(np.mean(np.abs(np.diff(x)))) if len(x) > 1 else 0.0
    def rng(x): return float(np.max(x) - np.min(x))

    features = {
        'Engine RPM [RPM]_std': std(rpm),
        'Engine RPM [RPM]_mad': mad(rpm),
        'Vehicle Speed Sensor [km/h]_mad': mad(speed),
        'acceleration_std': std(acceleration),
        'acceleration_range': rng(acceleration),
        'Absolute Throttle Position [%]_std': std(throttle)
    }

    return features


def predict_from_raw_window(
    rpm_values: list[float],
    speed_values: list[float],
    throttle_values: list[float],
) -> dict:

    features = _compute_features(rpm_values, speed_values, throttle_values)

    df = pd.DataFrame([features], columns=FEATURE_COLUMNS)

    scaled = _scaler.transform(df)
    label = int(_kmeans.predict(scaled)[0])

    return {
        "cluster_id": label,
        "behaviour_class": CLUSTER_MAP.get(label, "Unknown"),
        "features_debug": features  # 🔥 VERY IMPORTANT for debugging
    }