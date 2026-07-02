import joblib
import numpy as np
from pathlib import Path

MODEL_DIR = Path(__file__).parent.parent.parent / "models"

# joblib.load() reads both .joblib and .pkl files identically — the
# extension is just a naming convention, not a different format. So
# these random_forest_health.pkl / scaler_health.pkl files (saved with
# joblib.dump) load exactly the same way as the .joblib driver-behavior
# artifacts above.
_rf_model = joblib.load(MODEL_DIR / "random_forest_health.pkl")
_scaler = joblib.load(MODEL_DIR / "scaler_health.pkl")

# Must match the feature order used at training time in train_rf_health.py
FEATURE_COLS = [
    "rpm", "throttle_pos", "map_kpa", "maf",
    "coolant_temp", "intake_air_temp", "ambient_temp", "pedal_d",
]


def classify_vehicle_health(telemetry: dict) -> dict:
    """
    telemetry: dict with keys matching FEATURE_COLS
    Returns: {"status": "Normal"|"Warning"|"Critical", "confidence": float}
    """
    missing = [c for c in FEATURE_COLS if c not in telemetry]
    if missing:
        raise ValueError(f"Missing required telemetry fields: {missing}")

    features = [[telemetry[c] for c in FEATURE_COLS]]
    features_scaled = _scaler.transform(features)
    class_probs = _rf_model.predict_proba(features_scaled)[0]
    predicted_class = _rf_model.classes_[int(np.argmax(class_probs))]
    confidence = float(np.max(class_probs))

    return {
        "status": str(predicted_class),
        "confidence": confidence,
        "probabilities": {
            cls: float(p) for cls, p in zip(_rf_model.classes_, class_probs)
        },
    }
