# extended_telemetry.py

import obd


class ExtendedTelemetry:
    def __init__(self, connection):
        self.connection = connection

        self.commands = {
            "speed": obd.commands.SPEED,
            "rpm": obd.commands.RPM,
            "coolant_temp": obd.commands.COOLANT_TEMP,
            "throttle": obd.commands.THROTTLE_POS,
            "engine_load": obd.commands.ENGINE_LOAD,
            "fuel_level": obd.commands.FUEL_LEVEL,
            "battery_voltage": obd.commands.CONTROL_MODULE_VOLTAGE,
            "intake_temp": obd.commands.INTAKE_TEMP,
            "maf": obd.commands.MAF,
            "timing_advance": obd.commands.TIMING_ADVANCE,
            "intake_pressure": obd.commands.INTAKE_PRESSURE,
            "runtime": obd.commands.RUN_TIME,
        }

    def read_all(self):
        data = {}

        for name, command in self.commands.items():
            try:
                # Skip unsupported commands
                if not self.connection.supports(command):
                    data[name] = None
                    continue

                response = self.connection.query(command)

                if response.is_null():
                    data[name] = None
                else:
                    data[name] = response.value

            except Exception as e:
                print(f"[Telemetry] Failed reading {name}: {e}")
                data[name] = None

        return data
