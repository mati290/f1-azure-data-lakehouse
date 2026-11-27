# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC # Silver to Gold – Dimensional Model
# MAGIC
# MAGIC ## Objective
# MAGIC
# MAGIC Transform validated Formula 1 race results into a
# MAGIC dimensional model optimized for analytical queries.
# MAGIC
# MAGIC - Source: f1_lakehouse.silver.race_results
# MAGIC - Target: f1_lakehouse.gold
# MAGIC - Data scope: 2021–2025
# MAGIC - Data model: Star Schema
# MAGIC - Processing engine: PySpark
# MAGIC - Storage format: Delta Lake
# MAGIC - Load strategy: Full Refresh
# MAGIC - Fact grain: One driver result per race

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## 01. Configuration
# MAGIC
# MAGIC Import required PySpark modules and define
# MAGIC the source table, target schema and Gold storage path.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql import types as T
from pyspark.sql.window import Window

SILVER_TABLE = "f1_lakehouse.silver.race_results"

GOLD_SCHEMA = "f1_lakehouse.gold"

GOLD_PATH = (
    "abfss://gold@"
    "stf1lakehouse290.dfs.core.windows.net/"
)

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## 02. Read Silver Data
# MAGIC
# MAGIC Load validated race results from the Silver
# MAGIC Unity Catalog table and inspect the source dataset.

# COMMAND ----------

df_silver = spark.table(SILVER_TABLE)

print(f"Total records: {df_silver.count()}")
print(f"Total columns: {len(df_silver.columns)}")

df_silver.printSchema()

display(df_silver)

# COMMAND ----------

display(
    df_silver.agg(
        F.count("*").alias("total_records"),

        F.countDistinct("driver_id")
        .alias("total_drivers"),

        F.countDistinct("constructor_id")
        .alias("total_constructors"),

        F.countDistinct("circuit_id")
        .alias("total_circuits"),

        F.countDistinct("season", "round")
        .alias("total_races")
    )
)

# COMMAND ----------

# MAGIC
# MAGIC %md
# MAGIC
# MAGIC ## 03. Generate Race Identifier
# MAGIC
# MAGIC Create a deterministic race identifier using
# MAGIC the season and round number.
# MAGIC
# MAGIC The identifier is used as the primary key
# MAGIC of the race dimension and as a foreign key
# MAGIC in the race results fact table.

# COMMAND ----------

df_base = df_silver.withColumn(
    "race_id",
    F.concat(
        F.col("season").cast("string"),
        F.lit("_"),
        F.lpad(
            F.col("round").cast("string"),
            2,
            "0"
        )
    )
)

display(
    df_base.select(
        "race_id",
        "season",
        "round",
        "race_name",
        "race_date"
    )
    .distinct()
    .orderBy("season", "round")
)

# COMMAND ----------

FACT_KEY = ["race_id", "driver_id"]

duplicate_keys = (
    df_base
    .groupBy(*FACT_KEY)
    .count()
    .filter(F.col("count") > 1)
    .count()
)

assert duplicate_keys == 0, (
    "Duplicate race-driver keys detected"
)

assert df_base.filter(
    F.col("race_id").isNull()
    | F.col("driver_id").isNull()
).count() == 0, "Missing business keys"

print("Fact business key validation: PASSED")

# COMMAND ----------

# MAGIC
# MAGIC %md
# MAGIC
# MAGIC ## 04. Driver Dimension
# MAGIC
# MAGIC Create a driver dimension containing one record
# MAGIC per unique driver.
# MAGIC
# MAGIC Use a window function to select the latest available
# MAGIC driver attributes based on season and round.
# MAGIC
# MAGIC Apply a Type 1 dimension strategy without storing
# MAGIC historical attribute versions.
# MAGIC
# MAGIC Primary key: driver_id

# COMMAND ----------

def select_latest_record(df, key_column):
    window_spec = (
        Window
        .partitionBy(key_column)
        .orderBy(
            F.col("season").desc(),
            F.col("round").desc(),
            F.col("driver_id").asc()
        )
    )

    return (
        df
        .withColumn(
            "_row_number",
            F.row_number().over(window_spec)
        )
        .filter(F.col("_row_number") == 1)
        .drop("_row_number")
    )

# COMMAND ----------

df_dim_drivers = (
    select_latest_record(df_base, "driver_id")
    .select(
        "driver_id",
        "driver_code",
        "first_name",
        "last_name",

        F.concat_ws(
            " ",
            F.col("first_name"),
            F.col("last_name")
        ).alias("full_name"),

        "date_of_birth",

        F.col("driver_nationality")
        .alias("nationality")
    )
)

display(
    df_dim_drivers.orderBy("last_name")
)

print(f"Total drivers: {df_dim_drivers.count()}")

# COMMAND ----------

expected_drivers = (
    df_base
    .select("driver_id")
    .distinct()
    .count()
)

actual_drivers = df_dim_drivers.count()

assert actual_drivers == expected_drivers, (
    "Driver dimension record count mismatch"
)

assert (
    df_dim_drivers
    .groupBy("driver_id")
    .count()
    .filter(F.col("count") > 1)
    .count()
) == 0, "Duplicate driver IDs"

assert (
    df_dim_drivers
    .filter(F.col("driver_id").isNull())
    .count()
) == 0, "Missing driver IDs"

print(f"Expected drivers: {expected_drivers}")
print(f"Actual drivers: {actual_drivers}")
print("Driver dimension validation: PASSED")

# COMMAND ----------

# MAGIC
# MAGIC %md
# MAGIC
# MAGIC ## 05. Constructor Dimension
# MAGIC
# MAGIC Create a constructor dimension containing one
# MAGIC record per unique constructor.
# MAGIC
# MAGIC Select the latest available constructor attributes
# MAGIC using the reusable window function.
# MAGIC
# MAGIC Primary key: constructor_id

# COMMAND ----------

df_dim_constructors = (
    select_latest_record(df_base, "constructor_id")
    .select(
        "constructor_id",
        "constructor_name",

        F.col("constructor_nationality")
        .alias("nationality")
    )
)

display(
    df_dim_constructors.orderBy("constructor_name")
)

print(
    f"Total constructors: {df_dim_constructors.count()}"
)

# COMMAND ----------

def validate_dimension(df, source_df, key_column):
    expected_count = (
        source_df
        .select(key_column)
        .distinct()
        .count()
    )

    actual_count = df.count()

    assert actual_count == expected_count, (
        f"{key_column}: record count mismatch"
    )

    duplicate_count = (
        df
        .groupBy(key_column)
        .count()
        .filter(F.col("count") > 1)
        .count()
    )

    assert duplicate_count == 0, (
        f"{key_column}: duplicate keys detected"
    )

    null_count = (
        df
        .filter(F.col(key_column).isNull())
        .count()
    )

    assert null_count == 0, (
        f"{key_column}: missing keys"
    )

    print(f"Expected records: {expected_count}")
    print(f"Actual records: {actual_count}")
    print(f"Duplicate keys: {duplicate_count}")
    print(f"NULL keys: {null_count}")
    print(f"{key_column} validation: PASSED")

# COMMAND ----------

validate_dimension(
    df_dim_constructors,
    df_base,
    "constructor_id"
)

# COMMAND ----------

# MAGIC
# MAGIC %md
# MAGIC
# MAGIC ## 06. Circuit Dimension
# MAGIC
# MAGIC Create a circuit dimension containing one record
# MAGIC per unique Formula 1 circuit.
# MAGIC
# MAGIC Preserve circuit names, geographical attributes
# MAGIC and coordinates for analytical queries and
# MAGIC future map visualizations.
# MAGIC
# MAGIC Primary key: circuit_id

# COMMAND ----------

df_dim_circuits = (
    select_latest_record(df_base, "circuit_id")
    .select(
        "circuit_id",
        "circuit_name",
        "city",
        "country",
        "latitude",
        "longitude"
    )
)

display(
    df_dim_circuits.orderBy("country", "circuit_name")
)

print(f"Total circuits: {df_dim_circuits.count()}")

# COMMAND ----------

validate_dimension(
    df_dim_circuits,
    df_base,
    "circuit_id"
)

# COMMAND ----------

invalid_coordinates = (
    df_dim_circuits
    .filter(
        (~F.col("latitude").between(-90, 90))
        | (~F.col("longitude").between(-180, 180))
    )
    .count()
)

assert invalid_coordinates == 0, (
    f"Invalid coordinates: {invalid_coordinates}"
)

print("Circuit coordinates validation: PASSED")

# COMMAND ----------

# MAGIC
# MAGIC %md
# MAGIC
# MAGIC ## 07. Race Dimension
# MAGIC
# MAGIC Create a race dimension containing one record
# MAGIC per Formula 1 race.
# MAGIC
# MAGIC Preserve season, round, race name, date and
# MAGIC scheduled start time.
# MAGIC
# MAGIC Primary key: race_id

# COMMAND ----------

df_dim_races = (
    df_base
    .select(
        "race_id",
        "season",
        "round",
        "race_name",
        "race_date",
        "race_time"
    )
    .distinct()
)

display(
    df_dim_races.orderBy("season", "round")
)

print(f"Total races: {df_dim_races.count()}")

# COMMAND ----------

validate_dimension(
    df_dim_races,
    df_base,
    "race_id"
)

# COMMAND ----------

display(
    df_dim_races
    .groupBy("season")
    .count()
    .withColumnRenamed("count", "total_races")
    .orderBy("season")
)

# COMMAND ----------

# MAGIC
# MAGIC %md
# MAGIC
# MAGIC ## 08. Race Results Fact Table
# MAGIC
# MAGIC Create the central fact table containing race
# MAGIC results, performance measures and status flags.
# MAGIC
# MAGIC Grain: One driver result per race.
# MAGIC
# MAGIC Composite primary key:
# MAGIC - race_id
# MAGIC - driver_id
# MAGIC
# MAGIC Foreign keys:
# MAGIC - race_id
# MAGIC - driver_id
# MAGIC - constructor_id
# MAGIC - circuit_id
# MAGIC
# MAGIC Preserve all validated race results, including
# MAGIC DNF, DNS and DSQ records.

# COMMAND ----------

df_fact_race_results = (
    df_base
    .select(
        # Foreign keys
        "race_id",
        "driver_id",
        "constructor_id",
        "circuit_id",

        # Race-specific attributes
        "driver_number",
        "grid_position",
        "position",
        "position_text",
        "finish_position",
        "status",

        # Performance measures
        "points",
        "positions_gained",
        "laps_completed",
        "race_time_ms",
        "fastest_lap_rank",
        "fastest_lap_number",
        "fastest_lap_time",

        # Analytical flags
        "is_classified",
        "is_win",
        "is_podium",
        "is_dnf",
        "is_dns",
        "is_dsq"
    )
)

display(df_fact_race_results)

print(
    f"Total fact records: "
    f"{df_fact_race_results.count()}"
)

print(
    f"Total fact columns: "
    f"{len(df_fact_race_results.columns)}"
)

# COMMAND ----------

# MAGIC
# MAGIC %md
# MAGIC
# MAGIC ## 09. Fact Table Validation
# MAGIC
# MAGIC Validate fact table completeness and composite
# MAGIC primary key uniqueness.
# MAGIC
# MAGIC Ensure that no race results are lost during
# MAGIC the dimensional transformation.

# COMMAND ----------

expected_facts = df_silver.count()
actual_facts = df_fact_race_results.count()

assert actual_facts == expected_facts, (
    "Fact table record count mismatch"
)

duplicate_facts = (
    df_fact_race_results
    .groupBy(*FACT_KEY)
    .count()
    .filter(F.col("count") > 1)
    .count()
)

assert duplicate_facts == 0, (
    "Duplicate fact business keys"
)

null_keys = (
    df_fact_race_results
    .filter(
        F.col("race_id").isNull()
        | F.col("driver_id").isNull()
    )
    .count()
)

assert null_keys == 0, "Missing fact keys"

print(f"Expected fact records: {expected_facts}")
print(f"Actual fact records: {actual_facts}")
print(f"Duplicate fact keys: {duplicate_facts}")
print(f"NULL fact keys: {null_keys}")
print("Fact table validation: PASSED")

# COMMAND ----------

silver_points = (
    df_silver
    .agg(F.sum("points"))
    .first()[0]
)

gold_points = (
    df_fact_race_results
    .agg(F.sum("points"))
    .first()[0]
)

assert silver_points == gold_points, (
    "Championship points mismatch"
)

print(f"Silver total points: {silver_points}")
print(f"Gold total points: {gold_points}")
print("Points reconciliation: PASSED")

# COMMAND ----------

# MAGIC
# MAGIC %md
# MAGIC
# MAGIC ## 10. Referential Integrity Validation
# MAGIC
# MAGIC Validate all foreign key relationships between
# MAGIC the fact table and dimension tables.
# MAGIC
# MAGIC Use left anti joins to identify orphan records.
# MAGIC
# MAGIC Every foreign key in the fact table must have
# MAGIC a corresponding primary key in its dimension.
# MAGIC
# MAGIC Validation failures prevent invalid data from
# MAGIC being written to the Gold layer.

# COMMAND ----------

def validate_foreign_key(fact_df, dimension_df, key_column):

    orphan_records = (
        fact_df
        .join(
            dimension_df.select(key_column),
            on=key_column,
            how="left_anti"
        )
    )

    orphan_count = orphan_records.count()

    assert orphan_count == 0, (
        f"{key_column}: "
        f"{orphan_count} orphan records detected"
    )

    print(f"Foreign key: {key_column}")
    print(f"Orphan records: {orphan_count}")
    print("Referential integrity: PASSED")

# COMMAND ----------

validate_foreign_key(
    df_fact_race_results,
    df_dim_drivers,
    "driver_id"
)

validate_foreign_key(
    df_fact_race_results,
    df_dim_constructors,
    "constructor_id"
)

validate_foreign_key(
    df_fact_race_results,
    df_dim_circuits,
    "circuit_id"
)

validate_foreign_key(
    df_fact_race_results,
    df_dim_races,
    "race_id"
)

# COMMAND ----------

# MAGIC
# MAGIC %md
# MAGIC
# MAGIC ## 11. Star Schema Integration Validation
# MAGIC
# MAGIC Join the fact table with all dimension tables.
# MAGIC
# MAGIC Validate that the dimensional model preserves
# MAGIC the original record count and championship points.
# MAGIC
# MAGIC Ensure that joins do not introduce duplicate
# MAGIC records or data loss.

# COMMAND ----------

df_star = (
    df_fact_race_results

    .join(
        df_dim_drivers.select(
            "driver_id",
            "full_name"
        ),
        on="driver_id",
        how="inner"
    )

    .join(
        df_dim_constructors.select(
            "constructor_id",
            "constructor_name"
        ),
        on="constructor_id",
        how="inner"
    )

    .join(
        df_dim_circuits.select(
            "circuit_id",
            "circuit_name",
            "country"
        ),
        on="circuit_id",
        how="inner"
    )

    .join(
        df_dim_races.select(
            "race_id",
            "season",
            "round",
            "race_name",
            "race_date"
        ),
        on="race_id",
        how="inner"
    )
)

display(df_star)

# COMMAND ----------

star_count = df_star.count()

star_points = (
    df_star
    .agg(F.sum("points"))
    .first()[0]
)

star_duplicates = (
    df_star
    .groupBy(*FACT_KEY)
    .count()
    .filter(F.col("count") > 1)
    .count()
)

assert star_count == expected_facts, (
    "Star schema record count mismatch"
)

assert star_points == silver_points, (
    "Star schema points mismatch"
)

assert star_duplicates == 0, (
    "Star schema duplicate keys detected"
)

print(f"Star schema records: {star_count}")
print(f"Star schema total points: {star_points}")
print(f"Duplicate business keys: {star_duplicates}")
print("Star schema integration validation: PASSED")

# COMMAND ----------

# MAGIC
# MAGIC %md
# MAGIC
# MAGIC ## 12. Analytical Smoke Test
# MAGIC
# MAGIC Execute a sample analytical aggregation to
# MAGIC verify that the dimensional model supports
# MAGIC business reporting.
# MAGIC
# MAGIC Calculate total race points, wins and podiums
# MAGIC per driver across the available seasons.

# COMMAND ----------

display(
    df_star
    .groupBy("driver_id", "full_name")
    .agg(
        F.count("*").alias("race_entries"),

        F.sum("points").alias("total_points"),

        F.sum(
            F.col("is_win").cast("int")
        ).alias("wins"),

        F.sum(
            F.col("is_podium").cast("int")
        ).alias("podiums")
    )
    .orderBy(
        F.desc("total_points"),
        F.asc("driver_id")
    )
)

# COMMAND ----------

# MAGIC
# MAGIC %md
# MAGIC
# MAGIC ## 13. Gold Table Configuration
# MAGIC
# MAGIC Define all dimension and fact tables together
# MAGIC with their corresponding DataFrames.
# MAGIC
# MAGIC Each table is stored in a separate Delta Lake
# MAGIC directory within the Gold storage container.
# MAGIC
# MAGIC Load strategy: Full Refresh.

# COMMAND ----------

GOLD_TABLES = {
    "dim_drivers": df_dim_drivers,
    "dim_constructors": df_dim_constructors,
    "dim_circuits": df_dim_circuits,
    "dim_races": df_dim_races,
    "fact_race_results": df_fact_race_results
}

for table_name, dataframe in GOLD_TABLES.items():
    table_path = f"{GOLD_PATH}{table_name}"

    print(f"Table: {GOLD_SCHEMA}.{table_name}")
    print(f"Path: {table_path}")
    print(f"Records: {dataframe.count()}")
    print("-" * 50)

# COMMAND ----------

# MAGIC
# MAGIC %md
# MAGIC
# MAGIC ## 14. Write Gold Delta Tables
# MAGIC
# MAGIC Persist all validated dimension and fact tables
# MAGIC as Delta Lake datasets in Azure Data Lake Storage.
# MAGIC
# MAGIC Use overwrite mode to support repeatable
# MAGIC full-refresh processing without accumulating
# MAGIC duplicate records.

# COMMAND ----------

def write_gold_table(dataframe, table_name):

    table_path = f"{GOLD_PATH}{table_name}"

    (
        dataframe.write
        .format("delta")
        .mode("overwrite")
        .save(table_path)
    )

    print(f"{table_name}: WRITE COMPLETED")

# COMMAND ----------

for table_name, dataframe in GOLD_TABLES.items():

    write_gold_table(
        dataframe,
        table_name
    )

print("Gold Delta tables write: COMPLETED")

# COMMAND ----------

# MAGIC
# MAGIC %md
# MAGIC
# MAGIC ## 15. Gold Delta Read-Back Validation
# MAGIC
# MAGIC Read each persisted Delta table directly
# MAGIC from its storage location.
# MAGIC
# MAGIC Validate record counts, column names,
# MAGIC data types and data content against the
# MAGIC original transformed DataFrames.

# COMMAND ----------

def validate_delta_table(dataframe, table_name):

    table_path = f"{GOLD_PATH}{table_name}"

    df_restored = (
        spark.read
        .format("delta")
        .load(table_path)
    )

    expected_count = dataframe.count()
    actual_count = df_restored.count()

    assert actual_count == expected_count, (
        f"{table_name}: record count mismatch"
    )

    assert df_restored.dtypes == dataframe.dtypes, (
        f"{table_name}: schema mismatch"
    )

    assert df_restored.exceptAll(dataframe).count() == 0, (
        f"{table_name}: unexpected records"
    )

    assert dataframe.exceptAll(df_restored).count() == 0, (
        f"{table_name}: missing records"
    )

    print(f"{table_name}: {actual_count} records")
    print("Read-back validation: PASSED")

# COMMAND ----------

for table_name, dataframe in GOLD_TABLES.items():

    validate_delta_table(
        dataframe,
        table_name
    )

print("All Gold Delta validations: PASSED")

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## 16. Unity Catalog Registration
# MAGIC
# MAGIC Register all Gold Delta datasets as external
# MAGIC tables in Unity Catalog.
# MAGIC
# MAGIC Enable SQL-based access to the dimensional
# MAGIC model while preserving data storage in ADLS Gen2.
# MAGIC

# COMMAND ----------

def register_gold_table(table_name):

    full_table_name = f"{GOLD_SCHEMA}.{table_name}"
    table_path = f"{GOLD_PATH}{table_name}"

    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {full_table_name}
        USING DELTA
        LOCATION '{table_path}'
    """)

    print(f"{full_table_name}: REGISTERED")

# COMMAND ----------

for table_name in GOLD_TABLES:

    register_gold_table(table_name)

print("Gold Unity Catalog registration: COMPLETED")

# COMMAND ----------

display(
    spark.sql(f"SHOW TABLES IN {GOLD_SCHEMA}")
)

# COMMAND ----------

for table_name, dataframe in GOLD_TABLES.items():

    full_table_name = f"{GOLD_SCHEMA}.{table_name}"
    expected_path = f"{GOLD_PATH}{table_name}"

    df_registered = spark.table(full_table_name)

    details = (
        spark.sql(f"DESCRIBE DETAIL {full_table_name}")
        .first()
    )

    assert details["format"] == "delta"

    assert (
        details["location"].rstrip("/")
        == expected_path.rstrip("/")
    ), f"{table_name}: incorrect storage location"

    assert df_registered.count() == dataframe.count()

    assert df_registered.dtypes == dataframe.dtypes

    assert df_registered.exceptAll(dataframe).count() == 0

    assert dataframe.exceptAll(df_registered).count() == 0

    print(f"{full_table_name}: PASSED")

print("Unity Catalog validation: PASSED")

# COMMAND ----------

# MAGIC
# MAGIC %md
# MAGIC
# MAGIC ## 17. Gold Table Version History
# MAGIC
# MAGIC Inspect Delta Lake transaction history to
# MAGIC support repeatability and idempotency testing.
# MAGIC
# MAGIC Compare table versions before and after
# MAGIC a repeated full-refresh execution.

# COMMAND ----------

for table_name in GOLD_TABLES:

    full_table_name = f"{GOLD_SCHEMA}.{table_name}"

    print(f"Table: {full_table_name}")

    display(
        spark.sql(
            f"DESCRIBE HISTORY {full_table_name}"
        )
        .select(
            "version",
            "timestamp",
            "operation",
            "operationParameters"
        )
        .orderBy(F.desc("version"))
        .limit(5)
    )

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## 18. Full Refresh Idempotency Validation
# MAGIC
# MAGIC Compare the two latest Delta table versions
# MAGIC using Delta Lake Time Travel.
# MAGIC
# MAGIC Verify that repeated processing of unchanged
# MAGIC Silver data produces identical Gold records,
# MAGIC column names and data types.
# MAGIC
# MAGIC This validation requires at least two
# MAGIC successful Gold table writes.

# COMMAND ----------

def validate_idempotency(table_name):

    full_table_name = f"{GOLD_SCHEMA}.{table_name}"
    table_path = f"{GOLD_PATH}{table_name}"

    history = (
        spark.sql(f"DESCRIBE HISTORY {full_table_name}")
        .filter(F.col("operation") == "WRITE")
        .select("version")
        .orderBy(F.desc("version"))
        .limit(2)
        .collect()
    )

    assert len(history) == 2, (
        f"{table_name}: insufficient write history"
    )

    current_version = history[0]["version"]
    previous_version = history[1]["version"]

    df_current = (
        spark.read
        .format("delta")
        .option("versionAsOf", current_version)
        .load(table_path)
    )

    df_previous = (
        spark.read
        .format("delta")
        .option("versionAsOf", previous_version)
        .load(table_path)
    )

    assert df_current.count() == df_previous.count(), (
        f"{table_name}: record count changed"
    )

    assert df_current.dtypes == df_previous.dtypes, (
        f"{table_name}: schema changed"
    )

    assert df_current.exceptAll(df_previous).count() == 0, (
        f"{table_name}: new or changed records detected"
    )

    assert df_previous.exceptAll(df_current).count() == 0, (
        f"{table_name}: missing or changed records detected"
    )

    print(f"Table: {table_name}")
    print(f"Previous version: {previous_version}")
    print(f"Current version: {current_version}")
    print(f"Records: {df_current.count()}")
    print("Idempotency validation: PASSED")
    print("-" * 50)

# COMMAND ----------

for table_name in GOLD_TABLES:

    validate_idempotency(table_name)

print("Gold full refresh idempotency: PASSED")

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## 18. Optional Full Refresh Idempotency Test
# MAGIC
# MAGIC Development-only validation using Delta Lake
# MAGIC Time Travel.
# MAGIC
# MAGIC Run this test only when Silver input data
# MAGIC remains unchanged between two successful
# MAGIC Gold full-refresh executions.
# MAGIC
# MAGIC Disabled by default for scheduled pipeline runs.

# COMMAND ----------

RUN_IDEMPOTENCY_TEST = False

if RUN_IDEMPOTENCY_TEST:

    for table_name in GOLD_TABLES:
        validate_idempotency(table_name)

    print("Gold full refresh idempotency: PASSED")

else:
    print("Optional idempotency test: SKIPPED")