# Databricks notebook source
import json
from collections import Counter

BASE_PATH = (
    "abfss://bronze@"
    "stf1lakehouse290.dfs.core.windows.net/"
    "jolpica/race_results"
)

SEASONS = range(2021, 2026)
PAGE_LIMIT = 100

# COMMAND ----------

for season in SEASONS:
    path = f"{BASE_PATH}/season={season}/"

    files = dbutils.fs.ls(path)

    json_files = [
        file for file in files
        if file.name.endswith(".json")
    ]

    print(f"Season {season}: {len(json_files)} JSON files")

# COMMAND ----------

def validate_season(season):
    path = f"{BASE_PATH}/season={season}/"

    files = [
        file for file in dbutils.fs.ls(path)
        if file.name.endswith(".json")
    ]

    keys = []
    offsets = []
    totals = set()
    errors = []

    for file in files:
        content = dbutils.fs.head(file.path, file.size + 1)
        data = json.loads(content)

        metadata = data["MRData"]

        total = int(metadata["total"])
        offset = int(metadata["offset"])
        limit = int(metadata["limit"])

        totals.add(total)
        offsets.append(offset)

        if limit != PAGE_LIMIT:
            errors.append(f"Invalid limit: {file.name}")

        if file.name != f"offset_{offset}.json":
            errors.append(f"Invalid filename: {file.name}")

        page_count = 0

        for race in metadata["RaceTable"]["Races"]:
            for result in race["Results"]:
                key = (
                    race["season"],
                    race["round"],
                    result["Driver"]["driverId"]
                )

                keys.append(key)
                page_count += 1

                if int(race["season"]) != season:
                    errors.append("Incorrect season")

        expected_count = min(PAGE_LIMIT, total - offset)

        if page_count != expected_count:
            errors.append(f"Invalid record count: {file.name}")

    if len(totals) != 1:
        errors.append("Missing or inconsistent totals")

    expected_total = max(totals, default=0)

    expected_offsets = set(
        range(0, expected_total, PAGE_LIMIT)
    )

    missing_offsets = expected_offsets - set(offsets)
    unexpected_offsets = set(offsets) - expected_offsets

    duplicates = sum(
        count - 1
        for count in Counter(keys).values()
        if count > 1
    )

    passed = (
        expected_total > 0
        and len(keys) == expected_total
        and duplicates == 0
        and not missing_offsets
        and not unexpected_offsets
        and not errors
    )

    return {
        "season": season,
        "files": len(files),
        "expected": expected_total,
        "actual": len(keys),
        "duplicates": duplicates,
        "missing_offsets": sorted(missing_offsets),
        "unexpected_offsets": sorted(unexpected_offsets),
        "errors": errors,
        "status": "PASS" if passed else "FAIL"
    }

# COMMAND ----------

reports = [
    validate_season(season)
    for season in SEASONS
]

for report in reports:
    print(json.dumps(report, indent=2))

total_records = sum(
    report["actual"] for report in reports
)

print(f"\nTotal records: {total_records}")

assert all(
    report["status"] == "PASS"
    for report in reports
), "Bronze validation failed"

print("All seasons passed validation.")