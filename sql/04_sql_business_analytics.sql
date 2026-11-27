-- Databricks notebook source
-- MAGIC %md
-- MAGIC
-- MAGIC # SQL Business Analytics
-- MAGIC
-- MAGIC ## Objective
-- MAGIC
-- MAGIC Transform the Gold dimensional model into
-- MAGIC reusable SQL analytics for Formula 1
-- MAGIC performance reporting.
-- MAGIC
-- MAGIC - Source: f1_lakehouse.gold
-- MAGIC - Target: f1_lakehouse.analytics
-- MAGIC - Data scope: 2021–2025
-- MAGIC - Data model: Star Schema
-- MAGIC - Processing language: SQL
-- MAGIC - Business questions: 5
-- MAGIC - Consumer: Streamlit dashboard

-- COMMAND ----------

SHOW TABLES IN f1_lakehouse.gold;

-- COMMAND ----------

SELECT
    COUNT(*) AS total_records,
    COUNT(DISTINCT driver_id) AS total_drivers,
    COUNT(DISTINCT constructor_id) AS total_constructors,
    COUNT(DISTINCT circuit_id) AS total_circuits,
    COUNT(DISTINCT race_id) AS total_races,
    SUM(points) AS total_points
FROM f1_lakehouse.gold.fact_race_results;

-- COMMAND ----------

CREATE SCHEMA IF NOT EXISTS f1_lakehouse.analytics
COMMENT 'Reusable SQL views for Formula 1 performance analytics';

-- COMMAND ----------

-- MAGIC %md
-- MAGIC
-- MAGIC ## 01. Base Analytical View
-- MAGIC
-- MAGIC Create a reusable SQL view by joining the
-- MAGIC Gold fact table with all four dimensions.
-- MAGIC
-- MAGIC The view provides business-friendly attributes
-- MAGIC and performance measures for analytical queries
-- MAGIC without duplicating physical data.
-- MAGIC
-- MAGIC Grain: One driver result per race.

-- COMMAND ----------

CREATE OR REPLACE VIEW
    f1_lakehouse.analytics.vw_race_results
AS

SELECT
    -- Race attributes
    f.race_id,
    r.season,
    r.round,
    r.race_name,
    r.race_date,
    r.race_time,

    -- Driver attributes
    f.driver_id,
    d.driver_code,
    d.full_name AS driver_name,
    d.nationality AS driver_nationality,
    f.driver_number,

    -- Constructor attributes
    f.constructor_id,
    c.constructor_name,
    c.nationality AS constructor_nationality,

    -- Circuit attributes
    f.circuit_id,
    ci.circuit_name,
    ci.city,
    ci.country,
    ci.latitude,
    ci.longitude,

    -- Race performance
    f.grid_position,
    f.position,
    f.position_text,
    f.finish_position,
    f.positions_gained,
    f.points,
    f.laps_completed,
    f.status,

    -- Timing attributes
    f.race_time_ms,
    f.fastest_lap_rank,
    f.fastest_lap_number,
    f.fastest_lap_time,

    -- Analytical flags
    f.is_classified,
    f.is_win,
    f.is_podium,
    f.is_dnf,
    f.is_dns,
    f.is_dsq

FROM f1_lakehouse.gold.fact_race_results AS f

INNER JOIN f1_lakehouse.gold.dim_drivers AS d
    ON f.driver_id = d.driver_id

INNER JOIN f1_lakehouse.gold.dim_constructors AS c
    ON f.constructor_id = c.constructor_id

INNER JOIN f1_lakehouse.gold.dim_circuits AS ci
    ON f.circuit_id = ci.circuit_id

INNER JOIN f1_lakehouse.gold.dim_races AS r
    ON f.race_id = r.race_id;

-- COMMAND ----------

USE CATALOG f1_lakehouse; SHOW VIEWS IN analytics;

-- COMMAND ----------

DESCRIBE f1_lakehouse.analytics.vw_race_results;

-- COMMAND ----------

SELECT *
FROM f1_lakehouse.analytics.vw_race_results
ORDER BY
    race_date DESC,
    position ASC
LIMIT 20;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC
-- MAGIC ## 02. Analytical View Validation
-- MAGIC
-- MAGIC Validate the analytical view against the
-- MAGIC Gold fact table.
-- MAGIC
-- MAGIC Ensure that joins preserve record counts,
-- MAGIC business key uniqueness and total race points.

-- COMMAND ----------

WITH gold_summary AS (

    SELECT
        COUNT(*) AS total_records,
        SUM(points) AS total_points
    FROM f1_lakehouse.gold.fact_race_results

),

view_summary AS (

    SELECT
        COUNT(*) AS total_records,
        SUM(points) AS total_points
    FROM f1_lakehouse.analytics.vw_race_results

)

SELECT
    g.total_records AS gold_records,
    v.total_records AS view_records,
    g.total_points AS gold_points,
    v.total_points AS view_points,

    CASE
        WHEN g.total_records = v.total_records
         AND g.total_points = v.total_points
        THEN 'PASSED'
        ELSE 'FAILED'
    END AS validation_status

FROM gold_summary AS g
CROSS JOIN view_summary AS v;

-- COMMAND ----------

WITH duplicate_keys AS (

    SELECT
        race_id,
        driver_id,
        COUNT(*) AS record_count

    FROM f1_lakehouse.analytics.vw_race_results

    GROUP BY
        race_id,
        driver_id

    HAVING COUNT(*) > 1

)

SELECT
    COUNT(*) AS duplicate_business_keys,

    CASE
        WHEN COUNT(*) = 0 THEN 'PASSED'
        ELSE 'FAILED'
    END AS validation_status

FROM duplicate_keys;

-- COMMAND ----------

SELECT
    COUNT(*) AS total_records,

    COUNT_IF(is_classified) AS classified_results,
    COUNT_IF(is_win) AS wins,
    COUNT_IF(is_podium) AS podiums,
    COUNT_IF(is_dnf) AS dnf_results,
    COUNT_IF(is_dns) AS dns_results,
    COUNT_IF(is_dsq) AS dsq_results

FROM f1_lakehouse.analytics.vw_race_results;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC
-- MAGIC ## 03. Business Question 1 - Recent Circuit Performance
-- MAGIC
-- MAGIC Analyze the most recent N race results for
-- MAGIC a selected driver and circuit.
-- MAGIC
-- MAGIC Use a window function to rank race results
-- MAGIC chronologically across multiple seasons.
-- MAGIC
-- MAGIC Preserve classified and non-classified results,
-- MAGIC including DNF, DNS and DSQ.

-- COMMAND ----------

CREATE OR REPLACE VIEW
    f1_lakehouse.analytics.vw_driver_circuit_history
AS

SELECT
    race_id,
    season,
    round,
    race_date,
    race_name,

    driver_id,
    driver_name,

    constructor_id,
    constructor_name,

    circuit_id,
    circuit_name,

    grid_position,
    finish_position,
    positions_gained,
    points,
    status,

    is_classified,
    is_win,
    is_podium,
    is_dnf,
    is_dns,
    is_dsq,

    ROW_NUMBER() OVER (
        PARTITION BY driver_id, circuit_id
        ORDER BY
            race_date DESC,
            season DESC,
            round DESC
    ) AS recency_rank

FROM f1_lakehouse.analytics.vw_race_results;

-- COMMAND ----------

SELECT
    recency_rank,
    season,
    race_date,
    race_name,
    driver_name,
    constructor_name,
    circuit_name,
    grid_position,
    finish_position,
    positions_gained,
    points,
    status

FROM f1_lakehouse.analytics.vw_driver_circuit_history

WHERE driver_id = 'max_verstappen'
    AND circuit_id = 'silverstone'
    AND recency_rank <= 3

ORDER BY recency_rank;

-- COMMAND ----------

WITH recent_races AS (

    SELECT *
    FROM f1_lakehouse.analytics.vw_driver_circuit_history

    WHERE driver_id = 'max_verstappen'
        AND circuit_id = 'silverstone'
        AND recency_rank <= 3

)

SELECT
    COUNT(*) AS race_entries,

    COUNT_IF(is_classified) AS classified_results,

    SUM(points) AS total_points,

    ROUND(AVG(points), 2) AS avg_points,

    ROUND(AVG(finish_position), 2)
        AS avg_finish_position,

    ROUND(AVG(positions_gained), 2)
        AS avg_positions_gained,

    COUNT(positions_gained)
        AS valid_positions_gained_results,

    COUNT_IF(is_win) AS wins,

    COUNT_IF(is_podium) AS podiums,

    COUNT_IF(is_dnf) AS dnf_results,

    COUNT_IF(is_dns) AS dns_results,

    COUNT_IF(is_dsq) AS dsq_results

FROM recent_races;

-- COMMAND ----------

WITH base_summary AS (

    SELECT COUNT(*) AS total_records
    FROM f1_lakehouse.analytics.vw_race_results

),

history_summary AS (

    SELECT COUNT(*) AS total_records
    FROM f1_lakehouse.analytics.vw_driver_circuit_history

)

SELECT
    b.total_records AS base_records,
    h.total_records AS history_records,

    CASE
        WHEN b.total_records = h.total_records
        THEN 'PASSED'
        ELSE 'FAILED'
    END AS validation_status

FROM base_summary AS b
CROSS JOIN history_summary AS h;

-- COMMAND ----------

WITH ranking_validation AS (

    SELECT
        driver_id,
        circuit_id,
        COUNT(*) AS total_records,
        COUNT(DISTINCT recency_rank) AS unique_ranks,
        MIN(recency_rank) AS min_rank,
        MAX(recency_rank) AS max_rank

    FROM f1_lakehouse.analytics.vw_driver_circuit_history

    GROUP BY
        driver_id,
        circuit_id

)

SELECT
    COUNT(*) AS invalid_groups,

    CASE
        WHEN COUNT(*) = 0 THEN 'PASSED'
        ELSE 'FAILED'
    END AS validation_status

FROM ranking_validation

WHERE min_rank <> 1
    OR max_rank <> total_records
    OR unique_ranks <> total_records;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC
-- MAGIC ## 04. Business Question 2 - Driver Circuit Performance
-- MAGIC
-- MAGIC Compare driver performance across different
-- MAGIC circuits using aggregated race statistics.
-- MAGIC
-- MAGIC Use average points per start as the primary
-- MAGIC ranking metric to account for different
-- MAGIC numbers of race starts.
-- MAGIC
-- MAGIC Include sample size, wins, podiums,
-- MAGIC classification and retirement statistics.

-- COMMAND ----------

CREATE OR REPLACE VIEW
    f1_lakehouse.analytics.vw_driver_circuit_performance
AS

SELECT
    driver_id,
    driver_name,
    circuit_id,
    circuit_name,
    country,

    COUNT(*) AS race_entries,

    COUNT_IF(NOT is_dns) AS race_starts,

    COUNT_IF(is_classified) AS classified_results,

    COUNT(finish_position) AS valid_finish_results,

    SUM(points) AS total_points,

    ROUND(
        AVG(
            CASE
                WHEN NOT is_dns THEN points
            END
        ), 2
    ) AS avg_points_per_start,

    ROUND(AVG(finish_position), 2)
        AS avg_finish_position,

    MIN(finish_position) AS best_finish_position,

    COUNT_IF(is_win) AS wins,

    COUNT_IF(is_podium) AS podiums,

    COUNT_IF(is_dnf) AS dnf_results,

    COUNT_IF(is_dns) AS dns_results,

    COUNT_IF(is_dsq) AS dsq_results,

    ROUND(
        100.0 * TRY_DIVIDE(
            COUNT_IF(is_win),
            COUNT_IF(NOT is_dns)
        ), 2
    ) AS win_rate_pct,

    ROUND(
        100.0 * TRY_DIVIDE(
            COUNT_IF(is_podium),
            COUNT_IF(NOT is_dns)
        ), 2
    ) AS podium_rate_pct

FROM f1_lakehouse.analytics.vw_race_results

GROUP BY
    driver_id,
    driver_name,
    circuit_id,
    circuit_name,
    country;

-- COMMAND ----------

WITH eligible_circuits AS (

    SELECT *
    FROM f1_lakehouse.analytics.vw_driver_circuit_performance

    WHERE driver_id = 'max_verstappen'
        AND race_starts >= 3

)

SELECT
    ROW_NUMBER() OVER (
        ORDER BY
            avg_points_per_start DESC,
            race_starts DESC,
            circuit_id ASC
    ) AS circuit_rank,

    driver_name,
    circuit_name,
    country,
    race_starts,
    total_points,
    avg_points_per_start,
    avg_finish_position,
    best_finish_position,
    wins,
    podiums,
    win_rate_pct,
    podium_rate_pct

FROM eligible_circuits

ORDER BY circuit_rank

LIMIT 10;

-- COMMAND ----------

SELECT
    driver_name,
    circuit_name,
    race_starts,
    total_points,
    avg_points_per_start,
    avg_finish_position,
    wins,
    podiums,
    dnf_results

FROM f1_lakehouse.analytics.vw_driver_circuit_performance

WHERE driver_id = 'hamilton'
    AND race_starts >= 3

ORDER BY
    avg_points_per_start DESC,
    race_starts DESC,
    circuit_id ASC

LIMIT 10;

-- COMMAND ----------

WITH base_summary AS (

    SELECT
        COUNT(*) AS total_records,
        SUM(points) AS total_points

    FROM f1_lakehouse.analytics.vw_race_results

),

circuit_summary AS (

    SELECT
        SUM(race_entries) AS total_records,
        SUM(total_points) AS total_points

    FROM f1_lakehouse.analytics.vw_driver_circuit_performance

)

SELECT
    b.total_records AS base_records,
    c.total_records AS aggregated_records,

    b.total_points AS base_points,
    c.total_points AS aggregated_points,

    CASE
        WHEN b.total_records = c.total_records
         AND b.total_points = c.total_points
        THEN 'PASSED'
        ELSE 'FAILED'
    END AS validation_status

FROM base_summary AS b
CROSS JOIN circuit_summary AS c;

-- COMMAND ----------

SELECT
    COUNT(*) AS invalid_records,

    CASE
        WHEN COUNT(*) = 0 THEN 'PASSED'
        ELSE 'FAILED'
    END AS validation_status

FROM f1_lakehouse.analytics.vw_driver_circuit_performance

WHERE race_starts > race_entries
    OR race_starts + dns_results <> race_entries
    OR wins > podiums
    OR podiums > race_starts
    OR classified_results > race_starts
    OR valid_finish_results <> classified_results
    OR win_rate_pct NOT BETWEEN 0 AND 100
    OR podium_rate_pct NOT BETWEEN 0 AND 100
    OR avg_finish_position <= 0
    OR total_points < 0;

-- COMMAND ----------

WITH duplicate_keys AS (

    SELECT
        driver_id,
        circuit_id,
        COUNT(*) AS record_count

    FROM f1_lakehouse.analytics.vw_driver_circuit_performance

    GROUP BY
        driver_id,
        circuit_id

    HAVING COUNT(*) > 1

)

SELECT
    COUNT(*) AS duplicate_business_keys,

    CASE
        WHEN COUNT(*) = 0 THEN 'PASSED'
        ELSE 'FAILED'
    END AS validation_status

FROM duplicate_keys;

-- COMMAND ----------

-- MAGIC
-- MAGIC %md
-- MAGIC
-- MAGIC ## 05. Business Question 3 - Average Positions Gained
-- MAGIC
-- MAGIC Analyze how many grid positions drivers gain
-- MAGIC or lose during races.
-- MAGIC
-- MAGIC Use classified race results with valid
-- MAGIC starting positions.
-- MAGIC
-- MAGIC Positive values represent positions gained,
-- MAGIC negative values represent positions lost,
-- MAGIC and zero represents no change.
-- MAGIC
-- MAGIC Include sample size to provide context
-- MAGIC for performance comparisons.

-- COMMAND ----------

CREATE OR REPLACE VIEW
    f1_lakehouse.analytics.vw_driver_positions_gained
AS

SELECT
    driver_id,
    driver_name,

    COUNT(*) AS race_entries,

    COUNT(positions_gained) AS valid_results,

    COUNT(*) - COUNT(positions_gained)
        AS excluded_results,

    ROUND(
        AVG(
            CASE
                WHEN positions_gained IS NOT NULL
                THEN grid_position
            END
        ), 2
    ) AS avg_grid_position,

    ROUND(
        AVG(
            CASE
                WHEN positions_gained IS NOT NULL
                THEN finish_position
            END
        ), 2
    ) AS avg_finish_position,

    SUM(positions_gained)
        AS total_positions_gained,

    ROUND(AVG(positions_gained), 2)
        AS avg_positions_gained,

    MAX(positions_gained)
        AS best_positions_gained,

    MIN(positions_gained)
        AS worst_positions_gained,

    COUNT_IF(positions_gained > 0)
        AS races_gained_positions,

    COUNT_IF(positions_gained < 0)
        AS races_lost_positions,

    COUNT_IF(positions_gained = 0)
        AS races_unchanged_positions,

    ROUND(
        100.0 * TRY_DIVIDE(
            COUNT_IF(positions_gained > 0),
            COUNT(positions_gained)
        ), 2
    ) AS positions_gained_rate_pct

FROM f1_lakehouse.analytics.vw_race_results

GROUP BY
    driver_id,
    driver_name;

-- COMMAND ----------

SELECT
    ROW_NUMBER() OVER (
        ORDER BY
            avg_positions_gained DESC,
            valid_results DESC,
            driver_id ASC
    ) AS driver_rank,

    driver_name,
    race_entries,
    valid_results,
    avg_grid_position,
    avg_finish_position,
    avg_positions_gained,
    total_positions_gained,
    best_positions_gained,
    positions_gained_rate_pct

FROM f1_lakehouse.analytics.vw_driver_positions_gained

WHERE valid_results >= 10

ORDER BY driver_rank

LIMIT 10;

-- COMMAND ----------

SELECT *
FROM f1_lakehouse.analytics.vw_driver_positions_gained
WHERE driver_id = 'hamilton';

-- COMMAND ----------

WITH base_summary AS (

    SELECT
        COUNT(*) AS total_records,
        COUNT(positions_gained) AS valid_results,
        SUM(positions_gained) AS total_positions_gained

    FROM f1_lakehouse.analytics.vw_race_results

),

driver_summary AS (

    SELECT
        SUM(race_entries) AS total_records,
        SUM(valid_results) AS valid_results,
        SUM(total_positions_gained) AS total_positions_gained

    FROM f1_lakehouse.analytics.vw_driver_positions_gained

)

SELECT
    b.total_records AS base_records,
    d.total_records AS aggregated_records,

    b.valid_results AS base_valid_results,
    d.valid_results AS aggregated_valid_results,

    b.total_positions_gained AS base_positions_gained,
    d.total_positions_gained AS aggregated_positions_gained,

    CASE
        WHEN b.total_records = d.total_records
         AND b.valid_results = d.valid_results
         AND b.total_positions_gained = d.total_positions_gained
        THEN 'PASSED'
        ELSE 'FAILED'
    END AS validation_status

FROM base_summary AS b
CROSS JOIN driver_summary AS d;

-- COMMAND ----------

SELECT
    COUNT(*) AS invalid_records,

    CASE
        WHEN COUNT(*) = 0 THEN 'PASSED'
        ELSE 'FAILED'
    END AS validation_status

FROM f1_lakehouse.analytics.vw_driver_positions_gained

WHERE valid_results + excluded_results <> race_entries

    OR races_gained_positions
        + races_lost_positions
        + races_unchanged_positions <> valid_results

    OR positions_gained_rate_pct NOT BETWEEN 0 AND 100

    OR best_positions_gained < worst_positions_gained

    OR ABS(
        avg_grid_position
        - avg_finish_position
        - avg_positions_gained
    ) > 0.02;

-- COMMAND ----------

WITH duplicate_keys AS (

    SELECT
        driver_id,
        COUNT(*) AS record_count

    FROM f1_lakehouse.analytics.vw_driver_positions_gained

    GROUP BY driver_id

    HAVING COUNT(*) > 1

)

SELECT
    COUNT(*) AS duplicate_business_keys,

    CASE
        WHEN COUNT(*) = 0 THEN 'PASSED'
        ELSE 'FAILED'
    END AS validation_status

FROM duplicate_keys;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC
-- MAGIC ## 06. Business Question 4 - Driver Season Performance
-- MAGIC
-- MAGIC Analyze driver performance across seasons.
-- MAGIC
-- MAGIC Compare race starts, total race points,
-- MAGIC average points per start, finishing positions,
-- MAGIC positions gained, wins and podiums.
-- MAGIC
-- MAGIC Use a window function to calculate
-- MAGIC season-over-season performance changes.
-- MAGIC
-- MAGIC Sprint race results are not included.

-- COMMAND ----------

CREATE OR REPLACE VIEW
    f1_lakehouse.analytics.vw_driver_season_performance
AS

WITH season_metrics AS (

    SELECT
        driver_id,
        driver_name,
        season,

        COUNT(*) AS race_entries,

        COUNT_IF(NOT is_dns) AS race_starts,

        COUNT_IF(is_classified) AS classified_results,

        SUM(points) AS total_points,

        ROUND(
            AVG(
                CASE
                    WHEN NOT is_dns THEN points
                END
            ), 2
        ) AS avg_points_per_start,

        ROUND(AVG(finish_position), 2)
            AS avg_finish_position,

        ROUND(AVG(positions_gained), 2)
            AS avg_positions_gained,

        COUNT(positions_gained)
            AS valid_positions_gained_results,

        COUNT_IF(is_win) AS wins,

        COUNT_IF(is_podium) AS podiums,

        COUNT_IF(is_dnf) AS dnf_results,

        COUNT_IF(is_dns) AS dns_results,

        COUNT_IF(is_dsq) AS dsq_results,

        ROUND(
            100.0 * TRY_DIVIDE(
                COUNT_IF(is_win),
                COUNT_IF(NOT is_dns)
            ), 2
        ) AS win_rate_pct,

        ROUND(
            100.0 * TRY_DIVIDE(
                COUNT_IF(is_podium),
                COUNT_IF(NOT is_dns)
            ), 2
        ) AS podium_rate_pct

    FROM f1_lakehouse.analytics.vw_race_results

    GROUP BY
        driver_id,
        driver_name,
        season

),

season_comparison AS (

    SELECT
        *,

        LAG(season) OVER (
            PARTITION BY driver_id
            ORDER BY season
        ) AS previous_season,

        LAG(total_points) OVER (
            PARTITION BY driver_id
            ORDER BY season
        ) AS previous_season_points,

        LAG(avg_points_per_start) OVER (
            PARTITION BY driver_id
            ORDER BY season
        ) AS previous_avg_points_per_start

    FROM season_metrics

)

SELECT
    *,

    CASE
        WHEN previous_season = season - 1
        THEN total_points - previous_season_points
    END AS points_yoy_change,

    CASE
        WHEN previous_season = season - 1
        THEN ROUND(
            avg_points_per_start
            - previous_avg_points_per_start, 2
        )
    END AS avg_points_yoy_change,

    CASE
        WHEN previous_season = season - 1
        THEN ROUND(
            100.0 * TRY_DIVIDE(
                total_points - previous_season_points,
                previous_season_points
            ), 2
        )
    END AS points_yoy_change_pct

FROM season_comparison;

-- COMMAND ----------

SELECT
    season,
    driver_name,
    race_starts,
    total_points,
    avg_points_per_start,
    avg_finish_position,
    avg_positions_gained,
    wins,
    podiums,
    dnf_results,
    points_yoy_change,
    avg_points_yoy_change,
    points_yoy_change_pct

FROM f1_lakehouse.analytics.vw_driver_season_performance

WHERE driver_id = 'max_verstappen'

ORDER BY season;

-- COMMAND ----------

SELECT
    season,
    driver_name,
    race_starts,
    total_points,
    avg_points_per_start,
    wins,
    podiums,
    avg_points_yoy_change

FROM f1_lakehouse.analytics.vw_driver_season_performance

WHERE driver_id IN (
    'max_verstappen',
    'hamilton',
    'leclerc'
)

ORDER BY
    season,
    total_points DESC;

-- COMMAND ----------

WITH base_summary AS (

    SELECT
        COUNT(*) AS total_records,
        SUM(points) AS total_points

    FROM f1_lakehouse.analytics.vw_race_results

),

season_summary AS (

    SELECT
        SUM(race_entries) AS total_records,
        SUM(total_points) AS total_points

    FROM f1_lakehouse.analytics.vw_driver_season_performance

)

SELECT
    b.total_records AS base_records,
    s.total_records AS aggregated_records,

    b.total_points AS base_points,
    s.total_points AS aggregated_points,

    CASE
        WHEN b.total_records = s.total_records
         AND b.total_points = s.total_points
        THEN 'PASSED'
        ELSE 'FAILED'
    END AS validation_status

FROM base_summary AS b
CROSS JOIN season_summary AS s;

-- COMMAND ----------

SELECT
    COUNT(*) AS invalid_records,

    CASE
        WHEN COUNT(*) = 0 THEN 'PASSED'
        ELSE 'FAILED'
    END AS validation_status

FROM f1_lakehouse.analytics.vw_driver_season_performance

WHERE season NOT BETWEEN 2021 AND 2025

    OR race_starts + dns_results <> race_entries

    OR wins > podiums

    OR podiums > race_starts

    OR classified_results > race_starts

    OR win_rate_pct NOT BETWEEN 0 AND 100

    OR podium_rate_pct NOT BETWEEN 0 AND 100

    OR total_points < 0

    OR (
        (
            previous_season IS NULL
            OR previous_season <> season - 1
        )
        AND (
            points_yoy_change IS NOT NULL
            OR avg_points_yoy_change IS NOT NULL
            OR points_yoy_change_pct IS NOT NULL
        )
    )

    OR (
        previous_season = season - 1
        AND NOT (
            points_yoy_change <=>
            (total_points - previous_season_points)
        )
    );

-- COMMAND ----------

WITH duplicate_keys AS (

    SELECT
        driver_id,
        season,
        COUNT(*) AS record_count

    FROM f1_lakehouse.analytics.vw_driver_season_performance

    GROUP BY
        driver_id,
        season

    HAVING COUNT(*) > 1

)

SELECT
    COUNT(*) AS duplicate_business_keys,

    CASE
        WHEN COUNT(*) = 0 THEN 'PASSED'
        ELSE 'FAILED'
    END AS validation_status

FROM duplicate_keys;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC
-- MAGIC ## 07. Business Question 5 - Constructor Circuit Performance
-- MAGIC
-- MAGIC Compare constructor performance across circuits.
-- MAGIC
-- MAGIC Aggregate driver-level race results into
-- MAGIC constructor-level performance metrics.
-- MAGIC
-- MAGIC Distinguish individual driver entries
-- MAGIC from distinct constructor race appearances.
-- MAGIC
-- MAGIC Use average points per race as the primary
-- MAGIC ranking metric and include sample size.
-- MAGIC
-- MAGIC Sprint race results are not included.

-- COMMAND ----------

CREATE OR REPLACE VIEW
    f1_lakehouse.analytics.vw_constructor_circuit_performance
AS

SELECT
    constructor_id,
    constructor_name,
    circuit_id,
    circuit_name,
    country,

    COUNT(DISTINCT race_id)
        AS race_appearances,

    COUNT(DISTINCT CASE
        WHEN NOT is_dns THEN race_id
    END) AS race_starts,

    COUNT(*) AS driver_entries,

    COUNT_IF(NOT is_dns) AS driver_starts,

    COUNT(DISTINCT driver_id)
        AS unique_drivers,

    COUNT_IF(is_classified)
        AS classified_results,

    SUM(points) AS total_points,

    ROUND(
        TRY_DIVIDE(
            SUM(points),
            COUNT(DISTINCT race_id)
        ), 2
    ) AS avg_points_per_race,

    ROUND(AVG(finish_position), 2)
        AS avg_finish_position,

    ROUND(AVG(positions_gained), 2)
        AS avg_positions_gained,

    COUNT(positions_gained)
        AS valid_positions_gained_results,

    COUNT_IF(is_win) AS wins,

    COUNT_IF(is_podium) AS podiums,

    COUNT(DISTINCT CASE
        WHEN is_podium THEN race_id
    END) AS races_with_podium,

    COUNT_IF(is_dnf) AS dnf_results,

    COUNT_IF(is_dns) AS dns_results,

    COUNT_IF(is_dsq) AS dsq_results,

    ROUND(
        100.0 * TRY_DIVIDE(
            COUNT_IF(is_win),
            COUNT(DISTINCT CASE
                WHEN NOT is_dns THEN race_id
            END)
        ), 2
    ) AS win_rate_pct,

    ROUND(
        100.0 * TRY_DIVIDE(
            COUNT(DISTINCT CASE
                WHEN is_podium THEN race_id
            END),
            COUNT(DISTINCT CASE
                WHEN NOT is_dns THEN race_id
            END)
        ), 2
    ) AS podium_race_rate_pct

FROM f1_lakehouse.analytics.vw_race_results

GROUP BY
    constructor_id,
    constructor_name,
    circuit_id,
    circuit_name,
    country;

-- COMMAND ----------

WITH eligible_constructors AS (

    SELECT *
    FROM f1_lakehouse.analytics.vw_constructor_circuit_performance

    WHERE circuit_id = 'silverstone'
        AND race_starts >= 3

)

SELECT
    ROW_NUMBER() OVER (
        ORDER BY
            avg_points_per_race DESC,
            race_starts DESC,
            constructor_id ASC
    ) AS constructor_rank,

    constructor_name,
    circuit_name,
    race_appearances,
    race_starts,
    driver_entries,
    total_points,
    avg_points_per_race,
    avg_finish_position,
    wins,
    podiums,
    win_rate_pct,
    podium_race_rate_pct

FROM eligible_constructors

ORDER BY constructor_rank;

-- COMMAND ----------

SELECT
    constructor_name,
    circuit_name,
    country,
    race_starts,
    total_points,
    avg_points_per_race,
    avg_finish_position,
    wins,
    podiums,
    win_rate_pct

FROM f1_lakehouse.analytics.vw_constructor_circuit_performance

WHERE constructor_id = 'ferrari'
    AND race_starts >= 3

ORDER BY
    avg_points_per_race DESC,
    race_starts DESC,
    circuit_id ASC

LIMIT 10;

-- COMMAND ----------

WITH base_summary AS (

    SELECT
        COUNT(*) AS total_records,
        SUM(points) AS total_points

    FROM f1_lakehouse.analytics.vw_race_results

),

constructor_summary AS (

    SELECT
        SUM(driver_entries) AS total_records,
        SUM(total_points) AS total_points

    FROM f1_lakehouse.analytics.vw_constructor_circuit_performance

)

SELECT
    b.total_records AS base_records,
    c.total_records AS aggregated_records,

    b.total_points AS base_points,
    c.total_points AS aggregated_points,

    CASE
        WHEN b.total_records = c.total_records
         AND b.total_points = c.total_points
        THEN 'PASSED'
        ELSE 'FAILED'
    END AS validation_status

FROM base_summary AS b
CROSS JOIN constructor_summary AS c;

-- COMMAND ----------

SELECT
    COUNT(*) AS invalid_records,

    CASE
        WHEN COUNT(*) = 0 THEN 'PASSED'
        ELSE 'FAILED'
    END AS validation_status

FROM f1_lakehouse.analytics.vw_constructor_circuit_performance

WHERE race_appearances > driver_entries

    OR race_starts > race_appearances

    OR race_starts > driver_starts

    OR driver_starts + dns_results <> driver_entries

    OR classified_results > driver_starts

    OR wins > race_starts

    OR wins > races_with_podium

    OR races_with_podium > podiums

    OR races_with_podium > race_starts

    OR podiums > driver_starts

    OR win_rate_pct NOT BETWEEN 0 AND 100

    OR podium_race_rate_pct NOT BETWEEN 0 AND 100

    OR total_points < 0

    OR avg_finish_position <= 0;

-- COMMAND ----------

WITH duplicate_keys AS (

    SELECT
        constructor_id,
        circuit_id,
        COUNT(*) AS record_count

    FROM f1_lakehouse.analytics.vw_constructor_circuit_performance

    GROUP BY
        constructor_id,
        circuit_id

    HAVING COUNT(*) > 1

)

SELECT
    COUNT(*) AS duplicate_business_keys,

    CASE
        WHEN COUNT(*) = 0 THEN 'PASSED'
        ELSE 'FAILED'
    END AS validation_status

FROM duplicate_keys;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC
-- MAGIC ## 08. Final Analytics Validation
-- MAGIC
-- MAGIC Validate the completeness of the analytics layer.
-- MAGIC
-- MAGIC Verify that all required views exist,
-- MAGIC check their record counts and manually
-- MAGIC reconcile selected business metrics
-- MAGIC against the Gold layer.

-- COMMAND ----------

SHOW VIEWS IN f1_lakehouse.analytics;

-- COMMAND ----------

SELECT
    'vw_race_results' AS view_name,
    COUNT(*) AS row_count
FROM f1_lakehouse.analytics.vw_race_results

UNION ALL

SELECT
    'vw_driver_circuit_history',
    COUNT(*)
FROM f1_lakehouse.analytics.vw_driver_circuit_history

UNION ALL

SELECT
    'vw_driver_circuit_performance',
    COUNT(*)
FROM f1_lakehouse.analytics.vw_driver_circuit_performance

UNION ALL

SELECT
    'vw_driver_positions_gained',
    COUNT(*)
FROM f1_lakehouse.analytics.vw_driver_positions_gained

UNION ALL

SELECT
    'vw_driver_season_performance',
    COUNT(*)
FROM f1_lakehouse.analytics.vw_driver_season_performance

UNION ALL

SELECT
    'vw_constructor_circuit_performance',
    COUNT(*)
FROM f1_lakehouse.analytics.vw_constructor_circuit_performance;

-- COMMAND ----------

SELECT
    r.season,
    r.race_date,
    f.grid_position,
    f.finish_position,
    f.positions_gained,
    f.points,
    f.status,
    f.is_dns

FROM f1_lakehouse.gold.fact_race_results AS f

INNER JOIN f1_lakehouse.gold.dim_races AS r
    ON f.race_id = r.race_id

WHERE f.driver_id = 'max_verstappen'
    AND f.circuit_id = 'silverstone'

ORDER BY r.race_date DESC;

-- COMMAND ----------

SELECT
    driver_name,
    circuit_name,
    race_entries,
    race_starts,
    total_points,
    avg_points_per_start,
    avg_finish_position,
    wins,
    podiums

FROM f1_lakehouse.analytics.vw_driver_circuit_performance

WHERE driver_id = 'max_verstappen'
    AND circuit_id = 'silverstone';