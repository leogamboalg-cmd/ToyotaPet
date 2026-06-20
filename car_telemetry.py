import threading
import time
import obd


class CarTelemetry:
    def __init__(self):
        """Initializes the connection and setup variables."""
        self.connection = obd.OBD("COM7", fast=False, timeout=10)

        self._lock = threading.Lock()
        self._running = False
        self._thread = None

        self._speed = 0
        self._rpm = 0
        self._coolant = 0
        self._dtc = "Clear"

        self._last_dtc_check = 0

        if self.connection.is_connected():
            print("🚗 [Telemetry] Successfully connected to 2018 Toyota Corolla!")
        else:
            raise ConnectionError(
                "OBD connection failed. Check your adapter and ignition."
            )

    def start(self):
        """Starts the background telemetry thread loop."""
        if self._thread is None:
            self._running = True
            self._thread = threading.Thread(
                target=self._update_loop,
                daemon=True
            )
            self._thread.start()
            print("🧵 [Telemetry] Background worker thread started successfully.")

    def _update_loop(self):
        """Internal continuous loop that fetches car data over and over."""
        while self._running:
            try:
                new_rpm = self.connection.query(obd.commands.RPM)
                new_speed = self.connection.query(obd.commands.SPEED)
                new_coolant = self.connection.query(obd.commands.COOLANT_TEMP)

                now = time.time()
                should_check_dtc = now - self._last_dtc_check >= 10

                new_dtc = None
                if should_check_dtc:
                    new_dtc = self.connection.query(obd.commands.GET_DTC)
                    self._last_dtc_check = now

                with self._lock:
                    if not new_speed.is_null():
                        self._speed = int(new_speed.value.magnitude * 0.621371)

                    if not new_rpm.is_null():
                        self._rpm = int(new_rpm.value.magnitude)

                    if not new_coolant.is_null():
                        self._coolant = int(
                            (new_coolant.value.magnitude * 9 / 5) + 32
                        )

                    if new_dtc is not None:
                        if not new_dtc.is_null() and new_dtc.value:
                            self._dtc = str(new_dtc.value)
                        else:
                            self._dtc = "Clear"

            except Exception as e:
                print(f"[Telemetry Error] {e}")

            time.sleep(0.5)

    def get_data(self):
        """
        Safely returns a clean snapshot of all data for your Pygame UI loop.
        """
        with self._lock:
            return self._speed, self._rpm, self._coolant, self._dtc

    def stop(self):
        """Safely stops the thread and disconnects hardware link."""
        print("[Telemetry] Shutting down connection...")
        self._running = False

        if self._thread:
            self._thread.join(timeout=1.0)

        self.connection.close()
