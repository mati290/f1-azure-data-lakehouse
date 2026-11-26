# Data Source – Jolpica F1 API

## Overview

Jolpica F1 is a REST API providing historical Formula 1 data and maintaining compatibility with the Ergast API.

- Base URL: `https://api.jolpi.ca/ergast/f1`
- Source repository: https://github.com/jolpica/jolpica-f1
- Response format: JSON
- HTTP method: GET
- Authentication: Not required for the tested endpoint
- Planned MVP scope: 2021–2025 seasons

## Primary Endpoint

`GET /{season}/results/`

The endpoint provides race results together with nested driver, constructor, circuit and race information.

## Pagination

The API uses offset-based pagination.

| Parameter | Description |
|---|---|
| limit | Requested number of records per response |
| offset | Number of records skipped |
| total | Total number of available records |

### Exploration Results

| Metric | Value |
|---|---:|
| Tested season | 2025 |
| Total reported records | 479 |
| Requested page size | 100 |
| HTTP requests | 5 |
| Downloaded records | 479 |

## Data Grain

One record represents the result of one driver in one race.

Natural composite key:

`season + round + driverId`

## Data Dictionary

| Source field | Target field | Target type |
|---|---|---|
| season | season | Integer |
| round | round | Integer |
| raceName | race_name | String |
| date | race_date | Date |
| Circuit.circuitId | circuit_id | String |
| Driver.driverId | driver_id | String |
| Constructor.constructorId | constructor_id | String |
| grid | grid_position | Integer |
| position | result_position | Integer |
| positionText | position_text | String |
| points | points | Decimal |
| laps | laps | Integer |
| status | status | String |

## Data Quality Considerations

- Numeric values are returned as strings.
- Nested arrays require flattening.
- Pagination must be handled to prevent incomplete ingestion.
- Composite keys must be checked for uniqueness.
- Optional fields may be missing.
- DNF, DNS and DSQ require explicit handling.
- Grid position zero requires special handling.
- Driver numbers may change over time and should not be used as identifiers.

## Planned Ingestion

Azure Data Factory will handle automated batch ingestion into the Bronze layer.

Python exploration scripts are used for source discovery and validation, not as the primary production ingestion mechanism.

## Open Questions

- Confirm current API rate limits and data usage terms.
- Validate missing fields across all five historical seasons.
- Define classification rules for non-finished races.
- Validate the composite key across the complete historical dataset.