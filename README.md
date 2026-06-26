# DashBuddy OS

DashBuddy OS is a Pygame dashboard for car telemetry, trip tracking, trip scoring, and pet-style driving feedback. The main app runs from `main.py`; optional backend API code lives in `backend/`.

## Project Structure

- `main.py` - primary Pygame dashboard entry point
- `car_telemetry.py`, `mpg_calculator.py` - OBD-II telemetry helpers
- `trip_manager_solo.py`, `trip_history.py` - trip state and saved trip history
- `screens/` - dashboard screen drawing modules
- `assets/` - icons, sounds, and voice sample WAV files
- `voices/` - Piper voice model files
- `data/` - local trip history JSON
- `backend/` - optional Express API server
- `tools/diagnostics/` - manual OBD/audio test scripts
- `tools/reports/` - report and graph generation scripts
- `tools/experiments/` - alternate app experiments

## Run the App

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

The app can start without an OBD adapter; telemetry connection errors are shown in the console and the UI remains usable.

## Optional Backend

```powershell
cd backend
npm install
npm run dev
```

The backend listens on port `5000`.

## Tools

Generate trip graphs from `data/trips.json`:

```powershell
python tools/reports/make_trip_graphs.py
```

Manual hardware/audio probes are in `tools/diagnostics/`. They may require an OBD adapter, local serial port changes, or sound file path updates before use.
