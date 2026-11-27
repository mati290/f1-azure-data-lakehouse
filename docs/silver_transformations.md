# Silver Layer – Data Transformations

## 1. Overview

The Silver layer transforms raw Formula 1 race results
from the Bronze layer into a structured, validated
and analytics-ready Delta table.

The transformations are implemented using PySpark
in Azure Databricks.

## 2. Technical Configuration

| Component | Configuration |
|---|---|
| Processing engine | Azure Databricks / PySpark |
| Source format | JSON |
| Target format | Delta Lake |
| Storage | Azure Data Lake Storage Gen2 |
| Catalog | f1_lakehouse |
| Schema | silver |
| Table | race_results |
| Table type | External |
| Load strategy | Full Refresh |
| Data scope | 2021–2025 |

## 3. Data Flow

Bronze JSON
→ Schema Enforcement
→ Data Flattening
→ Type Casting
→ Data Cleaning
→ Deduplication
→ Business Logic
→ Data Quality Validation
→ Silver Delta Table

## 4. Storage Locations

### Source

`abfss://bronze@stf1lakehouse290.dfs.core.windows.net/jolpica/race_results`

### Target

`abfss://silver@stf1lakehouse290.dfs.core.windows.net/race_results`

### Unity Catalog Table

`f1_lakehouse.silver.race_results`

## 5. Transformation Logic

- Apply an explicit schema to raw JSON files.
- Flatten nested race and driver result structures.
- Extract relevant race, circuit, driver and
  constructor attributes.
- Convert source strings into appropriate data types.
- Preserve fractional championship points.
- Normalize empty strings to NULL.
- Remove exact duplicate records.
- Reject conflicting records sharing the same
  business key.
- Preserve optional missing values.
- Derive analytical columns.

## 6. Data Grain and Business Key

Each record represents one driver result
in one Formula 1 race.

The composite business key consists of:

- season
- round
- driver_id

## 7. Derived Columns

| Column | Description |
|---|---|
| is_classified | Valid numeric classification, excluding DNS and DSQ |
| finish_position | Classified finishing position |
| positions_gained | Grid position minus classified finishing position |
| is_win | Indicates first place |
| is_podium | Indicates a top-three finish |
| is_dnf | Non-finishing status, excluding DNS and DSQ |
| is_dns | Did-not-start result according to project rules |
| is_dsq | Indicates disqualification |

Positions gained are calculated only for classified
results with a positive grid position.

Unclassified results retain a NULL finish position
instead of an artificial numeric value.

DNF and classification are not mutually exclusive.

Race status flags are derived using project-specific
rules based on the available source data.

## 8. Data Quality Validation

The notebook implements the following checks:

- Required column completeness.
- Composite business key uniqueness.
- Numeric value range validation.
- Business logic consistency.
- Record count reconciliation against Bronze
  API metadata.
- Delta table read-back validation.
- Registered table schema validation.
- Silver table content consistency validation.

Validation failures stop notebook execution.

Pre-write validation checks prevent invalid data
from being written to the Silver layer.

## 9. Load Strategy and Idempotency

The Silver layer uses a Full Refresh strategy
with Delta overwrite mode.

This approach is appropriate for the current
historical dataset size and MVP scope.

Repeated execution with unchanged Bronze input
is expected to produce equivalent Silver data
without accumulating duplicate records.

A manual repeat-run test was performed using
unchanged Bronze input.

Record counts and business key uniqueness
were validated after repeated execution.

The notebook also compares the persisted Silver
table with the transformed DataFrame to verify
content consistency within the current execution.

Delta Lake transaction history provides visibility
into successive write operations.

## 10. Validation Results

| Metric | Value |
|---|---:|
| Total race results | 2278 |
| Classified results | 2007 |
| DNF | 288 |
| DNS | 14 |
| DSQ | 11 |
| Wins | 114 |
| Podiums | 342 |
| Duplicate business keys | 0 |

## 11. Security

Storage access is managed through Azure managed
identities and Unity Catalog external locations.

No storage account keys or access tokens are
embedded in the transformation notebook.

## 12. Known Limitations

- Processing is limited to seasons 2021–2025.
- Full Refresh is used instead of incremental
  processing.
- Race status interpretation depends on source
  data quality.
- Source status mappings may require updates
  when new values appear.
- Positions gained are not calculated for
  grid position zero.
- Automated cross-run data comparison is not
  implemented in the current MVP.

## 13. Implementation

The transformation notebook is available at:

[02_bronze_to_silver.py](../notebooks/02_bronze_to_silver.py)

## 14. Next Steps

The Silver table will serve as the source
for the Gold dimensional model:

- dim_drivers
- dim_constructors
- dim_circuits
- dim_races
- fact_race_results

The Gold layer will support SQL business analytics
and the Streamlit dashboard.