import time


class PetManager:
    def __init__(self, sounds=None):
        self.mood = "happy"
        self.message = "Ready to roll!"

        # How long an event reaction remains visible.
        self.reaction_duration = 3.0
        self.reaction_ends_at = 0.0

        self.sounds = sounds or {}

        # Remember event totals already processed.
        self.previous_hard_brakes = 0
        self.last_high_speed_sound = 0.0
        self.high_speed_sound_cooldown = 10.0
        self.previous_fast_accelerations = 0
        self.previous_long_idle_events = 0
        self.was_high_speed = False

    def _play_sound(self, name):
        sound = self.sounds.get(name)

        if sound is not None:
            sound.play()

    def update(
        self,
        speed,
        rpm,
        hard_brakes=0,
        fast_accelerations=0,
        long_idle_events=0,
        trip_active=False,
    ):
        """
        Update the pet using current vehicle and trip data.

        Event reactions temporarily override normal driving moods.
        """
        current_time = time.monotonic()

        try:
            speed = max(0.0, float(speed))
        except (TypeError, ValueError):
            speed = 0.0

        try:
            rpm = max(0.0, float(rpm))
        except (TypeError, ValueError):
            rpm = 0.0

        # Detect whether an event count increased.
        new_hard_brake = hard_brakes > self.previous_hard_brakes
        new_fast_acceleration = (
            fast_accelerations > self.previous_fast_accelerations
        )
        new_long_idle_event = long_idle_events > self.previous_long_idle_events

        # Save the latest counts so the same event is not reused.
        self.previous_hard_brakes = hard_brakes
        self.previous_fast_accelerations = fast_accelerations
        self.previous_long_idle_events = long_idle_events

        # Hard braking has priority over rapid acceleration.
        if new_hard_brake:
            self.mood = "shocked"
            self.message = "Whoa! Easy on the brakes!"
            self.reaction_ends_at = (
                current_time + self.reaction_duration
            )
            self._play_sound("hard_brake")
            print("Playing sound: hard_brake")
            return

        if new_fast_acceleration:
            self.mood = "excited"
            self.message = "Zooming today!"
            self.reaction_ends_at = (
                current_time + self.reaction_duration
            )
            self._play_sound("fast_acceleration")
            return

        if new_long_idle_event:
            self.mood = "bored"
            self.message = "Are we parked?"
            self.reaction_ends_at = (
                current_time + self.reaction_duration
            )
            self._play_sound("long_idle_event")
            return

        # Keep displaying the temporary event reaction.
        if current_time < self.reaction_ends_at:
            return

        if speed < 75:
            self.was_high_speed = False

       # Normal live behavior.
        if rpm < 300:
            self.mood = "sleepy"
            self.message = "The car is resting."

        elif speed < 1:
            self.mood = "idle"
            self.message = "We're stopped for now."

        elif speed >= 75:
            self.mood = "nervous"
            self.message = "That's pretty fast!"

            if (
                current_time - self.last_high_speed_sound
                >= self.high_speed_sound_cooldown and not self.was_high_speed
            ):
                self._play_sound("high_speed")
                self.last_high_speed_sound = current_time
            self.was_high_speed = True

        elif trip_active:
            self.mood = "happy"
            self.message = "Nice drive so far!"

        else:
            self.mood = "happy"
            self.message = "Ready to roll!"

    def reset_trip_events(self):
        """
        Reset remembered trip-event totals when beginning a new trip.
        """
        self.previous_hard_brakes = 0
        self.previous_fast_accelerations = 0
        self.previous_long_idle_events = 0
        self.reaction_ends_at = 0.0
        self.last_high_speed_sound = 0.0

    def get_data(self):
        return {
            "mood": self.mood,
            "message": self.message,
        }
