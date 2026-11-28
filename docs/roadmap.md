# Project Roadmap

[English](roadmap.md) | [Polski](pl/roadmap.md)

## 1. Purpose

This roadmap describes potential development beyond the initial F1 Azure Data Lakehouse MVP.

Future features are proposals rather than committed release deadlines.

Each enhancement should be implemented as a separately scoped GitHub issue with acceptance criteria.

## 2. v1.0.0 – MVP

Status: Completed.

Scope:

- Historical REST API ingestion.
- Azure Data Lake Storage Gen2.
- Azure Data Factory orchestration.
- Databricks Serverless processing.
- Medallion Architecture.
- Delta Lake tables.
- Gold dimensional model.
- SQL business analytics.
- Automated data quality tests.
- GitHub Actions CI.
- Streamlit dashboard.
- Bilingual portfolio documentation.

## 3. v1.1.0 – Reliability and Analytics

Status: Proposed.

| Feature | Priority |
|---|---|
| Automated SQL assertion enforcement | High |
| Dependency compatibility improvements | High |
| Automated test coverage reporting | Medium |
| Driver head-to-head comparison | Medium |
| Dashboard snapshot refresh automation | Medium |
| Interactive circuit map | Low |

Objective: improve reliability and analytical functionality without significantly increasing infrastructure complexity.

## 4. v1.2.0 – Advanced Data Engineering

Status: Proposed.

| Feature | Priority |
|---|---|
| Incremental ingestion and processing | High |
| Delta MERGE operations | High |
| Pipeline observability and alerting | High |
| Dedicated Job execution identity | High |
| Workload-level cost attribution | Medium |
| Infrastructure as Code | Medium |
| Automated deployment | Medium |
| Enhanced network isolation | Medium |
| Slowly Changing Dimensions Type 2 | Low |

Objective: evaluate production-oriented engineering practices and improve scalability.

## 5. v2.0.0 – Advanced Formula 1 Analytics

Status: Long-term proposal.

| Feature | Priority |
|---|---|
| Qualifying results integration | High |
| Sprint results integration | High |
| OpenF1 API integration | High |
| Lap time analytics | Medium |
| Tyre strategy analysis | Medium |
| Telemetry visualization | Medium |
| Animated race replay | Low |

Objective: expand the analytical dataset beyond historical Grand Prix race results.

Additional source licensing, data availability, API limitations and storage requirements must be evaluated before implementation.

## 6. Development Principles

- Preserve reproducibility of the existing MVP.
- Avoid unnecessary infrastructure complexity.
- Evaluate cloud costs before introducing new workloads.
- Maintain automated regression tests.
- Document architectural decisions.
- Review security and data licensing.
- Maintain English and Polish portfolio documentation.

## 7. Release Management

Proposed release numbering follows Semantic Versioning principles.

Future release contents and dates remain subject to prioritization.

GitHub Issues and GitHub Projects should be used to manage separately scoped development work.

## 8. Related Documentation

- [Main README](../README.md)
- [Solution Architecture](architecture.md)
- [Costs, Security and Technical Trade-offs](costs_security_tradeoffs.md)
- [Data Quality and CI](data_quality_and_ci.md)