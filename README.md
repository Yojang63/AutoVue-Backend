# ECU Guardian — Merged Backend (ML API + OBD-II Simulator)

Single FastAPI app combining:
1. **ML API** (`app/ml/`) — driver behaviour (KMeans) + vehicle health classification (Random Forest)
2. **OBD-II Simulator** (`app/simulator/`) — streams a recorded dataset as if it were a live vehicle

Merged into one process/one deployment for the demo phase (see reasoning
below). Both halves are still cleanly separated in code, so splitting the
simulator into its own service later is just deploying `app/simulator/`
on its own and pointing the frontend at two URLs instead of one.

## Why merged, not two services

On a free Render/Railway tier, two separate services means two independent
cold starts — if either one is asleep when your frontend calls it during a
live demo, you eat a 30-60s hang. One merged service means one wake-up,
one URL, no CORS setup between "your own two backends." The simulator
doesn't need to be its own service until you're actually replacing it with
real hardware or scaling past a single demo vehicle.

## Route map (verified no collisions)

| Route | Source | Purpose |
|---|---|---|
| `GET /health` | shared | health check |
| `POST /api/driver/predict` | ML | driver behaviour classification |
| `POST /api/health/predict` | ML | vehicle health snapshot classification |
| `GET /api/datasets`, `POST /api/upload`, etc. | Simulator | dataset management |
| `POST /api/start`, `/pause`, `/resume`, ... | Simulator | playback control |
| `GET /api/live-data`, `/api/status`, `/api/history` | Simulator | current state |
| `WS /api/ws/live`, `/api/ws/logs` | Simulator | live streaming |
| `GET /` | Simulator | control dashboard |
| `GET /docs` | FastAPI | interactive API docs (Swagger) — use this to test POST endpoints, since typing a URL in the browser only ever sends GET |

## Run locally
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python run.py
# or: uvicorn app.main:app --reload --port 8000
```
Visit `http://localhost:8000` for the simulator dashboard, or
`http://localhost:8000/docs` to test the ML endpoints interactively.

## Deploy (Render, free)
Same steps as before — this repo has one Dockerfile at the root now:
1. Push to GitHub.
2. Render → New → Web Service → connect repo → Free instance → Create.
3. One URL for everything: ML endpoints, simulator, and dashboard.

Remember: free-tier services sleep after ~15 min idle. Warm it up a few
minutes before your viva by just opening the dashboard URL.

## Testing POST endpoints
Since a browser address bar can only send GET, use one of:
- `https://your-app.onrender.com/docs` → Swagger UI → "Try it out"
- `curl -X POST .../api/health/predict -H "Content-Type: application/json" -d '{...}'`
- Postman / Insomnia
- The dashboard's own JS (already does this correctly for simulator controls)

## Next steps once this is deployed and stable
- Wire the simulator's live data into the ML endpoints automatically
  (right now they're independent — the simulator streams telemetry, but
  nothing calls `/api/health/predict` on each tick yet). That's the piece
  that turns "two APIs that happen to coexist" into an actual live
  health-monitoring pipeline.
- Add the missing models from the report (anomaly detection, VHS score,
  RUL, fuel efficiency) — see earlier roadmap.
