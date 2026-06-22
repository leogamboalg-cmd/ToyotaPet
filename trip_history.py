import json
import os
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
TRIPS_FILE = os.path.join(DATA_DIR, "trips.json")


def load_trips():
    """
    Load all completed trips.

    Returns an empty list when the file does not exist,
    is empty, or contains invalid JSON.
    """
    if not os.path.exists(TRIPS_FILE):
        return []

    try:
        with open(TRIPS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

    except (OSError, json.JSONDecodeError) as error:
        print(f"[Trip History] Could not load trips: {error}")

    return []


def save_trip(trip_data):
    """
    Add one completed trip to trips.json.
    """
    if not isinstance(trip_data, dict):
        print("[Trip History] Invalid trip data")
        return False

    os.makedirs(DATA_DIR, exist_ok=True)

    trips = load_trips()

    saved_trip = dict(trip_data)

    saved_trip["date"] = datetime.now().strftime(
        "%B %d, %Y %I:%M %p"
    )

    # The trip is finished, so don't store it as active.
    saved_trip["trip_active"] = False
    saved_trip["trip_paused"] = False

    # Newest trip first.
    trips.insert(0, saved_trip)

    try:
        temporary_file = TRIPS_FILE + ".tmp"

        with open(temporary_file, "w", encoding="utf-8") as file:
            json.dump(
                trips,
                file,
                indent=4,
            )

        os.replace(temporary_file, TRIPS_FILE)

        print(f"[Trip History] Saved trip to {TRIPS_FILE}")
        return True

    except OSError as error:
        print(f"[Trip History] Could not save trip: {error}")
        return False


def get_recent_trips(limit=3):
    """
    Return recent trips formatted for trips_screen.py.
    """
    trips = load_trips()
    recent = []

    for trip in trips[:limit]:
        recent.append(
            {
                "date": trip.get("date", "Unknown"),
                "distance": (
                    f"{float(trip.get('distance_miles', 0)):.2f} mi"
                ),
                "score": (
                    f"{float(trip.get('drive_score', 100)):.0f}/100"
                ),
            }
        )

    return recent
