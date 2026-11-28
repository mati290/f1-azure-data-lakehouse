# Setup and Reproducibility

[English](setup.md) | [Polski](pl/setup.md)

## 1. Overview

The F1 Performance Analytics project supports three independent exploration paths.

| Mode | Azure required | Purpose |
|---|---|---|
| Local dashboard | No | Explore historical Formula 1 performance |
| Local automated tests | No | Validate transformations and business logic |
| Full Azure deployment | Yes | Reproduce the end-to-end data pipeline |

The recommended starting point for recruiters and reviewers is the local dashboard.

## 2. Prerequisites

### Local Dashboard

- Python 3.12
- Git
- Internet access for dependency installation
- A web browser

### Automated Tests

- Python 3.12
- Java 17
- Git

### Full Azure Deployment

- Active Azure subscription
- Azure resource creation permissions
- Azure Data Factory
- Azure Data Lake Storage Gen2
- Azure Databricks Premium workspace
- Serverless compute availability
- Unity Catalog
- GitHub account

Visual Studio Code is recommended but not required.

## 3. Clone the Repository

```bash
git clone https://github.com/mati290/f1-azure-data-lakehouse.git
cd f1-azure-data-lakehouse
```

## 4. Configure the Python Environment

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the environment on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Activate the environment on Linux or macOS:

```bash
source .venv/bin/activate
```

Upgrade pip:

```bash
python -m pip install --upgrade pip
```

## 5. Run the Dashboard Locally

Install dashboard dependencies:

```bash
python -m pip install -r dashboard/requirements.txt
```

Check dependency consistency:

```bash
python -m pip check
```

Start Streamlit from the repository root:

```bash
python -m streamlit run dashboard/app.py
```

Open the application in a browser:

http://localhost:8501

### Dashboard Dataset

| Property | Value |
|---|---|
| Seasons | 2021–2025 |
| Initial records | 2,278 |
| Columns | 38 |
| Format | Parquet |
| Source | Gold analytics view |
| Refresh | Manual snapshot export |

The dataset and its metadata are included in the repository:

- `dashboard/data/race_results.parquet`
- `dashboard/data/metadata.json`

No Azure credentials, Databricks connection or live API requests are required.

See the [Dashboard Documentation](../dashboard/README.md) for additional information.

## 6. Run Automated Tests

Verify Python and Java:

```bash
python --version
java -version
```

Install development and dashboard dependencies:

```bash
python -m pip install -r requirements-dev.txt
python -m pip install -r dashboard/requirements.txt
```

Validate dependencies:

```bash
python -m pip check
```

Run the complete test suite:

```bash
python -m pytest -q
```

The MVP test suite contains 57 tests:

| Test suite | Tests |
|---|---:|
| PySpark transformations and data quality | 21 |
| Dashboard | 36 |
| Total | 57 |

Run only pipeline unit tests:

```bash
python -m pytest tests -v
```

Run only dashboard tests:

```bash
python -m pytest dashboard/tests -v
```

The automated tests do not require Azure credentials.

CI executes these tests using Python 3.12 and Java 17.

A Pandas compatibility warning was observed during local PySpark testing. Passing tests do not guarantee compatibility with every Pandas-dependent Spark operation.

## 7. Configure Azure Infrastructure

Create and configure the required resources:

1. Azure Resource Group.
2. ADLS Gen2 storage account with hierarchical namespace enabled.
3. Private Bronze, Silver and Gold containers.
4. Azure Data Factory V2.
5. Azure Databricks Premium workspace with Serverless support.
6. Databricks Access Connector.
7. Azure budget and spending alerts.

Configure Managed Identity and scoped Azure RBAC permissions.

Create the Unity Catalog storage credential and external locations.

Create the `f1_lakehouse` catalog and required schemas:

- `bronze`
- `silver`
- `gold`
- `analytics`

See [Azure Environment Setup](azure_setup.md) for the original environment configuration and permission model.

Resource names, regions and identifiers must be adapted to the target environment.

## 8. Configure Azure Data Factory

The version-controlled ADF definitions are stored in:

`adf/`

Configure the GitHub integration and environment-specific linked services:

- `ls_http_jolpica`
- `ls_adls_gen2_f1`
- `ls_databricks_f1`

Validate storage and API connectivity.

Review the ingestion pipelines:

- `pl_ingest_jolpica_page`
- `pl_ingest_jolpica_season`
- `pl_ingest_jolpica_all_seasons`
- `pl_f1_end_to_end`

Update environment-specific references before publishing the configuration.

See [Bronze Data Ingestion](bronze_ingestion.md).

## 9. Configure Azure Databricks

Clone the GitHub repository into a Databricks Git folder.

Review and adapt storage paths and catalog configuration to the target environment.

Run the environment validation notebook:

`notebooks/00_environment_validation.py`

Configure the Databricks Job using:

`databricks/jobs/job_f1_lakehouse.json`

Replace the workspace path placeholders:

- `<WORKSPACE_NOTEBOOK_ROOT>`
- `<WORKSPACE_GIT_ROOT>`

Configure the following tasks in dependency order:

| Task | Source file |
|---|---|
| validate_bronze | notebooks/01_bronze_validation.py |
| bronze_to_silver | notebooks/02_bronze_to_silver.py |
| silver_to_gold | notebooks/03_silver_to_gold.py |
| deploy_analytics | sql/04_sql_business_analytics.sql |

Import the SQL source as a Databricks SQL notebook if required by the notebook task configuration.

Configure the Job execution identity and grant the ADF Managed Identity the required Job permissions.

Update the Databricks Job ID in the ADF orchestration pipeline.

## 10. Execute the End-to-End Pipeline

Open the published Azure Data Factory pipeline:

`pl_f1_end_to_end`

Execute a full historical load using the seasons parameter:

```json
["2021", "2022", "2023", "2024", "2025"]
```

Monitor execution in Azure Data Factory Monitor and Databricks Job Runs.

The pipeline performs:

1. Input parameter validation.
2. Historical data ingestion.
3. Bronze validation.
4. Silver transformation.
5. Gold dimensional modeling.
6. SQL analytics deployment.

A selected season refresh is also supported:

```json
["2025"]
```

The remaining historical seasons must already exist in Bronze storage.

Silver and Gold transformations still rebuild the complete historical dataset.

## 11. Validate the Results

Run the post-execution validation notebook:

`notebooks/05_end_to_end_validation.py`

The original validated dataset produced the following results:

| Dataset | Records |
|---|---:|
| Bronze JSON files | 25 |
| Silver race results | 2,278 |
| Gold drivers | 35 |
| Gold constructors | 12 |
| Gold circuits | 28 |
| Gold races | 114 |
| Gold race results | 2,278 |

Additional validation results:

- Duplicate business keys: 0.
- Orphan foreign keys: 0.
- Analytical SQL views: 6.
- Total Grand Prix race points: 11,540.50.

These values represent the original historical dataset and may change if the source provider corrects historical records.

See [End-to-End Pipeline](end_to_end_pipeline.md).

## 12. Refresh the Dashboard Snapshot

After successfully rebuilding the Gold layer, execute:

`notebooks/06_export_dashboard_snapshot.ipynb`

The notebook exports the following analytical view:

`f1_lakehouse.analytics.vw_race_results`

Output files:

- `dashboard/data/race_results.parquet`
- `dashboard/data/metadata.json`

Validate the exported files and review the changes before committing them to GitHub.

Pull the updated snapshot into the local repository and restart the dashboard.

Snapshot export is a manual operation independent of the main ADF pipeline.

## 13. Troubleshooting

| Problem | Suggested action |
|---|---|
| Python command unavailable | Verify Python installation and PATH |
| Missing Python package | Install dependencies in the active virtual environment |
| Spark initialization failure | Verify Java 17 and JAVA_HOME |
| Missing snapshot | Verify the dashboard/data directory |
| ADF HTTP 403 | Review Managed Identity and container-scoped RBAC |
| Databricks access failure | Review workspace, Unity Catalog and Job permissions |
| Pipeline validation failure | Inspect ADF and Databricks execution logs |
| Unsupported Azure region | Select a supported region for the required service |

## 14. Security and Cost Management

- Never commit passwords, tokens or storage account keys.
- Use Managed Identity and scoped permissions.
- Keep storage containers private.
- Configure Azure budget alerts.
- Execute cloud workloads only when required.
- Review resources and storage costs after testing.

Azure budget alerts do not automatically stop resource consumption.

The local dashboard is the preferred demonstration option when cloud access is unnecessary.

## 15. Reproducibility Limitations

The local dashboard and automated tests can be explored independently of Azure.

The complete cloud environment requires manual configuration of infrastructure, identities, permissions and workspace-specific paths.

Automated infrastructure provisioning and deployment are outside the MVP scope.

The original Azure environment was validated during development. A complete deployment into a separate Azure environment has not been independently tested.

Historical source corrections, dependency updates and Azure service availability may affect reproducibility.

## 16. Related Documentation

- [Solution Architecture](architecture.md)
- [Azure Environment Setup](azure_setup.md)
- [Data Source](data_source.md)
- [End-to-End Pipeline](end_to_end_pipeline.md)
- [Data Quality and CI](data_quality_and_ci.md)
- [Dashboard Documentation](../dashboard/README.md)
- [Main README](../README.md)