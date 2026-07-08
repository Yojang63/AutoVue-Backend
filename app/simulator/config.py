"""
Central configuration. Every setting can be overridden via an environment
variable (or a .env file - see .env.example), so the same code runs
unchanged locally and on a cloud host like Render.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Where bundled sample datasets live (shipped with the repo)
DATASETS_DIR = Path(os.getenv("DATASETS_DIR", BASE_DIR / "datasets"))
# Where user-uploaded datasets are stored (should be a persistent volume in prod)
UPLOADS_DIR = Path(os.getenv("UPLOADS_DIR", BASE_DIR / "uploads"))

DATASETS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Default playback tick interval (seconds) used when the dataset's own
# timestamps can't be trusted (e.g. first row, or a timestamp wraparound)
DEFAULT_TICK_SECONDS = float(os.getenv("DEFAULT_TICK_SECONDS", "0.1"))

# Safety clamp: never wait longer than this between rows, even if the
# dataset's timestamps imply a bigger gap (avoids the simulator appearing
# to "hang" because of a bad timestamp).
MAX_TICK_SECONDS = float(os.getenv("MAX_TICK_SECONDS", "2.0"))

# How many recent rows to keep in memory for GET /api/history
HISTORY_BUFFER_SIZE = int(os.getenv("HISTORY_BUFFER_SIZE", "500"))

# Missing-value handling strategy: "ffill" (forward-fill then back-fill),
# "zero" (fill with 0), or "keep_null" (leave as null - frontend must handle it)
MISSING_VALUE_STRATEGY = os.getenv("MISSING_VALUE_STRATEGY", "ffill")

# Allowed playback speed multipliers (dashboard slider is restricted to these)
ALLOWED_SPEEDS = [0.5, 1, 2, 5, 10]

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
