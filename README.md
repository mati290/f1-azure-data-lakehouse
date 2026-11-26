# F1 Performance Analytics

An end-to-end data engineering portfolio project focused on historical Formula 1 race results and performance analytics using the Azure ecosystem.

## Project Status

🚧 In Development — MVP

## Project Objective

Build a reliable and reproducible batch data pipeline that ingests, transforms, validates and serves Formula 1 race data for interactive analytics.

## Business Requirements

The platform aims to answer the following questions:

- How has a driver performed in their last N races at a specific circuit?
- Which circuits are a driver's strongest?
- How many positions does a driver gain or lose during a race?
- How does driver performance change across seasons?
- Which constructors perform best at a selected circuit?

## Data Source

[Jolpica F1 API](https://github.com/jolpica/jolpica-f1)

Initial historical data scope: 2021–2025 seasons.

## Planned Technology Stack

| Technology | Purpose |
|---|---|
| Python | Data processing and reusable functions |
| SQL | Data modeling and business analytics |
| PySpark | Data transformations |
| Azure Data Factory | Data ingestion and orchestration |
| ADLS Gen2 | Data storage |
| Azure Databricks | Data processing |
| Delta Lake | Reliable data tables |
| Unity Catalog | Data organization and governance |
| Streamlit | Interactive analytics dashboard |
| Pytest | Unit testing |
| GitHub Actions | Basic continuous integration |

## Planned Architecture

Jolpica F1 API → Azure Data Factory → ADLS Gen2 → Azure Databricks → Delta Lake → Streamlit

The project follows the Medallion Architecture:

- **Bronze:** Raw API responses.
- **Silver:** Cleaned and validated data.
- **Gold:** Business-ready dimensional model and analytical views.

## Project Structure

| Directory | Description |
|---|---|
| `src/` | Reusable Python modules |
| `notebooks/` | Databricks notebooks |
| `sql/` | SQL queries and views |
| `adf/` | Azure Data Factory configuration |
| `tests/` | Unit tests |
| `app/` | Streamlit application |
| `data/sample/` | Sample data |
| `docs/` | Project documentation |

## Development Setup

Requirements:

- Python 3.12
- Git
- Visual Studio Code

Clone the repository and create a Python virtual environment.

## Roadmap

- [ ] Project initialization
- [ ] REST API exploration
- [ ] Azure environment setup
- [ ] Bronze data ingestion
- [ ] Silver data transformations
- [ ] Gold dimensional model
- [ ] SQL business analytics
- [ ] Pipeline orchestration
- [ ] Data quality and testing
- [ ] Streamlit dashboard
- [ ] Final documentation

## Future Enhancements

- Driver head-to-head comparison
- Qualifying results analysis
- Interactive circuit map
- OpenF1 API integration
- Lap time and tyre strategy analysis
- Telemetry visualization
- Animated race replay

## License

The project source code is licensed under the MIT License. External data remains subject to its respective source terms.

This is an independent educational project and is not affiliated with Formula 1.