# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC
# MAGIC # Bronze to Silver Transformations
# MAGIC
# MAGIC Formula 1 race results processing with PySpark,
# MAGIC Delta Lake and Unity Catalog.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Configuration
# MAGIC Import required PySpark modules and define source and target storage locations.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql import types as T

BRONZE_PATH = (
    "abfss://bronze@"
    "stf1lakehouse290.dfs.core.windows.net/"
    "jolpica/race_results"
)

SILVER_PATH = (
    "abfss://silver@"
    "stf1lakehouse290.dfs.core.windows.net/"
    "race_results"
)

SILVER_TABLE = "f1_lakehouse.silver.race_results"

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Bronze Schema
# MAGIC Define an explicit JSON schema to ensure consistent data types and predictable handling of optional field

# COMMAND ----------

BRONZE_SCHEMA = """
MRData STRUCT<
    total: STRING,
    limit: STRING,
    offset: STRING,
    RaceTable: STRUCT<
        Races: ARRAY<STRUCT<
            season: STRING,
            round: STRING,
            raceName: STRING,
            date: STRING,
            time: STRING,
            Circuit: STRUCT<
                circuitId: STRING,
                circuitName: STRING,
                Location: STRUCT<
                    locality: STRING,
                    country: STRING,
                    lat: STRING,
                    long: STRING
                >
            >,
            Results: ARRAY<STRUCT<
                number: STRING,
                grid: STRING,
                position: STRING,
                positionText: STRING,
                points: STRING,
                laps: STRING,
                status: STRING,
                Driver: STRUCT<
                    driverId: STRING,
                    code: STRING,
                    givenName: STRING,
                    familyName: STRING,
                    dateOfBirth: STRING,
                    nationality: STRING
                >,
                Constructor: STRUCT<
                    constructorId: STRING,
                    name: STRING,
                    nationality: STRING
                >,
                Time: STRUCT<
                    millis: STRING
                >,
                FastestLap: STRUCT<
                    rank: STRING,
                    lap: STRING,
                    Time: STRUCT<
                        time: STRING
                    >
                >
            >>
        >>
    >
>
"""

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Read Bronze Data
# MAGIC Load raw JSON files from ADLS Gen2 using the predefined schema.

# COMMAND ----------

df_bronze = (
    spark.read
    .schema(BRONZE_SCHEMA)
    .option("multiLine", "true")
    .option("recursiveFileLookup", "true")
    .option("pathGlobFilter", "*.json")
    .option("mode", "FAILFAST")
    .json(BRONZE_PATH)
)

display(df_bronze)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 04. Data Exploration
# MAGIC
# MAGIC Inspect the source schema, record counts and API metadata before applying transformations.

# COMMAND ----------

df_bronze.printSchema()

# COMMAND ----------

print(f"Raw rows: {df_bronze.count()}")

display(
    df_bronze.select(
        "MRData.total",
        "MRData.limit",
        "MRData.offset"
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 05. Flatten Nested JSON
# MAGIC
# MAGIC Explode nested race and result arrays to obtain one record per driver per race. Extract relevant race, circuit, driver, constructor and performance attributes.

# COMMAND ----------

df_races = df_bronze.select(
    F.explode("MRData.RaceTable.Races").alias("race")
)

display(df_races)

# COMMAND ----------

df_results = df_races.select(
    F.col("race"),
    F.explode("race.Results").alias("result")
)

display(df_results)

print(f"Race result rows: {df_results.count()}")

# COMMAND ----------

df_flat = df_results.select(
    # Race
    F.col("race.season").alias("season"),
    F.col("race.round").alias("round"),
    F.col("race.raceName").alias("race_name"),
    F.col("race.date").alias("race_date"),
    F.col("race.time").alias("race_time"),

    # Circuit
    F.col("race.Circuit.circuitId").alias("circuit_id"),
    F.col("race.Circuit.circuitName").alias("circuit_name"),
    F.col("race.Circuit.Location.locality").alias("city"),
    F.col("race.Circuit.Location.country").alias("country"),
    F.col("race.Circuit.Location.lat").alias("latitude"),
    F.col("race.Circuit.Location.long").alias("longitude"),

    # Driver
    F.col("result.Driver.driverId").alias("driver_id"),
    F.col("result.Driver.code").alias("driver_code"),
    F.col("result.Driver.givenName").alias("first_name"),
    F.col("result.Driver.familyName").alias("last_name"),
    F.col("result.Driver.dateOfBirth").alias("date_of_birth"),
    F.col("result.Driver.nationality").alias("driver_nationality"),

    # Constructor
    F.col("result.Constructor.constructorId").alias("constructor_id"),
    F.col("result.Constructor.name").alias("constructor_name"),
    F.col("result.Constructor.nationality").alias("constructor_nationality"),

    # Race result
    F.col("result.number").alias("driver_number"),
    F.col("result.grid").alias("grid_position"),
    F.col("result.position").alias("position"),
    F.col("result.positionText").alias("position_text"),
    F.col("result.points").alias("points"),
    F.col("result.laps").alias("laps_completed"),
    F.col("result.status").alias("status"),
    F.col("result.Time.millis").alias("race_time_ms"),
    F.col("result.FastestLap.rank").alias("fastest_lap_rank"),
    F.col("result.FastestLap.lap").alias("fastest_lap_number"),
    F.col("result.FastestLap.Time.time").alias("fastest_lap_time")
)

display(df_flat)

# COMMAND ----------

df_flat.printSchema()

print(f"Rows: {df_flat.count()}")
print(f"Columns: {len(df_flat.columns)}")

display(
    df_flat.groupBy("season")
    .count()
    .orderBy("season")
)

display(
    df_flat.groupBy("status", "position_text")
    .count()
    .orderBy(F.desc("count"))
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 06. Data Type Conversion
# MAGIC
# MAGIC Convert source strings into appropriate integer, decimal, double and date types. Preserve decimal championship points.

# COMMAND ----------

df_typed = (
    df_flat
    .withColumn("season", F.col("season").cast(T.IntegerType()))
    .withColumn("round", F.col("round").cast(T.IntegerType()))
    .withColumn("race_date", F.to_date("race_date", "yyyy-MM-dd"))
    .withColumn("date_of_birth", F.to_date("date_of_birth", "yyyy-MM-dd"))
    .withColumn("latitude", F.col("latitude").cast(T.DoubleType()))
    .withColumn("longitude", F.col("longitude").cast(T.DoubleType()))
    .withColumn("driver_number", F.col("driver_number").cast(T.IntegerType()))
    .withColumn("grid_position", F.col("grid_position").cast(T.IntegerType()))
    .withColumn("position", F.col("position").cast(T.IntegerType()))
    .withColumn("points", F.col("points").cast(T.DecimalType(6, 2)))
    .withColumn("laps_completed", F.col("laps_completed").cast(T.IntegerType()))
    .withColumn("race_time_ms", F.col("race_time_ms").cast(T.LongType()))
    .withColumn("fastest_lap_rank", F.col("fastest_lap_rank").cast(T.IntegerType()))
    .withColumn("fastest_lap_number", F.col("fastest_lap_number").cast(T.IntegerType()))
)

df_typed.printSchema()
display(df_typed)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 07. Data Cleaning
# MAGIC
# MAGIC Normalize empty strings to NULL and inspect missing values. Preserve missing optional attributes without introducing artificial values.

# COMMAND ----------

df_clean = df_typed

string_columns = [
    field.name
    for field in df_clean.schema.fields
    if isinstance(field.dataType, T.StringType)
]

for column in string_columns:
    df_clean = df_clean.withColumn(
        column,
        F.when(
            F.trim(F.col(column)) == "",
            F.lit(None)
        ).otherwise(F.trim(F.col(column)))
    )

display(df_clean)

# COMMAND ----------

display(
    df_clean.groupBy("status")
    .count()
    .orderBy(F.desc("count"))
)

display(
    df_clean.groupBy("position_text")
    .count()
    .orderBy(F.desc("count"))
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 08. Deduplication
# MAGIC
# MAGIC Remove exact duplicate records and validate uniqueness using the composite business key: season, round and driver_id. Reject conflicting records.

# COMMAND ----------

BUSINESS_KEY = ["season", "round", "driver_id"]

df_duplicates = (
    df_clean
    .groupBy(*BUSINESS_KEY)
    .count()
    .filter(F.col("count") > 1)
)

duplicate_keys = df_duplicates.count()

print(f"Duplicate business keys: {duplicate_keys}")

display(df_duplicates)

# COMMAND ----------

rows_before = df_clean.count()

df_deduplicated = df_clean.dropDuplicates()

rows_after = df_deduplicated.count()

print(f"Rows before deduplication: {rows_before}")
print(f"Rows after deduplication: {rows_after}")
print(f"Removed duplicates: {rows_before - rows_after}")

# COMMAND ----------

remaining_duplicates = (
    df_deduplicated
    .groupBy(*BUSINESS_KEY)
    .count()
    .filter(F.col("count") > 1)
    .count()
)

assert remaining_duplicates == 0, (
    "Conflicting records detected for the business key"
)

print("Business key uniqueness: PASSED")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 09. Business Logic and Derived Columns
# MAGIC
# MAGIC Analyze race statuses and derive classification, finishing positions, positions gained, wins, podiums and DNF, DNS and DSQ flags.

# COMMAND ----------

display(
    df_deduplicated
    .groupBy("status")
    .count()
    .orderBy(F.desc("count"))
)

display(
    df_deduplicated
    .filter(
        ~F.col("position_text").rlike("^[0-9]+$")
        | F.col("position_text").isNull()
    )
    .groupBy("position_text", "status")
    .count()
    .orderBy(F.desc("count"))
)

# COMMAND ----------

df_enriched = (
    df_deduplicated
    .withColumn(
        "is_classified",
        F.coalesce(
            F.col("position_text").rlike("^[1-9][0-9]*$"),
            F.lit(False)
        )
    )
    .withColumn(
        "finish_position",
        F.when(
            F.col("is_classified"),
            F.col("position_text").cast(T.IntegerType())
        )
    )
    .withColumn(
        "positions_gained",
        F.when(
            F.col("is_classified")
            & (F.col("grid_position") > 0),
            F.col("grid_position") - F.col("finish_position")
        )
    )
)

display(df_enriched)

# COMMAND ----------

df_enriched = (
    df_enriched
    .withColumn(
        "is_win",
        F.coalesce(
            F.col("finish_position") == 1,
            F.lit(False)
        )
    )
    .withColumn(
        "is_podium",
        F.coalesce(
            F.col("finish_position").between(1, 3),
            F.lit(False)
        )
    )
)

display(
    df_enriched.select(
        "season",
        "round",
        "driver_id",
        "grid_position",
        "position",
        "position_text",
        "finish_position",
        "positions_gained",
        "is_classified",
        "is_win",
        "is_podium"
    )
)

# COMMAND ----------

status = F.lower(F.col("status"))

df_enriched = (
    df_enriched
    .withColumn(
        "is_dsq",
        (status == "disqualified")
        | (F.col("position_text") == "D")
    )
    .withColumn(
        "is_dns",
        (status == "did not start")
        | (
            (F.col("position_text") == "W")
            & (F.col("laps_completed") == 0)
        )
    )
    .withColumn(
        "is_dnf",
        ~F.col("is_dsq")
        & ~F.col("is_dns")
        & ~(
            status.isin("finished", "lapped")
            | status.rlike(r"^\+\d+ laps?$")
        )
    )
)

display(
    df_enriched.groupBy(
        "is_dnf", "is_dns", "is_dsq"
    ).count()
)

# COMMAND ----------

df_enriched = (
    df_enriched
    .withColumn(
        "is_classified",
        F.col("is_classified")
        & ~F.col("is_dsq")
        & ~F.col("is_dns")
    )
    .withColumn(
        "finish_position",
        F.when(
            F.col("is_classified"),
            F.col("position_text").cast("int")
        )
    )
    .withColumn(
        "positions_gained",
        F.when(
            F.col("is_classified")
            & (F.col("grid_position") > 0),
            F.col("grid_position")
            - F.col("finish_position")
        )
    )
    .withColumn(
        "is_win",
        F.coalesce(
            F.col("finish_position") == 1,
            F.lit(False)
        )
    )
    .withColumn(
        "is_podium",
        F.coalesce(
            F.col("finish_position").between(1, 3),
            F.lit(False)
        )
    )
)

# COMMAND ----------

display(
    df_enriched.agg(
        F.count("*").alias("total_records"),
        *[
            F.sum(F.col(column).cast("int")).alias(column)
            for column in [
                "is_classified",
                "is_dnf",
                "is_dns",
                "is_dsq",
                "is_win",
                "is_podium"
            ]
        ]
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 10. Data Quality Validation
# MAGIC
# MAGIC Validate required attributes, numeric ranges, business rules and completeness against Bronze API metadata.

# COMMAND ----------

REQUIRED_COLUMNS = [
    "season",
    "round",
    "driver_id",
    "constructor_id",
    "circuit_id",
    "race_date",
    "grid_position",
    "position",
    "position_text",
    "points",
    "laps_completed",
    "status"
]

null_counts = df_enriched.select(
    *[
        F.count(
            F.when(F.col(column).isNull(), 1)
        ).alias(column)
        for column in REQUIRED_COLUMNS
    ]
).first().asDict()

for column, count in null_counts.items():
    assert count == 0, f"Missing values in {column}: {count}"

print("Required columns validation: PASSED")

# COMMAND ----------

invalid_records = df_enriched.filter(
    (~F.col("season").between(2021, 2025))
    | (F.col("round") <= 0)
    | (F.col("grid_position") < 0)
    | (F.col("position") <= 0)
    | (F.col("points") < 0)
    | (F.col("laps_completed") < 0)
)

invalid_count = invalid_records.count()

assert invalid_count == 0, (
    f"Invalid records detected: {invalid_count}"
)

print("Value range validation: PASSED")

# COMMAND ----------

invalid_business_logic = df_enriched.filter(
    (F.col("is_win") & ~F.col("is_podium"))
    | (F.col("is_classified") & F.col("finish_position").isNull())
    | (~F.col("is_classified") & F.col("finish_position").isNotNull())
    | (F.col("is_dsq") & F.col("is_classified"))
    | (F.col("is_dns") & F.col("is_classified"))
    | (F.col("is_dnf") & F.col("is_dns"))
    | (F.col("is_dnf") & F.col("is_dsq"))
    | (F.col("is_dns") & F.col("is_dsq"))
    | (
        (F.col("grid_position") == 0)
        & F.col("positions_gained").isNotNull()
    )
)

invalid_count = invalid_business_logic.count()

assert invalid_count == 0, (
    f"Business logic violations: {invalid_count}"
)

print("Business logic validation: PASSED")

# COMMAND ----------

df_expected = (
    df_bronze
    .select(
        F.explode("MRData.RaceTable.Races").alias("race"),
        F.col("MRData.total").cast("int").alias("total")
    )
    .select(
        F.col("race.season").cast("int").alias("season"),
        "total"
    )
    .distinct()
)

metadata = df_expected.collect()

expected_counts = {}

for row in metadata:
    season = row["season"]
    total = row["total"]

    assert season is not None
    assert total is not None and total > 0

    if season in expected_counts:
        assert expected_counts[season] == total, (
            f"Inconsistent metadata for season {season}"
        )

    expected_counts[season] = total

actual_counts = {
    row["season"]: row["count"]
    for row in df_enriched.groupBy("season").count().collect()
}

assert set(expected_counts) == set(range(2021, 2026))

assert actual_counts == expected_counts, (
    f"Expected: {expected_counts}, Actual: {actual_counts}"
)

assert df_enriched.count() == rows_after

print(f"Expected counts: {expected_counts}")
print(f"Actual counts: {actual_counts}")
print("Data completeness validation: PASSED")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 11. Write Silver Delta Table
# MAGIC
# MAGIC Persist validated records in Delta Lake format using a Full Refresh strategy.

# COMMAND ----------

df_silver = df_enriched

print(f"Total records: {df_silver.count()}")
print(f"Total columns: {len(df_silver.columns)}")

df_silver.printSchema()

# COMMAND ----------

(
    df_silver.write
    .format("delta")
    .mode("overwrite")
    .save(SILVER_PATH)
)

print("Silver Delta write: COMPLETED")
print(f"Storage path: {SILVER_PATH}")

# COMMAND ----------

display(dbutils.fs.ls(SILVER_PATH))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 12. Silver Read-Back Validation
# MAGIC
# MAGIC Verify persisted record counts, column names and data types.

# COMMAND ----------

df_silver_read = (
    spark.read
    .format("delta")
    .load(SILVER_PATH)
)

assert df_silver_read.count() == df_silver.count(), (
    "Silver record count mismatch"
)

assert df_silver_read.dtypes == df_silver.dtypes, (
    "Silver column names or data types mismatch"
)

print(f"Silver records: {df_silver_read.count()}")
print(f"Silver columns: {len(df_silver_read.columns)}")
print("Silver read-back validation: PASSED")

display(df_silver_read)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 13. Unity Catalog Registration
# MAGIC
# MAGIC Register the existing Delta storage location as an external table and inspect its metadata.

# COMMAND ----------

spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {SILVER_TABLE}
    USING DELTA
    LOCATION '{SILVER_PATH}'
""")

print(f"Silver table registered: {SILVER_TABLE}")

# COMMAND ----------

display(
    spark.sql(f"DESCRIBE DETAIL {SILVER_TABLE}")
)

# COMMAND ----------

display(
    spark.sql(f"DESCRIBE EXTENDED {SILVER_TABLE}")
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 14. SQL Exploration
# MAGIC
# MAGIC Analyze race counts, driver counts and championship points by season using SQL

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT
# MAGIC     season,
# MAGIC     COUNT(*) AS total_records,
# MAGIC     COUNT(DISTINCT round) AS total_races,
# MAGIC     COUNT(DISTINCT driver_id) AS total_drivers,
# MAGIC     SUM(points) AS total_points
# MAGIC FROM f1_lakehouse.silver.race_results
# MAGIC GROUP BY season
# MAGIC ORDER BY season;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 15. Final Validation and Idempotency
# MAGIC
# MAGIC Validate registered table content and business key uniqueness. Inspect Delta transaction history and repeated execution results.

# COMMAND ----------

df_registered = spark.table(SILVER_TABLE)

assert df_registered.count() == df_silver.count(), (
    "Registered table record count mismatch"
)

assert df_registered.dtypes == df_silver.dtypes, (
    "Registered table schema mismatch"
)

assert df_registered.exceptAll(df_silver).count() == 0
assert df_silver.exceptAll(df_registered).count() == 0

print("Unity Catalog table validation: PASSED")

# COMMAND ----------

df_final = spark.table(SILVER_TABLE)

assert df_final.count() == sum(expected_counts.values())

assert (
    df_final.groupBy(*BUSINESS_KEY)
    .count()
    .filter(F.col("count") > 1)
    .count()
) == 0

assert df_final.exceptAll(df_silver).count() == 0
assert df_silver.exceptAll(df_final).count() == 0

print("Silver content consistency validation: PASSED")

display(
    spark.sql(f"DESCRIBE HISTORY {SILVER_TABLE}")
)