# Bronze Data Ingestion

## Overview

The Bronze ingestion layer collects historical Formula 1 race results from the Jolpica F1 REST API and stores the original JSON responses in Azure Data Lake Storage Gen2.

The ingestion process is orchestrated by Azure Data Factory.

## Scope

- Seasons: 2021–2025
- Data source: Jolpica F1 API
- Data format: Raw JSON
- Pagination: Offset-based
- Page size: 100 records
- Processing mode: Sequential batch ingestion

## Architecture

```text
Jolpica F1 API
      |
Azure Data Factory
      |
ADLS Gen2 - Bronze
      |
Databricks Validation
```

## Pipeline Components

| Pipeline | Responsibility |
|---|---|
| `pl_ingest_jolpica_all_seasons` | Iterates through the configured seasons. |
| `pl_ingest_jolpica_season` | Retrieves metadata and manages pagination. |
| `pl_ingest_jolpica_page` | Copies a single API response to Bronze storage. |

## Storage Structure

```text
bronze/
└── jolpica/
    └── race_results/
        ├── season=2021/
        ├── season=2022/
        ├── season=2023/
        ├── season=2024/
        └── season=2025/
            ├── offset_0.json
            ├── offset_100.json
            ├── offset_200.json
            ├── offset_300.json
            └── offset_400.json
```

Raw API responses are preserved without business transformations.

## Error Handling

The ingestion process implements:

- Activity retries for transient failures.
- A 30-second retry interval.
- Activity and loop timeouts.
- Sequential API requests with a delay between pages.
- An error flag to terminate pagination after a failed page ingestion.
- Explicit pipeline failure reporting.

## Idempotency

Output filenames are determined by season and pagination offset.

Repeated execution with the same parameters overwrites existing files instead of creating additional copies.

This approach assumes a fixed page size and a stable historical dataset.

## Data Quality

The `01_bronze_validation.py` Databricks notebook performs the following checks:

- Record completeness against API metadata.
- Pagination completeness.
- Business key uniqueness.
- Metadata consistency.
- Season consistency.
- File naming consistency.
- Record count validation for individual pages.

The business key consists of:

```text
season + round + driverId
```

## Security

Azure Data Factory accesses Bronze storage through its system-assigned managed identity.

Storage containers are private, and authentication credentials are not stored in the repository.

## Version Control

Azure Data Factory definitions are maintained in the `adf/` directory.

Validation notebooks are maintained in the `notebooks/` directory.

## Known Limitations

- Historical batch ingestion only.
- Fixed pagination size.
- No incremental ingestion.
- No atomic replacement of complete season datasets.
- API availability and rate limits depend on the external provider.

## Next Steps

Transform raw JSON responses into validated, typed and deduplicated Delta tables in the Silver layer using PySpark.