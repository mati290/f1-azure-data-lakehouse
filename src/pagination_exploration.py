
import time
import requests

BASE_URL = "https://api.jolpi.ca/ergast/f1"
SEASON = 2025
LIMIT = 100

url = f"{BASE_URL}/{SEASON}/results/"

offset = 0
all_results = []

while True:

    params = {
        "limit": LIMIT,
        "offset": offset
    }

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()
    metadata = data["MRData"]

    total = int(metadata["total"])
    races = metadata["RaceTable"]["Races"]

    page_count = 0

    for race in races:
        for result in race["Results"]:

            all_results.append({
                "season": race["season"],
                "round": race["round"],
                "race_name": race["raceName"],
                "circuit_id": race["Circuit"]["circuitId"],
                "driver_id": result["Driver"]["driverId"],
                "constructor_id": result["Constructor"]["constructorId"],
                "position": int(result["position"]),
                "points": float(result["points"]),
                "grid": int(result["grid"]),
                "status": result["status"]
            })

            page_count += 1

    print(
        f"Offset: {offset} | "
        f"Downloaded: {page_count} | "
        f"Progress: {len(all_results)}/{total}"
    )

    if len(all_results) >= total:
        break

    if page_count == 0:
        raise RuntimeError("Unexpected empty API page")

    offset += page_count

    time.sleep(2)

print("\nDownload completed.")
print(f"Total downloaded: {len(all_results)}")
print(f"Expected records: {total}")

assert len(all_results) == total


# Data quality checks
unique_keys = {
    (
        result["season"],
        result["round"],
        result["driver_id"]
    )
    for result in all_results
}

duplicates = len(all_results) - len(unique_keys)

print("\nData Quality Report")
print(f"Total records: {len(all_results)}")
print(f"Unique records: {len(unique_keys)}")
print(f"Duplicates: {duplicates}")

assert duplicates == 0, "Duplicate records detected"





