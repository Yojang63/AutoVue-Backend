"""
Merged entrypoint: runs the ECU Guardian ML API (driver behaviour + health
classification) and the OBD-II simulator (dataset playback + streaming) in
a single FastAPI app / single process / single Render service.

Why merged (see chat discussion): avoids double cold-starts on Render's
free tier and keeps one URL for the frontend. The simulator lives under
app/simulator/ as a self-contained package with its own router - splitting
it back out into its own service later is just deploying that package
separately and pointing the frontend at two URLs instead of one; no
internal rewrite needed.

Route map (no collisions):
  /health                     - shared health check
  /api/driver/predict         - ML: driver behaviour (KMeans)
  /api/health/predict         - ML: vehicle health classification (RF)
  /api/datasets, /api/upload,
  /api/start, /api/status,
  /api/live-data, /api/ws/live, ...  - simulator (see app/simulator/api/routes.py)
  /                            - simulator control dashboard
"""
import asyncio
import logging
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.ml.driver_behaviour import predict_from_raw_window
from app.ml.health_classifier import classify_vehicle_health

from app.simulator.api.routes import router as simulator_router
from app.simulator.api.websocket import telemetry_manager, log_manager
from app.simulator.services.simulator import simulator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ecu_guardian")

app = FastAPI(title="ECU Guardian API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before real production use
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- ML endpoints (unchanged from the original backend) ----------------

class WindowRequest(BaseModel):
    rpm_values: List[float]
    speed_values: List[float]
    throttle_values: List[float]


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
        return predict_from_raw_window(body.rpm_values, body.speed_values, body.throttle_values)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/health/predict")
def predict_health(body: HealthSnapshotRequest):
    try:
        return classify_vehicle_health(body.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------- Simulator (dataset playback + streaming) ----------------

app.include_router(simulator_router)


async def _on_telemetry(payload: dict):
    await telemetry_manager.broadcast_json(payload)


def _on_log(entry: dict):
    coro = log_manager.broadcast_json(entry)
    try:
        asyncio.get_running_loop()
        asyncio.create_task(coro)
    except RuntimeError:
        coro.close()


simulator.subscribe(_on_telemetry)
simulator.subscribe_logs(_on_log)


@app.on_event("startup")
async def on_startup():
    try:
        simulator.load_dataset()
        logger.info("Simulator: default dataset pre-loaded. POST /api/start to begin streaming.")
    except ValueError as e:
        logger.warning("Simulator: no dataset available at startup: %s", e)


@app.get("/")
def serve_dashboard():
    return FileResponse("app/static/dashboard.html")


app.mount("/static", StaticFiles(directory="app/static"), name="static")
