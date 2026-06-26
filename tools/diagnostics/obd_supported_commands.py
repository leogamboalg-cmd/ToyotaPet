import csv
import time
from datetime import datetime

import obd


PORT = "COM7"  # change to COM8 if needed
TIMEOUT_SECONDS = 3
OUTPUT_FILE = "obd_supported_commands.csv"


def clean_value(response):
    if response is None or response.is_null():
        return "NO DATA"

    try:
        return str(response.value)
    except Exception:
        return str(response)


def main():
    print("Connecting to OBD-II...")
    connection = obd.OBD(
        PORT,
        timeout=TIMEOUT_SECONDS,
        fast=False
    )

    if not connection.is_connected():
        print("Could not connect.")
        return

    print("Connected!")
    print("Testing every python-OBD command...\n")

    results = []

    all_commands = sorted(
        obd.commands.__dict__.items(),
        key=lambda item: item[0]
    )

    for name, command in all_commands:
        if not isinstance(command, obd.OBDCommand):
            continue

        print(f"Testing {name}...", end=" ")

        try:
            start = time.time()
            response = connection.query(command, force=True)
            elapsed_ms = round((time.time() - start) * 1000, 2)

            value = clean_value(response)

            supported = value != "NO DATA"

            print(value)

            results.append({
                "name": name,
                "pid": str(command.command),
                "description": command.desc,
                "unit": str(command.unit),
                "supported": supported,
                "value": value,
                "time_ms": elapsed_ms,
            })

        except Exception as e:
            print(f"ERROR: {e}")

            results.append({
                "name": name,
                "pid": str(command.command),
                "description": command.desc,
                "unit": str(command.unit),
                "supported": False,
                "value": f"ERROR: {e}",
                "time_ms": "",
            })

        time.sleep(0.08)

    connection.close()

    supported = [r for r in results if r["supported"]]
    unsupported = [r for r in results if not r["supported"]]

    print("\n==============================")
    print("OBD-II TEST COMPLETE")
    print("==============================")
    print(f"Total tested: {len(results)}")
    print(f"Supported: {len(supported)}")
    print(f"Unsupported / no data: {len(unsupported)}")

    print("\nSupported commands:")
    for r in supported:
        print(f"- {r['name']}: {r['value']}")

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "name",
                "pid",
                "description",
                "unit",
                "supported",
                "value",
                "time_ms",
            ],
        )
        writer.writeheader()
        writer.writerows(results)

    print(f"\nSaved full results to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
