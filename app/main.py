from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from app.ml.driver_behaviour import predict_from_raw_window
from app.ml.health_classifier import classify_vehicle_health

app = FastAPI(title="ECU Guardian API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten later
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ UPDATED request model (removed accel_d & accel_e)
class WindowRequest(BaseModel):
    rpm_values: List[float]
    speed_values: List[float]
    throttle_values: List[float]
#Random

# Random Forest snapshot health classification request model
class HealthSnapshotRequest(BaseModel):
    rpm: float
    throttle_pos: float
    map_kpa: float
    maf: float
    coolant_temp: float
    intake_air_temp: float
    ambient_temp: float
    pedal_d: float

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/driver/predict")
def predict(body: WindowRequest):
    try:
        if len(body.rpm_values) < 5:
            raise HTTPException(status_code=400, detail="Not enough data points")

        result = predict_from_raw_window(
            body.rpm_values,
            body.speed_values,
            body.throttle_values
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/health/predict")
def predict_health(body: HealthSnapshotRequest):
    try:
        result = classify_vehicle_health(body.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))