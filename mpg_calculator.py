# extended_telemetry.py


class ExtendedTelemetry:
    """
    Calculates derived metrics from CarTelemetry data.
    Does NOT talk to the OBD adapter directly.
    """

    def __init__(self, car_telemetry):
        self.car_telemetry = car_telemetry

        self.instant_mpg = 0.0

    def calculate_instant_mpg(self):
        """
        Estimate MPG using speed and MAF.

        Requires CarTelemetry to expose:
            self._speed
            self._maf
        """

        speed = self.car_telemetry._speed
        maf = self.car_telemetry._maf

        try:
            gallons_per_hour = (
                maf * 3600
            ) / (14.7 * 2834)

            if gallons_per_hour > 0:
                self.instant_mpg = (
                    speed / gallons_per_hour
                )
            else:
                self.instant_mpg = 0.0

        except Exception as e:
            print(f"[ExtendedTelemetry] MPG error: {e}")
            self.instant_mpg = 0.0

        return round(self.instant_mpg, 1)

    def get_data(self):
        """
        Return all derived metrics.
        """

        return {
            "instant_mpg": self.calculate_instant_mpg()
        }
