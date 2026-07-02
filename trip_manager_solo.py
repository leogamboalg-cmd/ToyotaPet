"""
trip_manager_practice.py

A learning version of TripManager.

The class and method names are provided, but the main logic is intentionally
left unfinished. Implement one method at a time.

Recommended order:
1. __init__
2. reset_trip
3. start_trip
4. pause_trip
5. resume_trip
6. get_elapsed_seconds
7. update
8. calculate_average_speed
9. calculate_drive_score
10. get_data
11. end_trip
"""

import time
from collections import deque


class TripManager:
    """
    Tracks one driving trip.

    Responsibilities:
    - Start, pause, resume, and end a trip
    - Receive speed and RPM readings
    - Track time, distance, and maximum speed
    - Detect driving events
    - Calculate a drive score
    - Return trip data as a dictionary
    """

    def __init__(self):
        """
        Create all instance variables needed by a trip.

        Instructions:
        1. Create trip-state variables: trip_active and trip_paused.

        2. Create timing variables: start_time, pause_started_at,
           total_paused_seconds, and last_update_time.
        3. Create statistics: distance_miles, maximum_speed, idle_seconds,
           and moving_seconds.
        4. Store previous_speed.
        5. Create speed_history and last_speed_sample_time.
        6. Create event counters and a starting drive_score of 100.
        7. Create recent speed samples using deque(), active-event flags,
           and event thresholds.

        Suggested values:
        - Booleans: False
        - Counters/totals: 0 or 0.0
        - Times not set yet: None
        - Starting score: 100

        Useful tools:
        - deque(): efficient queue for recent readings
        - None: represents a value that has not been set
        """
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
        self.speed_history = deque(maxlen=300)
        self.last_speed_sample_time = None

        # Driving events
        self.hard_brakes = 0
        self.fast_accelerations = 0
        self.long_idle_events = 0
        self.drive_score = 100

        # Event detection timing
        self.long_idle_threshold_seconds = 120.0
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

    def reset_trip(self):
        """
        Reset all values that belong to one trip.

        Instructions:
        1. Reset timing values.
        2. Reset distance, speed, idle, and moving statistics.
        3. Reset previous telemetry values.
        4. Empty speed history and recent event samples.
        5. Reset event counters and active-event flags.
        6. Reset the score to 100.

        Useful methods:
        - list.clear(): removes every item from a list
        - deque.clear(): removes every item from a deque
        """

        self.start_time = None
        self.pause_started_at = None
        self.total_paused_seconds = 0.0
        self.last_update_time = None

        self.distance_miles = 0.0
        self.maximum_speed = 0.0
        self.idle_seconds = 0.0

        self.previous_speed = 0.0
        self.speed_history.clear()
        self.last_speed_sample_time = None
        self.hard_brakes = 0
        self.fast_accelerations = 0
        self.long_idle_events = 0
        self.drive_score = 100
        self.event_speed_samples.clear()

        self.hard_brake_active = False
        self.fast_acceleration_active = False
        self.current_idle_seconds = 0.0
        self.moving_seconds = 0.0
        self.long_idle_event_recorded = False

    def start_trip(self):
        """
        Start a brand-new trip.

        Instructions:
        1. If already active, return.
        2. Call reset_trip().
        3. Save time.monotonic() in start_time.
        4. Set trip_active to True and trip_paused to False.
        5. Keep last_update_time as None until the first telemetry reading.
        """
        if self.trip_active:
            return
        self.reset_trip()
        self.start_time = time.monotonic()
        self.trip_active = True
        self.trip_paused = False

    def pause_trip(self):
        """
        Pause an active trip.

        Instructions:
        1. Return if inactive.
        2. Return if already paused.
        3. Set trip_paused to True.
        4. Save time.monotonic() in pause_started_at.
        5. Reset continuous idle/event state that should not cross a pause.
        """
        if not self.trip_active or self.trip_paused:
            return

        self.trip_paused = True
        self.pause_started_at = time.monotonic()
        self.current_idle_seconds = 0.0
        self.long_idle_event_recorded = False

    def resume_trip(self):
        """
        Resume a paused trip.

        Instructions:
        1. Return if inactive or not paused.
        2. Get current_time using time.monotonic().
        3. Compute current_time - pause_started_at.
        4. Add the result to total_paused_seconds.
        5. Set pause_started_at to None.
        6. Set trip_paused to False.
        7. Set last_update_time to current_time so paused time is not counted.
        """
        if not self.trip_active or not self.trip_paused:
            return

        current_time = time.monotonic()
        self.total_paused_seconds += current_time - self.pause_started_at
        self.pause_started_at = None
        self.trip_paused = False
        self.last_update_time = current_time

    def toggle_pause(self):
        """
        Switch between paused and active.

        Instructions:
        1. Return if inactive.
        2. If paused, call resume_trip().
        3. Otherwise, call pause_trip().
        """
        if not self.trip_active:
            return

        if self.trip_paused:
            self.resume_trip()
        else:
            self.pause_trip()

    def end_trip(self):
        """
        Finish the trip and return its final dictionary.

        Instructions:
        1. Return None if inactive.
        2. Call get_data() before changing trip_active.
        3. Store the dictionary in a local variable.
        4. Set trip_active and trip_paused to False.
        5. Return the dictionary.

        Add saving/network logic later, after the class works locally.
        """
        if not self.trip_active:
            return None

        data = self.get_data()

        self.trip_active = False
        self.trip_paused = False

        return data

    def update(self, speed_mph, rpm):
        """
        Process one speed and RPM reading.

        Instructions:
        1. Return if inactive or paused.
        2. Convert speed_mph and rpm with float() inside try/except.
        3. Reject negative speed.
        4. Get current_time with time.monotonic().
        5. On the first reading, initialize previous values and return.
        6. Calculate delta_seconds = current_time - last_update_time.
        7. Ignore invalid or very large time gaps.
        8. Calculate distance:
               average_speed = (previous_speed + speed_mph) / 2
               delta_hours = delta_seconds / 3600
               distance += average_speed * delta_hours
        9. Update maximum_speed with max().
        10. Track idle/moving time using speed, rpm, and delta_seconds.
        11. Append (current_time, speed_mph) to the recent-samples deque.
        12. Remove old samples with popleft().
        13. Detect hard braking and fast acceleration over a time window.
        14. Count one continuous maneuver once using active flags.
        15. Add a graph sample around once per second.
        16. Set previous_speed at the end.

        Useful tools:
        - float(value): converts input to a decimal number
        - try/except: handles bad input without crashing
        - max(a, b): returns the larger value
        - deque.append(value): adds a newest reading
        - deque.popleft(): removes the oldest reading
        - len(collection): number of stored items
        - abs(number): magnitude without the sign
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

        if self.last_update_time is None:
            self.previous_speed = speed_mph
            self.last_update_time = current_time
            self.last_speed_sample_time = current_time
            self.speed_history.append(speed_mph)
            self.maximum_speed = speed_mph
            self.event_speed_samples.append((current_time, speed_mph))
            return

        else:
            time_passed = current_time - self.last_update_time
            self.last_update_time = current_time
            if time_passed <= 0 or time_passed > 10:
                self.previous_speed = speed_mph
                return

        average_speed = (self.previous_speed + speed_mph) / 2
        delta_hours = time_passed / 3600
        self.distance_miles += average_speed * delta_hours
        self.maximum_speed = max(self.maximum_speed, speed_mph)

        if speed_mph < 1 and rpm > 300:
            self.idle_seconds = self.idle_seconds + \
                (time_passed)
            self.current_idle_seconds += time_passed
            if (
                self.current_idle_seconds >= self.long_idle_threshold_seconds
                and not self.long_idle_event_recorded
            ):
                self.long_idle_events += 1
                self.long_idle_event_recorded = True
        elif speed_mph >= 1:
            self.moving_seconds = self.moving_seconds + \
                (time_passed)
            self.current_idle_seconds = 0.0
            self.long_idle_event_recorded = False

        self.event_speed_samples.append((current_time, speed_mph))

        while len(self.event_speed_samples) > 1 and \
                (current_time - self.event_speed_samples[0][0]) > 1:
            self.event_speed_samples.popleft()

        if len(self.event_speed_samples) >= 2:

            speed_change = speed_mph - self.event_speed_samples[0][1]
            time_change = current_time - self.event_speed_samples[0][0]

            if time_change > 0:
                acceleration = speed_change / time_change

                if acceleration < self.hard_brake_threshold and not self.hard_brake_active:
                    self.hard_brakes += 1
                    self.hard_brake_active = True

                if acceleration > self.fast_acceleration_threshold and not self.fast_acceleration_active:
                    self.fast_accelerations += 1
                    self.fast_acceleration_active = True

                if abs(acceleration) <= self.event_release_threshold:
                    self.hard_brake_active = False
                    self.fast_acceleration_active = False

        if (
            self.last_speed_sample_time is None
            or current_time - self.last_speed_sample_time >= 1.0
        ):
            self.speed_history.append(speed_mph)
            self.last_speed_sample_time = current_time

        self.previous_speed = speed_mph

    def get_elapsed_seconds(self):
        """
        Return trip duration excluding paused time.

        Instructions:
        1. Return 0.0 if start_time is None.
        2. Get current_time with time.monotonic().
        3. Start with total_paused_seconds.
        4. If currently paused, include the unfinished pause.
        5. Compute current_time - start_time - paused_seconds.
        6. Return max(0.0, result).
        """
        if self.start_time is None:
            return 0.0

        current_time = time.monotonic()

        paused_seconds = self.total_paused_seconds

        if self.trip_paused and self.pause_started_at is not None:
            paused_seconds += current_time - self.pause_started_at

        elapsed_seconds = current_time - self.start_time - paused_seconds

        return max(0.0, elapsed_seconds)

    def calculate_average_speed(self):
        """
        Calculate moving average speed.

        Formula:
            distance_miles / moving_hours

        Instructions:
        1. moving_hours = moving_seconds / 3600.
        2. If moving_hours <= 0, return 0.0.
        3. Return distance_miles / moving_hours.
        """

        if self.moving_seconds == 0:
            return 0.0

        average_speed = self.distance_miles / (self.moving_seconds / 3600)

        return average_speed

    def calculate_drive_score(self):
        """
        Calculate a score from 0 to 100.

        Suggested approach:
        1. scoring_distance = max(distance_miles, 3.0)
        2. distance_units = scoring_distance / 10
        3. Convert events to events per 10 miles.
        4. Apply weights, such as 2.5 per hard brake and 1.25 per
           fast acceleration.
        5. Cap idle penalty with min().
        6. Subtract total penalty from 100.
        7. Clamp with max(0, min(100, score)).
        8. Use round() for a whole-number score.

        Useful built-ins:
        - min(a, b): smaller value
        - max(a, b): larger value
        - round(number): nearest integer
        """

        scoring_distance = max(self.distance_miles, 3.0)
        distance_units = scoring_distance / 10

        hard_brake_penalty = (self.hard_brakes / distance_units) * 2.5
        fast_acceleration_penalty = (
            self.fast_accelerations / distance_units) * 1.25

        idle_penalty = min(self.long_idle_events * 1.0, 5.0)

        total_penalty = hard_brake_penalty + fast_acceleration_penalty + idle_penalty
        score = 100 - total_penalty
        self.drive_score = round(max(0, min(100, score)))
        return self.drive_score

    def format_duration(self, total_seconds):
        """
        Convert seconds to HH:MM:SS.

        Instructions:
        1. Convert to a non-negative int.
        2. hours = total_seconds // 3600
        3. minutes = (total_seconds % 3600) // 60
        4. seconds = total_seconds % 60
        5. Return f"{hours:02}:{minutes:02}:{seconds:02}"

        Operators:
        - // means whole-number division
        - % returns the remainder
        """
        total_seconds = max(0, int(total_seconds))

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def get_data(self):
        """
        Return current trip information as a dictionary.

        Instructions:
        1. Call calculate_drive_score().
        2. Call calculate_average_speed().
        3. Format elapsed and idle time.
        4. Choose a smoothness label from score ranges.
        5. Return a dictionary containing state, times, distance, speeds,
           score, event totals, history, and smoothness.
        6. Convert speed_history to a list so callers do not receive
           your original deque.
        """
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
            "speed_history": list(self.speed_history),
            "hard_brakes": self.hard_brakes,
            "fast_accelerations": self.fast_accelerations,
            "long_idle_events": self.long_idle_events,
            "smoothness": smoothness,
            "score": score,
        }
