# Databricks notebook source
# MAGIC %md
# MAGIC # End-to-End Pipeline Validation
# MAGIC
# MAGIC Validates the consistency of the F1 lakehouse after
# MAGIC a full historical load and a selected season refresh.
# MAGIC
# MAGIC Validation scope:
# MAGIC - Record counts
# MAGIC - Business key uniqueness
# MAGIC - Delta Time Travel content comparison
# MAGIC - Bronze storage completeness
# MAGIC - Analytics view availability
# MAGIC - Points reconciliation

# COMMAND ----------

from pyspark.sql import functions as F

TABLES = {
    "f1_lakehouse.silver.race_results": 2278,
    "f1_lakehouse.gold.dim_drivers": 35,
    "f1_lakehouse.gold.dim_constructors": 12,
    "f1_lakehouse.gold.dim_circuits": 28,
    "f1_lakehouse.gold.dim_races": 114,
    "f1_lakehouse.gold.fact_race_results": 2278
}

# COMMAND ----------

for table_name, expected_count in TABLES.items():
    actual_count = spark.table(table_name).count()

    assert actual_count == expected_count, (
        f"{table_name}: expected {expected_count}, "
        f"got {actual_count}"
    )

    print(f"{table_name}: {actual_count} rows - PASSED")

print("\nRecord count validation: PASSED")

# COMMAND ----------

BUSINESS_KEYS = {
    "f1_lakehouse.silver.race_results":
        ["season", "round", "driver_id"],

    "f1_lakehouse.gold.dim_drivers":
        ["driver_id"],

    "f1_lakehouse.gold.dim_constructors":
        ["constructor_id"],

    "f1_lakehouse.gold.dim_circuits":
        ["circuit_id"],

    "f1_lakehouse.gold.dim_races":
        ["race_id"],

    "f1_lakehouse.gold.fact_race_results":
        ["race_id", "driver_id"]
}

for table_name, keys in BUSINESS_KEYS.items():
    duplicates = (
        spark.table(table_name)
        .groupBy(*keys)
        .count()
        .filter(F.col("count") > 1)
        .count()
    )

    assert duplicates == 0, (
        f"{table_name}: duplicate keys detected"
    )

    print(f"{table_name}: 0 duplicate keys - PASSED")

print("\nBusiness key validation: PASSED")

# COMMAND ----------

for table_name in TABLES:
    versions = (
        spark.sql(f"DESCRIBE HISTORY {table_name}")
        .filter(F.col("operation") == "WRITE")
        .orderBy(F.desc("version"))
        .select("version")
        .limit(2)
        .collect()
    )

    assert len(versions) == 2, (
        f"{table_name}: insufficient write history"
    )

    current_version = versions[0]["version"]
    previous_version = versions[1]["version"]

    df_current = (
        spark.read.format("delta")
        .option("versionAsOf", current_version)
        .table(table_name)
    )

    df_previous = (
        spark.read.format("delta")
        .option("versionAsOf", previous_version)
        .table(table_name)
    )

    assert df_current.dtypes == df_previous.dtypes

    assert df_current.exceptAll(df_previous).count() == 0
    assert df_previous.exceptAll(df_current).count() == 0

    print(
        f"{table_name}: "
        f"v{previous_version} -> v{current_version} - PASSED"
    )

print("\nDelta content consistency: PASSED")

# COMMAND ----------

BRONZE_PATH = (
    "abfss://bronze@stf1lakehouse290.dfs.core.windows.net"
    "/jolpica/race_results"
)

total_files = 0

for season in range(2021, 2026):
    files = dbutils.fs.ls(
        f"{BRONZE_PATH}/season={season}"
    )

    actual_files = {
        file.name for file in files
        if file.name.endswith(".json")
    }

    expected_files = {
        f"offset_{offset}.json"
        for offset in range(0, 500, 100)
    }

    assert actual_files == expected_files, (
        f"Season {season}: unexpected Bronze files"
    )

    total_files += len(actual_files)

    print(
        f"Season {season}: "
        f"{len(actual_files)} files - PASSED"
    )

assert total_files == 25

print(f"\nTotal Bronze files: {total_files}")
print("Bronze storage validation: PASSED")

# COMMAND ----------

ANALYTICS_SCHEMA = "f1_lakehouse.analytics"

EXPECTED_VIEWS = [
    "vw_race_results",
    "vw_driver_circuit_history",
    "vw_driver_circuit_performance",
    "vw_driver_positions_gained",
    "vw_driver_season_performance",
    "vw_constructor_circuit_performance"
]

for view_name in EXPECTED_VIEWS:
    full_name = f"{ANALYTICS_SCHEMA}.{view_name}"

    row_count = spark.table(full_name).count()

    assert row_count > 0, (
        f"{view_name}: empty view"
    )

    print(f"{view_name}: {row_count} rows - PASSED")

print("\nAnalytics views validation: PASSED")

# COMMAND ----------

from decimal import Decimal

POINTS_SOURCES = [
    "f1_lakehouse.silver.race_results",
    "f1_lakehouse.gold.fact_race_results",
    "f1_lakehouse.analytics.vw_race_results"
]

EXPECTED_POINTS = Decimal("11540.50")

for table_name in POINTS_SOURCES:
    total_points = (
        spark.table(table_name)
        .agg(F.sum("points").alias("total_points"))
        .first()["total_points"]
    )

    assert total_points == EXPECTED_POINTS, (
        f"{table_name}: points mismatch"
    )

    print(f"{table_name}: {total_points} - PASSED")

print("\nPoints reconciliation: PASSED")
print("END-TO-END DATA VALIDATION: PASSED")