import json
from pathlib import Path

import matplotlib.pyplot as plt


ROOT_DIR = Path(__file__).resolve().parents[2]

# Change this if your data file has a different name.
DATA_FILE = ROOT_DIR / "data" / "trips.json"

# All generated graph images will be placed here.
OUTPUT_FOLDER = ROOT_DIR / "trip_graphs"


def load_trips(file_path):
    """
    Open the JSON file and return the list of saved trips.
    """
    if not file_path.exists():
        raise FileNotFoundError(
            f"Could not find {file_path.resolve()}\n"
            "Place this script in the same folder as your JSON file, "
            "or change DATA_FILE at the top of the script."
        )

    with file_path.open("r", encoding="utf-8") as file:
        trips = json.load(file)

    if not isinstance(trips, list):
        raise ValueError("The JSON file must contain a list of trips.")

    return trips


def safe_filename(text):
    """
    Convert a trip date into a filename-safe string.
    """
    return (
        str(text)
        .replace(":", "-")
        .replace("/", "-")
        .replace(",", "")
        .replace(" ", "_")
    )


def make_speed_graph(trip, trip_number, output_folder):
    """
    Create a line graph using the trip's speed_history list.
    """
    speed_history = trip.get("speed_history", [])

    if not speed_history:
        print(f"Trip {trip_number}: no speed history, skipping graph.")
        return

    # Your current file appears to save roughly one sample per second.
    sample_numbers = list(range(len(speed_history)))

    trip_date = trip.get("date", f"Trip {trip_number}")
    distance = trip.get("distance_miles", 0)
    average_speed = trip.get("average_speed", 0)
    maximum_speed = trip.get("maximum_speed", 0)
    score = trip.get("drive_score", trip.get("score", 0))

    plt.figure(figsize=(12, 6))
    plt.plot(sample_numbers, speed_history, linewidth=2)

    plt.title(
        f"Trip {trip_number} Speed History\n"
        f"{trip_date}"
    )
    plt.xlabel("Sample number")
    plt.ylabel("Speed (MPH)")
    plt.grid(True, alpha=0.3)

    information = (
        f"Distance: {distance:.2f} miles\n"
        f"Average speed: {average_speed:.1f} MPH\n"
        f"Maximum speed: {maximum_speed:.1f} MPH\n"
        f"Drive score: {score}"
    )

    plt.text(
        0.99,
        0.97,
        information,
        transform=plt.gca().transAxes,
        horizontalalignment="right",
        verticalalignment="top",
        bbox={"boxstyle": "round", "alpha": 0.8},
    )

    plt.tight_layout()

    date_for_filename = safe_filename(trip_date)
    output_path = output_folder / f"trip_{trip_number}_{date_for_filename}.png"

    plt.savefig(output_path, dpi=150)
    plt.close()

    print(f"Created: {output_path}")


def make_trip_summary_graph(trips, output_folder):
    """
    Create one graph comparing distance, score, and event totals
    across all saved trips.
    """
    if not trips:
        return

    trip_labels = [f"Trip {index}" for index in range(1, len(trips) + 1)]

    distances = [
        float(trip.get("distance_miles", 0))
        for trip in trips
    ]

    scores = [
        float(trip.get("drive_score", trip.get("score", 0)))
        for trip in trips
    ]

    hard_brakes = [
        int(trip.get("hard_brakes", 0))
        for trip in trips
    ]

    fast_accelerations = [
        int(trip.get("fast_accelerations", 0))
        for trip in trips
    ]

    # Distance comparison
    plt.figure(figsize=(10, 6))
    plt.bar(trip_labels, distances)
    plt.title("Trip Distance Comparison")
    plt.xlabel("Trip")
    plt.ylabel("Distance (miles)")
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_folder / "summary_distances.png", dpi=150)
    plt.close()

    # Drive score comparison
    plt.figure(figsize=(10, 6))
    plt.bar(trip_labels, scores)
    plt.title("Drive Score Comparison")
    plt.xlabel("Trip")
    plt.ylabel("Drive score")
    plt.ylim(0, 100)
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_folder / "summary_scores.png", dpi=150)
    plt.close()

    # Driving events comparison
    positions = list(range(len(trips)))
    bar_width = 0.4

    plt.figure(figsize=(10, 6))
    plt.bar(
        [position - bar_width / 2 for position in positions],
        hard_brakes,
        width=bar_width,
        label="Hard brakes",
    )
    plt.bar(
        [position + bar_width / 2 for position in positions],
        fast_accelerations,
        width=bar_width,
        label="Fast accelerations",
    )

    plt.title("Driving Event Comparison")
    plt.xlabel("Trip")
    plt.ylabel("Event count")
    plt.xticks(positions, trip_labels)
    plt.legend()
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_folder / "summary_events.png", dpi=150)
    plt.close()

    print("Created summary graphs.")


def main():
    try:
        trips = load_trips(DATA_FILE)

        OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

        print(f"Loaded {len(trips)} trips from {DATA_FILE.resolve()}")

        for trip_number, trip in enumerate(trips, start=1):
            make_speed_graph(
                trip=trip,
                trip_number=trip_number,
                output_folder=OUTPUT_FOLDER,
            )

        make_trip_summary_graph(trips, OUTPUT_FOLDER)

        print(f"\nFinished. Graphs are in: {OUTPUT_FOLDER.resolve()}")

    except (FileNotFoundError, json.JSONDecodeError, ValueError) as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()
