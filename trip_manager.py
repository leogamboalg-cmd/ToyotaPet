import time


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

    def start_trip(self):
        """
        Start a new trip.

        Instructions:
        1. Do nothing if a trip is already active.
        2. Reset all old trip statistics.
        3. Store the current monotonic time.
        4. Set trip_active to True.
        5. Set trip_paused to False.
        6. Set last_update_time so update() can measure elapsed time.
        """
        if self.trip_active:
            return

        self.reset_trip()

        current_time = time.monotonic()

        self.start_time = current_time
        self.last_update_time = current_time

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

    def update(self, speed_mph, rpm):
        """
        Process one telemetry update.

        main.py should call this repeatedly while the program is running.

        Instructions:
        1. Return immediately if the trip is inactive or paused.
        2. Read the current monotonic time.
        3. Calculate delta_seconds since the previous update.
        4. Reject invalid values such as negative time or very large gaps.
        5. Convert speed_mph and rpm to safe non-negative floats.
        6. Add distance using:
               distance = speed_mph * (delta_seconds / 3600)
        7. Update maximum_speed.
        8. Add idle time when speed is below 1 MPH and RPM is above 400.
        9. Add moving time when speed is at least 1 MPH.
        10. Store one speed-history sample about once per second.
        11. Later, detect hard braking and fast acceleration.
        12. Save speed_mph into previous_speed.
        """

        if not self.trip_active or self.trip_paused:
            return

        current_time = time.monotonic()

        if self.last_update_time is None:
            self.last_update_time = current_time
            return

        delta_seconds = current_time - self.last_update_time
        self.last_update_time = current_time

        if delta_seconds <= 0 or delta_seconds > 2:
            return

        try:
            speed_mph = max(0.0, float(speed_mph))
        except (TypeError, ValueError):
            speed_mph = 0.0

        try:
            rpm = max(0.0, float(rpm))
        except (TypeError, ValueError):
            rpm = 0.0

        delta_hours = delta_seconds / 3600
        self.distance_miles += speed_mph * delta_hours

        self.maximum_speed = max(self.maximum_speed, speed_mph)

        if speed_mph < 1 and rpm > 400:
            self.idle_seconds += delta_seconds

        if speed_mph >= 1:
            self.moving_seconds += delta_seconds

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

        elapsed_seconds = self.get_elapsed_seconds()
        elapsed_hours = elapsed_seconds / 3600

        if elapsed_hours <= 0:
            return 0.0

        return self.distance_miles / elapsed_hours

    def format_duration(self, total_seconds):
        total_seconds = max(0, int(total_seconds))

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def calculate_drive_score(self):
        score = 100

        score -= self.hard_brakes * 4
        score -= self.fast_accelerations * 2
        score -= self.long_idle_events * 1

        # Prevent the score from going below 0 or above 100.
        self.drive_score = max(0, min(100, score))

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
        }
