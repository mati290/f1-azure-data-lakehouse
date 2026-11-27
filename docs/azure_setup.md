# Azure Environment Setup

## Overview

The F1 Performance Analytics project uses Microsoft Azure to implement a cloud-based data lakehouse following the Medallion Architecture.

The environment is designed for educational and portfolio purposes, with an emphasis on cost optimization, secure authentication and minimal infrastructure complexity.

## Azure Resources

| Resource | Name | Region |
|---|---|---|
| Subscription | Azure for Students | N/A |
| Resource Group | rg-f1-dev | West Europe |
| Storage Account | stf1lakehouse290 | West Europe |
| Data Factory | adf-f1-dev-290 | West Europe |
| Databricks Workspace | dbw-f1-dev | Germany West Central |
| Access Connector | ac-dbw-f1-dev | West Europe |
| Budget | budget-f1-dev | N/A |

## Storage Configuration

Azure Data Lake Storage Gen2 is configured with:

- Standard performance tier
- Locally redundant storage (LRS)
- Hierarchical namespace enabled
- Hot access tier
- Secure transfer enabled
- Anonymous access disabled

### Storage Containers

| Container | Purpose | Planned format |
|---|---|---|
| bronze | Raw API responses | JSON |
| silver | Cleaned and validated data | Delta Lake |
| gold | Business-ready dimensional model | Delta Lake |

## Azure Data Factory

Azure Data Factory is responsible for data ingestion and pipeline orchestration.

Configuration:

- Version: V2
- Integration Runtime: AutoResolveIntegrationRuntime
- Authentication: System-assigned Managed Identity
- Linked Service:  ls_adls_f1
- Storage access: Storage Blob Data Contributor scoped to the bronze container

## Azure Databricks

Configuration:

- Pricing tier: Premium
- Workspace type: Serverless
- Processing engine: Apache Spark
- Programming language: Python / PySpark
- Table format: Delta Lake
- Data governance: Unity Catalog

Germany West Central was selected because West Europe was unavailable for new workspace creation.

The Databricks trial pricing tier was not supported by the Azure for Students subscription.

## Authentication and Authorization

The project uses Managed Identity and Azure RBAC instead of storing storage account keys in source code.

### Databricks Access Connector

Name: ac-dbw-f1-dev

Assigned roles:

- Storage Blob Delegator at storage account scope
- Storage Blob Data Contributor at bronze container scope
- Storage Blob Data Contributor at silver container scope
- Storage Blob Data Contributor at gold container scope

### Unity Catalog Storage Credential

Name: sc_adls_f1

Authentication: Azure Managed Identity

### External Locations

| Name | Container | Access mode |
|---|---|---|
| loc_f1_bronze | bronze | Read only |
| loc_f1_silver | silver | Read / Write |
| loc_f1_gold | gold | Read / Write |

Bronze write access is restricted at the Unity Catalog external location level.

## Unity Catalog Structure

Catalog: f1_lakehouse

Schemas:

- bronze
- silver
- gold

External volumes and external Delta tables will be implemented during subsequent development stages.

## Environment Validation

| Test | Result |
|---|---|
| ADF connection to Bronze | Passed |
| Serverless Compute | Passed |
| Spark version retrieval | Passed |
| PySpark DataFrame creation | Passed |
| Unity Catalog accessibility | Passed |
| Bronze container read access | Passed |
| Silver container read access | Passed |
| Gold container read access | Passed |

Write access and end-to-end pipeline execution will be validated during subsequent implementation stages.

## Troubleshooting

### ADF Connection – HTTP 403 Forbidden

Testing the entire storage account returned HTTP 403 Forbidden.

Testing the specific bronze container resolved the issue without expanding RBAC permissions.

### Databricks Region Availability

West Europe was unavailable for new workspace creation.

Resolution: Germany West Central was selected.

### Databricks Trial Subscription Restriction

Trial workspace creation was not supported by Azure for Students.

Resolution: Premium Serverless workspace was selected.

## Cost Management

- Monthly budget: 10 USD or equivalent billing currency
- Budget alerts: 50%, 80% and 100%
- Minimal infrastructure configuration
- Compute usage limited to development and testing
- No unnecessary scheduled workloads

Budget alerts do not automatically stop resource consumption.

Cross-region data transfer and Serverless Compute may generate additional charges.

## Security Considerations

- No hardcoded credentials
- No secrets committed to GitHub
- Private storage containers
- Managed Identity authentication
- Scoped RBAC permissions
- Public network endpoints for simplified development

Production deployments should consider additional network isolation, stricter access controls and automated infrastructure provisioning.

## Azure Data Factory Linked Services

| Linked service | Connector | Purpose |
|---|---|---|
| `ls_http_jolpica` | HTTP | API ingestion |
| `ls_adls_gen2_f1` | Azure Data Lake Storage Gen2 | Bronze storage |
| `ls_adls_f1` | Azure Blob Storage | Initial connectivity testing; unused by ingestion |