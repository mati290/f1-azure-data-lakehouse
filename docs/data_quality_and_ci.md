# Data Quality and Continuous Integration

## 1. Overview

The F1 Azure Data Lakehouse implements automated data quality checks and lightweight continuous integration to improve the reliability, maintainability and reproducibility of data transformations.

The testing framework operates independently of Azure infrastructure and does not require cloud credentials.

## 2. Objectives

- Protect core PySpark transformations against regressions.
- Validate business rules and data integrity.
- Separate reusable transformation logic from notebook orchestration.
- Automate testing through GitHub Actions.
- Support local development without Azure dependencies.

## 3. Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Development environment |
| PySpark | Data transformations |
| pytest | Automated testing framework |
| Java 17 | Local Spark runtime |
| GitHub Actions | Continuous integration |
| Azure Databricks | Lakehouse integration and regression validation |

## 4. Project Structure

| File | Responsibility |
|---|---|
| `src/__init__.py` | Python package initialization |
| `src/transformations.py` | Reusable data transformation functions |
| `src/data_quality.py` | Business rule validation |
| `tests/conftest.py` | Spark session and test fixtures |
| `tests/test_transformations.py` | Transformation tests |
| `tests/test_data_quality.py` | Data quality tests |
| `pytest.ini` | pytest configuration |
| `requirements-dev.txt` | Development dependencies |
| `.github/workflows/ci.yml` | CI workflow configuration |

## 5. Reusable Transformations

The Silver notebook delegates core transformation logic to reusable Python functions.

| Function | Responsibility |
|---|---|
| `cast_race_results()` | Convert raw values into appropriate Spark data types |
| `normalize_strings()` | Trim whitespace and convert empty strings to null values |
| `deduplicate_records()` | Remove exact duplicate records |

Conflicting records sharing the same business key are not silently removed. They are detected by the data quality validation layer.

## 6. Data Quality Rules

The Silver layer uses the following composite business key:

`season + round + driver_id`

| Rule | Expected behaviour |
|---|---|
| Business key uniqueness | Reject duplicate race-driver keys |
| Business key completeness | Reject null business key values |
| Non-negative points | Reject negative points |
| Points completeness | Reject null points |
| Fractional points | Preserve valid decimal values |
| Exact duplicates | Remove identical records |

Invalid records detected by the shared validation functions raise a `DataQualityError`.

Additional notebook-level validations protect historical coverage, required columns, numeric ranges and derived business metrics.

## 7. Automated Test Coverage

The test suite contains 21 automated tests.

| Test category | Number of tests |
|---|---:|
| Data type conversion | 5 |
| String normalization | 4 |
| Deduplication | 3 |
| Data quality validation | 9 |
| **Total** | **21** |

Synthetic fixtures represent valid and intentionally invalid Formula 1 race results.

The tests cover both successful transformations and expected validation failures.

## 8. Running Tests Locally

Prerequisites:

- Python 3.12
- Java 17
- Python virtual environment

Install development dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

Check dependency consistency:

```bash
python -m pip check
```

Execute the test suite:

```bash
python -m pytest
```

Expected result:

```text
21 passed
```

No Azure credentials or live API requests are required.

## 9. Continuous Integration

The GitHub Actions workflow automatically