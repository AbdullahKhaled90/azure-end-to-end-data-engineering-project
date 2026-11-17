# End-to-End Azure Data Engineering Project

An end-to-end data pipeline on Microsoft Azure that moves data from an **on-premises SQL Server** database to a **Power BI** report, using the **Medallion Architecture** (Bronze → Silver → Gold).

Architecture

---

## Tech Stack

| Layer | Service |
|---|---|
| Source | On-premises SQL Server (AdventureWorksLT2022) |
| Ingestion & orchestration | Azure Data Factory + Self-Hosted Integration Runtime |
| Storage | Azure Data Lake Storage Gen2 (bronze / silver / gold containers) |
| Transformation | Azure Databricks (PySpark, Delta Lake) |
| Serving | Azure Synapse Analytics (Serverless SQL pool) |
| Reporting | Power BI |
| Security | Azure Key Vault, Managed Identities, Azure RBAC |

---

## Pipeline Overview

### 1. Ingestion — Metadata-driven pipeline (Data Factory)
- A **Lookup** activity queries `sys.tables` and `sys.schemas` to get every table in the `SalesLT` schema.
- A **ForEach** activity loops over the result and runs a **Copy** activity for each table **in parallel**.
- Datasets are **parameterized** (`SchemaName`, `TableName`), so new tables are picked up automatically with no pipeline changes.
- Data lands in the **bronze** container as Parquet: `bronze/SalesLT/<Table>/<Table>.parquet`
- The SQL Server password is stored in **Azure Key Vault**, never in the pipeline.

### 2. Bronze → Silver (Databricks)
- Reads every table from bronze.
- Detects all date columns and standardizes them to `yyyy-MM-dd`.
- Writes the result as **Delta** tables to the silver container.

### 3. Silver → Gold (Databricks)
- Renames all columns from `PascalCase` to `snake_case` (e.g. `SalesOrderID` → `sales_order_id`).
- Writes **Delta** tables to the gold container.

Both notebooks run as activities in the same Data Factory pipeline:

```
Lookup → ForEach (Copy) → BronzeToSilver → SilverToGold
```

### 4. Serving layer (Synapse Serverless SQL)
- A stored procedure (`CreateSQLServerlessView_gold`) creates a **view** over each Delta table using `OPENROWSET(... FORMAT = 'DELTA')`.
- A Synapse pipeline (**Get Metadata → ForEach → Stored Procedure**) creates views for all gold tables automatically.

### 5. Reporting (Power BI)
- Power BI connects to the Synapse serverless endpoint and reads the `gold_db` views.

---

## Challenges & How I Solved Them

| Challenge | Solution |
|---|---|
| Self-Hosted IR could not reach `SQLEXPRESS` (error 26) | Enabled TCP/IP, started the SQL Server Browser service, and enabled SQL Server authentication |
| Parquet writes failed on the Self-Hosted IR | Installed a 64-bit Java runtime (OpenJDK 17) and set `JAVA_HOME` |
| All tables wrote to one file (`LeaseIdMissing`) | Replaced literal text with dynamic content and dataset parameters (`@item().TableName`) |
| **DBFS mounts are disabled** on new Databricks workspaces | Dropped `dbutils.fs.mount` and read/wrote directly with `abfss://` paths |
| Subscription vCPU quota limits | Sized the cluster as a single node with Photon off (≈1 DBU/h) |
| Synapse could not read the Delta files when queried with SQL authentication | Created a server-scoped credential with `IDENTITY = 'Managed Identity'` and gave the Synapse identity **Storage Blob Data Reader** |

---

## Repository Structure

```
├── adf/                  # Data Factory pipelines, datasets, linked services (JSON, Git integration)
├── synapse/              # Synapse pipelines and SQL scripts
├── databricks/
│   ├── bronze_to_silver.py
│   └── silver_to_gold.py
├── sql/
│   ├── 01_create_login_and_user.sql
│   └── 02_create_serverless_view_proc.sql
├── powerbi/
│   └── report.pbix
├── architecture/
│   └── architecture.png
└── README.md
```

---

## Possible Improvements
- Store dates as real `date` types instead of strings in the silver layer
- Incremental loading (watermark column) instead of full overwrite
- Scheduled trigger for daily runs, with failure alerts
- Move from direct `abfss://` access to Unity Catalog external locations
- Data quality checks between layers

---

## Acknowledgement
Built by following <!-- add tutorial name and link -->, adapted for the current Azure platform (2026), where several steps in the original no longer work as shown.
