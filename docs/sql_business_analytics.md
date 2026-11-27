# SQL Business Analytics

## 1. Overview

The analytics layer provides reusable SQL views for Formula 1 performance analysis based on the Gold dimensional model.

It separates business logic from data transformation processes and provides a consistent data source for the future Streamlit dashboard.

### Objectives

- Answer five business questions using SQL.
- Provide reusable analytical views.
- Ensure consistent business metric definitions.
- Validate analytical results against the Gold layer.
- Support dashboard development.

## 2. Technology Stack

| Technology | Purpose |
|---|---|
| Azure Databricks | SQL execution environment |
| Spark SQL | Business analytics |
| Delta Lake | Underlying Gold data storage |
| Unity Catalog | Schema and view management |
| GitHub | Source code version control |
| Streamlit | Future dashboard integration |

## 3. Data Scope

The analytics layer covers Formula 1 race results from the 2021–2025 seasons.

The underlying Gold dataset contains:

| Metric | Value |
|---|---:|
| Seasons | 5 |
| Races | 114 |
| Drivers | 35 |
| Constructors | 12 |
| Circuits | 28 |
| Race result records | 2,278 |
| Total race points | 11,540.50 |

Sprint race results are excluded. Therefore, aggregated points should not be interpreted as official championship standings.

## 4. Analytics Architecture

The analytics layer is implemented as a dedicated Unity Catalog schema:

`f1_lakehouse.analytics`

It consumes the existing Gold dimensional model:

- `f1_lakehouse.gold.fact_race_results`
- `f1_lakehouse.gold.dim_drivers`
- `f1_lakehouse.gold.dim_constructors`
- `f1_lakehouse.gold.dim_circuits`
- `f1_lakehouse.gold.dim_races`

The analytical views do not create additional physical copies of the underlying data.

## 5. Analytical Views

| View | Grain | Purpose |
|---|---|---|
| `vw_race_results` | Driver per race | Base analytical dataset |
| `vw_driver_circuit_history` | Driver per race | Recent circuit performance |
| `vw_driver_circuit_performance` | Driver per circuit | Circuit performance comparison |
| `vw_driver_positions_gained` | Driver | Grid position improvement |
| `vw_driver_season_performance` | Driver per season | Historical performance trends |
| `vw_constructor_circuit_performance` | Constructor per circuit | Constructor performance comparison |

All business-specific views depend on the base analytical view.

## 6. Base Analytical View

The `vw_race_results` view combines the Gold fact table with all four dimension tables using INNER JOIN operations.

It provides a unified analytical dataset containing:

- Race and season information.
- Driver information.
- Constructor information.
- Circuit information.
- Race performance metrics.
- Classification and race status indicators.

The business key is the combination of `race_id` and `driver_id`.

## 7. Business Questions

### 7.1. Recent Driver Circuit Performance

**Question:** How has a driver performed in their last N race appearances at a selected circuit?

**View:** `vw_driver_circuit_history`

The view uses the ROW_NUMBER window function to rank race appearances by date within each driver and circuit combination.

Key metrics:

- Grid position.
- Finish position.
- Positions gained.
- Race points.
- Wins and podiums.
- Race status.

The number of recent appearances can be controlled through the `recency_rank` filter.

All recorded race entries are retained, including DNF, DNS and DSQ results.

### 7.2. Strongest Driver Circuits

**Question:** Which circuits are a driver's strongest?

**View:** `vw_driver_circuit_performance`

Driver performance is aggregated across circuits.

Key metrics:

- Race entries and starts.
- Total points.
- Average points per start.
- Average finishing position.
- Best finishing position.
- Wins and podiums.
- Win and podium rates.

Average points per start is the primary ranking metric.

Example ranking queries require at least three race starts to reduce the influence of small sample sizes.

### 7.3. Average Positions Gained

**Question:** How many grid positions does a driver gain or lose on average?

**View:** `vw_driver_positions_gained`

Positions gained are calculated in the Silver layer using:

`positions_gained = grid_position - finish_position`

Only classified results with valid starting positions are included.

Key metrics:

- Average starting position.
- Average finishing position.
- Average positions gained.
- Total positions gained.
- Best and worst position changes.
- Valid and excluded result counts.
- Percentage of races with positions gained.

Example ranking queries require at least ten valid results.

Positions gained should not be interpreted as the number of on-track overtakes.

### 7.4. Driver Season Performance

**Question:** How does driver performance change across seasons?

**View:** `vw_driver_season_performance`

Race results are aggregated by driver and season.

Key metrics:

- Race starts.
- Total race points.
- Average points per start.
- Average finishing position.
- Average positions gained.
- Wins and podiums.
- Year-over-year performance changes.

The LAG window function retrieves previous-season metrics.

Year-over-year changes are calculated only for consecutive seasons. Missing previous seasons and undefined percentage changes are represented by NULL values.

### 7.5. Constructor Circuit Performance

**Question:** Which constructors perform best at a selected circuit?

**View:** `vw_constructor_circuit_performance`

Driver-level results are aggregated by constructor and circuit.

Key metrics:

- Distinct race appearances.
- Distinct races with at least one driver starting.
- Individual driver entries and starts.
- Total race points.
- Average points per race appearance.
- Wins and individual podiums.
- Races with at least one podium.
- Win and podium race rates.

Distinct race identifiers prevent individual driver results from being incorrectly counted as separate constructor race appearances.

Example ranking queries require at least three races with a constructor start.

## 8. Business Metric Definitions

| Metric | Definition |
|---|---|
| Race entry | A recorded driver race result |
| Driver race start | A race entry not marked as DNS |
| Constructor race appearance | A distinct race with a recorded constructor result |
| Constructor race start | A distinct race with at least one driver not marked as DNS |
| Average points per start | Average race points across driver starts |
| Average constructor points per race | Total constructor points divided by distinct race appearances |
| Average finishing position | Average classified finishing position |
| Positions gained | Valid starting position minus classified finishing position |
| Win rate | Wins divided by race starts |
| Driver podium rate | Individual podiums divided by driver starts |
| Constructor podium race rate | Races with at least one podium divided by constructor race starts |
| YoY change | Difference between consecutive season metrics |

Undefined averages and ratios are represented by NULL values rather than artificial zero values.

## 9. SQL Techniques

The analytics implementation demonstrates the following SQL techniques:

| Technique | Application |
|---|---|
| INNER JOIN | Combining fact and dimension tables |
| GROUP BY | Business metric aggregation |
| Common Table Expressions | Structuring analytical queries |
| ROW_NUMBER | Ranking and recent race selection |
| LAG | Previous-season comparisons |
| COUNT DISTINCT | Counting unique races and drivers |
| COUNT_IF | Conditional metric aggregation |
| CASE WHEN | Business rules and conditional calculations |
| TRY_DIVIDE | Safe division |
| UNION ALL | Consolidated view validation |
| Null-safe equality | Validation involving nullable values |
| CREATE OR REPLACE VIEW | Repeatable analytical view deployment |

## 10. Data Quality and Validation

The SQL notebook includes validation queries covering:

- Analytical view availability.
- Record count and race point reconciliation.
- Business key uniqueness.
- Ranking sequence consistency.
- Business metric ranges.
- Race entry and start consistency.
- Win and podium consistency.
- Positions gained reconciliation.
- Year-over-year calculation rules.

Validation queries return PASSED or FAILED statuses for manual inspection.

Automated data quality testing will be implemented in F09.

## 11. Manual Business Validation

A manual reconciliation example compares Max Verstappen's Silverstone race results directly from the Gold tables with the aggregated driver circuit performance view.

The comparison covers race starts, total points, average points per start, average finishing position, wins and podiums.

## 12. Execution Instructions

Source file: `sql/04_sql_business_analytics.sql`

1. Ensure that the Gold dimensional model exists.
2. Import the SQL source into Azure Databricks.
3. Select a compatible compute environment.
4. Execute the notebook cells in order.
5. Verify all six analytical views.
6. Review validation query results.

CREATE OR REPLACE VIEW statements support repeatable deployment.

## 13. Design Decisions and Limitations

- Standard SQL views are used instead of materialized views.
- Business logic is centralized in reusable analytical views.
- Rankings include sample-size thresholds.
- Ranking metrics are rounded to two decimal places.
- Race status definitions are inherited from Silver.
- Constructor identities follow source system identifiers.
- Sprint results and qualifying data are excluded.
- Historical results do not isolate driver ability from car performance.
- Validation queries currently require manual inspection.
- Dynamic dashboard filtering will be implemented in F10.

## 14. Next Steps

- F08: End-to-end pipeline orchestration.
- F09: Automated data quality tests and basic CI.
- F10: Streamlit dashboard.
- F11: Portfolio documentation.