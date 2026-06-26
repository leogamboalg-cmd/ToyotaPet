# trip_manager.py
import time
import requests
import time
from collections import deque

import requests

EXPRESS_URL = "http://localhost:5000/api/data/submitData"


def send_trip_to_server(trip_data):
    try:
        requests.post(
            "http://127.0.0.1:5000/api/data/submitData",
            json=trip_data,
            timeout=2
        )
    except requests.RequestException as e:
        print("Failed to send trip:", e)


class TripManager:
    """
    Manages one driving trip.

    This class should:
    - Start, pause, resume, and end a trip
    - Receive live speed and RPM values
    - Calculate trip statistics
    - Return data in the format expected by trips_screen.py
    """

    def __init__(self):
        # Trip state
        self.trip_active = False
        self.trip_paused = False

        # Timing
        self.start_time = None
        self.pause_started_at = None
        self.total_paused_seconds = 0.0
        self.last_update_time = None

        # Trip statistics
        self.distance_miles = 0.0
        self.maximum_speed = 0.0
        self.idle_seconds = 0.0
        self.moving_seconds = 0.0

        # Previous telemetry values
        self.previous_speed = 0.0

        # Graph data
        self.speed_history = []
        self.last_speed_sample_time = None

        # Driving events
        self.hard_brakes = 0
        self.fast_accelerations = 0
        self.long_idle_events = 0
        self.drive_score = 100

        # Event detection timing
        self.long_idle_threshold_seconds = 60.0
        self.long_idle_event_recorded = False

        # Store recent speed readings for event detection.
        self.event_speed_samples = deque()
        self.event_window_seconds = 1.0

        # Prevent one continuous maneuver from counting repeatedly.
        self.hard_brake_active = False
        self.fast_acceleration_active = False

        # Acceleration thresholds in MPH per second.
        self.hard_brake_threshold = -8.0
        self.fast_acceleration_threshold = 7.0

        # The acceleration must return near normal before another event can count.
        self.event_release_threshold = 3.0

        self.current_idle_seconds = 0.0

    def start_trip(self):
        """
        Start a completely new trip.
        """

        if self.trip_active:
            return

        self.reset_trip()

        self.start_time = time.monotonic()

        # update() will initialize this when the first real
        # telemetry reading arrives.
        self.last_update_time = None

        self.trip_active = True
        self.trip_paused = False

    def pause_trip(self):
        """
        Pause the current trip.

        Instructions:
        1. Only pause if a trip is active.
        2. Do nothing if it is already paused.
        3. Set trip_paused to True.
        4. Store the time the pause began.
        """
        if not self.trip_active:
            return

        if self.trip_paused:
            return

        self.trip_paused = True
        self.pause_started_at = time.monotonic()

        # A pause breaks any continuous idle period.
        self.current_idle_seconds = 0.0
        self.long_idle_event_recorded = False

    def resume_trip(self):
        if not self.trip_active:
            return

        if not self.trip_paused:
            return

        current_time = time.monotonic()

        pause_duration = current_time - self.pause_started_at
        self.total_paused_seconds += pause_duration

        self.pause_started_at = None
        self.trip_paused = False
        self.last_update_time = current_time
        self.last_speed_sample_time = None

    def toggle_pause(self):
        """
        Switch between paused and active.

        Instructions:
        - If currently paused, call resume_trip().
        - Otherwise, call pause_trip().
        """
        if not self.trip_active:
            return

        if self.trip_paused:
            self.resume_trip()
        else:
            self.pause_trip()

    def end_trip(self):
        """
        End the current trip.

        Instructions:
        1. Do nothing if no trip is active.
        2. Get the final trip data before changing the state.
        3. Set trip_active and trip_paused to False.
        4. Later, save the finished trip to a JSON history file.
        5. Return the final trip dictionary.
        """
        if not self.trip_active:
            return

        trip_data = self.get_data()

        self.trip_active = False
        self.trip_paused = False
        send_trip_to_server(trip_data)

        return trip_data

    def reset_trip(self):
        # Reset timing
        self.start_time = None
        self.pause_started_at = None
        self.total_paused_seconds = 0.0
        self.last_update_time = None

        # Reset statistics
        self.distance_miles = 0.0
        self.maximum_speed = 0.0
        self.idle_seconds = 0.0
        self.moving_seconds = 0.0

        # Reset previous telemetry
        self.previous_speed = 0.0

        # Reset graph data
        self.speed_history.clear()
        self.last_speed_sample_time = None

        # Reset events and score
        self.hard_brakes = 0
        self.fast_accelerations = 0
        self.long_idle_events = 0
        self.drive_score = 100
        self.long_idle_event_recorded = False
        self.event_speed_samples.clear()

        self.hard_brake_active = False
        self.fast_acceleration_active = False
        self.current_idle_seconds = 0.0

    def _cooldown_finished(self, previous_event_time, current_time):
        """
        Return True when enough time has passed since the previous event.

        Without a cooldown, one braking action could be counted multiple
        times because update() may run several times per second.
        """

        if previous_event_time is None:
            return True

        return (
            current_time - previous_event_time
            >= self.event_cooldown_seconds
        )

    def update(self, speed_mph, rpm):
        """
        Process one telemetry update from the car.

        This method:
        - Calculates distance
        - Tracks idle and moving time
        - Records graph samples
        - Detects hard braking
        - Detects rapid acceleration
        - Detects long idle periods
        """

        if not self.trip_active or self.trip_paused:
            return

        current_time = time.monotonic()

        try:
            speed_mph = float(speed_mph)

            if speed_mph < 0:
                return
        except (TypeError, ValueError):
            # Do not treat missing speed data as zero.
            return

        try:
            rpm = max(0.0, float(rpm))
        except (TypeError, ValueError):
            rpm = 0.0

        # Establish the first telemetry reading.
        if self.last_update_time is None:
            self.last_update_time = current_time
            self.previous_speed = speed_mph
            self.last_speed_sample_time = current_time
            self.speed_history.append(speed_mph)
            self.maximum_speed = speed_mph
            return

        delta_seconds = current_time - self.last_update_time
        self.last_update_time = current_time

        # Ignore invalid timing or long connection gaps.
        if delta_seconds <= 0 or delta_seconds > 2:
            self.previous_speed = speed_mph
            self.last_speed_sample_time = current_time
            return

        # Use the average of the previous and current speeds.
        average_interval_speed = (
            self.previous_speed + speed_mph
        ) / 2.0

        delta_hours = delta_seconds / 3600.0
        self.distance_miles += average_interval_speed * delta_hours

        self.maximum_speed = max(
            self.maximum_speed,
            speed_mph
        )

        # -------------------------
        # IDLE AND MOVING TIME
        # -------------------------

        engine_running = rpm > 400
        vehicle_stopped = speed_mph < 1.0

        if vehicle_stopped and engine_running:
            self.idle_seconds += delta_seconds
            self.current_idle_seconds += delta_seconds

            if (
                self.current_idle_seconds
                >= self.long_idle_threshold_seconds
                and not self.long_idle_event_recorded
            ):
                self.long_idle_events += 1
                self.long_idle_event_recorded = True

        elif speed_mph >= 1.0:
            self.moving_seconds += delta_seconds
            self.current_idle_seconds = 0.0
            self.long_idle_event_recorded = False

        else:
            self.current_idle_seconds = 0.0
            self.long_idle_event_recorded = False

        # -------------------------
        # DRIVING EVENT DETECTION
        # -------------------------

        # Add the newest speed reading.
        self.event_speed_samples.append((current_time, speed_mph))

        # Remove readings older than approximately one second.
        while (
            len(self.event_speed_samples) > 1
            and current_time - self.event_speed_samples[0][0]
            > self.event_window_seconds
        ):
            self.event_speed_samples.popleft()

        if len(self.event_speed_samples) >= 2:
            oldest_time, oldest_speed = self.event_speed_samples[0]

            event_delta_seconds = current_time - oldest_time

            if event_delta_seconds >= 0.75:
                acceleration_mph_per_second = (
                    speed_mph - oldest_speed
                ) / event_delta_seconds

                # Count one hard-braking maneuver.
                if (
                    oldest_speed >= 10.0
                    and acceleration_mph_per_second
                    <= self.hard_brake_threshold
                ):
                    if not self.hard_brake_active:
                        self.hard_brakes += 1
                        self.hard_brake_active = True

                    self.fast_acceleration_active = False

                # Count one fast-acceleration maneuver.
                elif (
                    speed_mph >= 10.0
                    and acceleration_mph_per_second
                    >= self.fast_acceleration_threshold
                ):
                    if not self.fast_acceleration_active:
                        self.fast_accelerations += 1
                        self.fast_acceleration_active = True

                    self.hard_brake_active = False

                # Reset only after acceleration becomes normal again.
                elif (
                    abs(acceleration_mph_per_second)
                    <= self.event_release_threshold
                ):
                    self.hard_brake_active = False
                    self.fast_acceleration_active = False

        # -------------------------
        # SPEED HISTORY
        # -------------------------

        if (
            self.last_speed_sample_time is None
            or current_time - self.last_speed_sample_time >= 1.0
        ):
            self.speed_history.append(speed_mph)
            self.last_speed_sample_time = current_time

            if len(self.speed_history) > 300:
                self.speed_history.pop(0)

        self.previous_speed = speed_mph

    def get_elapsed_seconds(self):
        """
        Return active trip duration without paused time.

        Instructions:
        1. Return 0 if the trip has never started.
        2. Find the current monotonic time.
        3. Start with total_paused_seconds.
        4. If currently paused, include the current unfinished pause.
        5. Subtract paused time from total time since start_time.
        6. Never return a negative number.
        """
        if not self.trip_active or self.start_time is None:
            return 0.0

        current_time = time.monotonic()
        paused_seconds = self.total_paused_seconds

        # If the trip is currently paused, the current pause has not yet
        # been added to total_paused_seconds, so include it temporarily.
        if self.trip_paused and self.pause_started_at is not None:
            paused_seconds += current_time - self.pause_started_at

        elapsed_seconds = (
            current_time
            - self.start_time
            - paused_seconds
        )

        return max(0.0, elapsed_seconds)

    def calculate_average_speed(self):
        """
        Calculate average speed for the trip.

        Instructions:
        - Decide whether this should be an overall average or moving average.
        - For overall average:
              distance_miles / elapsed_hours
        - For moving average:
              distance_miles / moving_hours
        - Protect against division by zero.
        """

        moving_hours = self.moving_seconds / 3600.0

        if moving_hours <= 0:
            return 0.0

        return self.distance_miles / moving_hours

    def format_duration(self, total_seconds):
        total_seconds = max(0, int(total_seconds))

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def calculate_drive_score(self):
        # Use at least three miles so very short trips are not over-penalized.
        scoring_distance = max(self.distance_miles, 3.0)

        # Convert event totals into events per ten miles.
        distance_units = scoring_distance / 10.0

        hard_brakes_per_10_miles = (
            self.hard_brakes / distance_units
        )

        fast_accels_per_10_miles = (
            self.fast_accelerations / distance_units
        )

        hard_brake_penalty = hard_brakes_per_10_miles * 2.5
        acceleration_penalty = fast_accels_per_10_miles * 1.25

        # Idle penalty is intentionally small and capped.
        idle_penalty = min(self.long_idle_events * 1.0, 5.0)

        total_penalty = (
            hard_brake_penalty
            + acceleration_penalty
            + idle_penalty
        )

        self.drive_score = round(
            max(0.0, min(100.0, 100.0 - total_penalty))
        )

        return self.drive_score

    def get_data(self):
        score = self.calculate_drive_score()

        if score >= 90:
            smoothness = "Excellent"
        elif score >= 75:
            smoothness = "Good"
        elif score >= 60:
            smoothness = "Fair"
        else:
            smoothness = "Needs Improvement"

        return {
            "trip_active": self.trip_active,
            "trip_paused": self.trip_paused,
            "elapsed_time": self.format_duration(
                self.get_elapsed_seconds()
            ),
            "distance_miles": self.distance_miles,
            "average_speed": self.calculate_average_speed(),
            "maximum_speed": self.maximum_speed,
            "drive_score": score,
            "idle_time": self.format_duration(
                self.idle_seconds
            ),
            "speed_history": self.speed_history.copy(),
            "hard_brakes": self.hard_brakes,
            "fast_accelerations": self.fast_accelerations,
            "long_idle_events": self.long_idle_events,
            "smoothness": smoothness,
            "score": score,
        }
