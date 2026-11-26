
import requests
import json
from pathlib import Path


BASE_URL = "https://api.jolpi.ca/ergast/f1"
SEASON = 2025

url = f"{BASE_URL}/{SEASON}/results/"

params = {
    "limit": 5,
    "offset": 0
}

response = requests.get(
    url,
    params=params,
    timeout=30
)

response.raise_for_status()

data = response.json()

# Extract pagination metadata
metadata = data["MRData"]

total = int(metadata["total"])
limit = int(metadata["limit"])
offset = int(metadata["offset"])

print(f"Total records: {total}")
print(f"Limit: {limit}")
print(f"Offset: {offset}")

# Extract race data
races = metadata["RaceTable"]["Races"]

for race in races:

    print(f"\nRace: {race['raceName']}")
    print(f"Circuit: {race['Circuit']['circuitName']}")
    print(f"Date: {race['date']}\n")

    for result in race["Results"]:

        driver = result["Driver"]
        constructor = result["Constructor"]

        driver_name = (
            f"{driver['givenName']} "
            f"{driver['familyName']}"
        )

        position = int(result["position"])
        points = float(result["points"])
        grid = int(result["grid"])
        laps = int(result["laps"])
        status = result["status"]
        positions_gained = int(result["grid"]) - int(result["position"])
        driverId = driver["driverId"]

        print(
            f"{position}. {driver_name} | "
            f"{constructor['name']} | "
            f"Grid: {grid} | "
            f"Laps: {laps} | "
            f"Points: {points} | "
            f"Status: {status} | "
            f"Positions Gained: {positions_gained} | "
            f"Driver ID: {driverId}"
        )

# Save sample API response
project_root = Path(__file__).resolve().parents[1]

output_path = (
    project_root
    / "data"
    / "sample"
    / "race_results_2025.json"
)

output_path.parent.mkdir(parents=True, exist_ok=True)

with output_path.open("w", encoding="utf-8") as file:
    json.dump(data, file, indent=4, ensure_ascii=False)

print(f"\nSample data saved to: {output_path}")