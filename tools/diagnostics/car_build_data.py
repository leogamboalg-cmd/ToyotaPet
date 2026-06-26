import requests

vin_number = "5YFBURHE3JP785915"
url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin_number}?format=json"

try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    data = response.json()

    print("\n--- 2018 Toyota Corolla Specs ---")

    wanted = [
        "Make",
        "Model",
        "Model Year",
        "Trim",
        "Drive Type",
        "Engine Number of Cylinders",
        "Displacement (L)",
        "Fuel Type - Primary",
        "Transmission Style",
    ]

    for item in data.get("Results", []):
        variable = item.get("Variable")
        value = item.get("Value")

        if variable in wanted and value:
            print(f"{variable}: {value}")

except requests.exceptions.RequestException as e:
    print(f"Network/API error: {e}")
except ValueError:
    print("Error: API did not return valid JSON")
