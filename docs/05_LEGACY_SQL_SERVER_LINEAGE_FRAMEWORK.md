## Executive Summary
This document provides a step by step strategy to manage ambigous legacy sql server lineage tracking 

### Step 1: Define the lineage goal
Ask (and document):
 - Table-level lineage? Column-level?
 - Operational lineage only (SQL Server → SQL Server)?

Include if applicable:
 - Stored procedures
 - SSIS
 - SQL Agent jobs
 - Views
 - Ad-hoc reporting tables

### Step 2: Inventory all SQL Server Assets 
Run against each database: 
``` SQL: Database Inventory by create date
SELECT name, create_date
FROM sys.databases
WHERE state_desc = 'ONLINE';
```
```SQL: Object Counts by Type
SELECT type_desc, COUNT(*)
FROM sys.objects
GROUP BY type_desc
ORDER BY COUNT(*) DESC;
```
```SQL: Schemas can reveal relationships 
SELECT schema_id, name
FROM sys.schemas;
```
#### OUTPUT = master repository 
 - Server
 - Database
 - Schema
 - Object name
 - Object type
 - Create date
 - Last modified

### Step 3: Identify “source” tables
Tables with:
- No foreign keys referencing them
- High insert/update frequency
- Names like stg_, raw_, import_, src_

```SQL: source table investigation
SELECT t.name
FROM sys.tables t
LEFT JOIN sys.foreign_keys fk
  ON fk.referenced_object_id = t.object_id
WHERE fk.object_id IS NULL;
```
### Step 4: Identify downstream / derived tables
Look for:
- Tables populated via INSERT…SELECT
- Truncate + insert patterns
- ETL-like naming (fact_, dim_, agg_)

```SQL: Search for population logic - provides list of sources, transformations, presenation tbls
SELECT OBJECT_NAME(object_id), definition
FROM sys.sql_modules
WHERE definition LIKE '%INSERT%'
   OR definition LIKE '%MERGE%'
   OR definition LIKE '%SELECT%INTO%';
```
### Step 5: Capture view dependencies
```SQL: provides direct liniage edges table -> view & view -> view
SELECT 
  OBJECT_SCHEMA_NAME(v.object_id) AS view_schema,
  v.name AS view_name,
  OBJECT_SCHEMA_NAME(d.referenced_id) AS referenced_schema,
  OBJECT_NAME(d.referenced_id) AS referenced_object
FROM sys.views v
JOIN sys.sql_expression_dependencies d
  ON v.object_id = d.referencing_id;
```
### Step 6: Analyze stored procedures & functions
```SQL: Extract read/write behavior: 1 = target 0 = source
SELECT 
  o.name AS object_name,
  o.type_desc,
  d.referenced_entity_name,
  d.is_updated
FROM sys.objects o
JOIN sys.sql_expression_dependencies d
  ON o.object_id = d.referencing_id
WHERE o.type IN ('P','FN','IF','TF');
```
### Step 7: Handle dynamic SQL (more difficult)
``` SQL: Search Patterns - manual inspection, regex table name extraction, flag as inferred
SELECT OBJECT_NAME(object_id), definition
FROM sys.sql_modules
WHERE definition LIKE '%EXEC(%'
   OR definition LIKE '%sp_executesql%';
```
### Step 8: Column-Level Lineage 
```SQL: Extract column mappings from views
SELECT 
  v.name AS view_name,
  vc.name AS view_column,
  t.name AS source_table,
  tc.name AS source_column
FROM sys.views v
JOIN sys.columns vc ON v.object_id = vc.object_id
JOIN sys.sql_expression_dependencies d ON v.object_id = d.referencing_id
JOIN sys.tables t ON d.referenced_id = t.object_id
JOIN sys.columns tc ON t.object_id = tc.object_id;
```
### Step 9: Column Linage for Stored Procedures
This is mostly manual or tool-assisted:
 - Parse SELECT lists
 - Track aliases
 - Map expressions
Tip: Start with critical tables only (facts, financials, regulatory data)

### Step 10: Orchestration & Execution Lineage
``` SQL: Agent Jobs defining execution order which is part of lineage - stored proc calls - SSIS References, batch sequences
SELECT 
  j.name AS job_name,
  s.step_id,
  s.command
FROM msdb.dbo.sysjobs j
JOIN msdb.dbo.sysjobsteps s
  ON j.job_id = s.job_id;
```
### Step 11: SSIS Packages (if present)
Look for:
- Source components
- Destination components
- Transformations
- Export packages and scan:
- Connection strings
- Data flow mappings

### Step 12: Reconstruct End-to-End Lineage Graph
Build linage relationships 
| *From Object | *To Object | *Type | *Confidence |
|--------------|------------|-------|-------------|
| raw_sales | staging_sales | INSERT | High |
| fact_sales | rpt_sales | VIEW | High | 

This can become the systems of record lineage table ideally kept in Snowflake as a reference 

### Step 13: Visualize
- If analysis, source systems all captured in Snowflake then you can build PK/FK Relationships on your enterprise roadmamp and get an entity relationship diagram for ease of understanding througout the entire migraiton project 

Other tools: less optimal as these tend to get lost and not updated 
 - Draw.io
 - Viseo
 - Graph DB NeoJ4
 - Excel & PowerBI 

 #### Validation/Risk Analysis 
 Lineage must match reality.
 - Row count comparisons
 - Load timing correlation
 - Data freshness checks

 ``` SQL example 
 SELECT MAX(load_date) FROM fact_sales;
SELECT MAX(load_date) FROM stg_sales;
```

### Step 14: Build into Data Governance Program 
 - Assign Data Owners & Stewards 
 - Assign contracts & SLAs 
 - Create data dictonaries and process of approval for adjustments for accountability 

### Step 15: Automate Linage Capture 
 - Store dependency metadata nightly
 - Track Schema Changes & understand why & upstream/downstream impacts
 - Version linage definitions & sign off 

### Step 16: Implement minimum gates for legacy 
 - No table without a data owner & data steward 
 - No table without source 
 - No table without load mechanism 
 - No deployment without liniage update   

## High Level Architecture 

SQL Server(s)
   ↓
Python Extractors (pyodbc / sqlalchemy)
   ↓
Lineage Engine (rules + parsers)
   ↓
Metadata Store (SQL / Azure SQL)
   ↓
Purview REST APIs
   ↓
Governance UI / Impact Analysis

## *Establish Object Level Lineage: simple yaml config 
```yaml: 
sql_servers:
  - name: PROD-SQL-01
    auth: integrated
    databases:
      - SalesDW
      - FinanceDW

metadata_db:
  connection_string: "Driver={ODBC Driver 17 for SQL Server};..."

purview:
  account_name: mypurview
  collection: SQL-Lineage
```
## Python Extraction Layer 
 - Libraries 
    - pyodbc
    - sqlalchemy
    - pandas
    - sqlparse
    - re
    - requests
    - pyyaml

```python:  extractor returns normalized dataframes
def extract_objects(engine) -> pd.DataFrame:
    return pd.read_sql("SELECT ... FROM sys.objects", engine)

def extract_dependencies(engine) -> pd.DataFrame:
    return pd.read_sql("SELECT ... FROM sys.sql_expression_dependencies", engine)

```
### Dependency Extraction Modules 
*Core extractors
- objects.py
- columns.py
- dependencies.py
- procedures.py
- jobs.py
- dynamic_sql.py

*Each module:
- Executes known-safe SQL
- Tags rows with source_system, extract_time

### Lineage Inference Engine (Rule-Based)
```Python: Rule Examples
if is_updated == 1:
    lineage_type = "WRITE"
else:
    lineage_type = "READ"
#-------------------------------------------------------------------------
#-------------------------------------------------------------------------
if object_type == "VIEW":
    confidence = "High"
elif uses_dynamic_sql:
    confidence = "Medium"
else:
    confidence = "High"
```

### Metadata store layer: 
Python writes directly into:
- md_asset
- md_lineage
- md_column (optional for MVP)
Use UPSERT logic to stay idempotent

``` python
def upsert_asset(df):
    # merge into md_asset

```
### Purview Push (MVP Scope) - other options beyond purview in snowflake

Let Purview scan assets automatically.
You only push:
- Process entities
- Lineage edges

Use Purview REST API:
- Create Process
- Link Inputs/Outputs
Python handles auth via Azure AD (service principal)

### Production Hardening
#### Dynamic SQL Parsing Automation
Python regex + sqlparse:

```python
TABLE_REGEX = r"(from|join|into|update)\s+([\w\.\[\]]+)"
```
- Extract candidate table names
- Cross-check against known assets
- Assign confidence = Medium

#### Column-Level Lineage (Selective)
Only for:
- Views
- Critical fact tables
- Algorithm:
    - Parse SELECT lists
    - Map aliases
- Store only resolved mappings
- Don’t aim for 100%. Aim for material tables only.

#### Execution Order & Temporal Lineage
Python maps:
-SQL Agent job → step → proc → table
This enables:
- “What breaks if this job fails?”
- “What data is stale?”

#### Change Detection
Nightly run compares:
- Object hashes
- Definition hashes

Only recompute lineage for:
- Changed objects
- New dependencies

This keeps runtime low.

### Alignment to Data Governance Best Practices (Perview or other)
|  Feature |  Implementation |
|----------|-----------------|
| Data Onwer/Steward | Assing via metadata |
| Data Dictionary | Link Business Terms |
| Sensitivity | Tag columns |
| Confidence | Custom Attribute|

### Automated Exceptions Workflow 
Python flags:
- Dynamic SQL
- Missing sources
- Circular dependencies

Writes to:
- Jira/ADO/et al 
- ServiceNow
- Teams webhook

Humans only see exceptions, established SLAs and SOPs define time boxed outcomes and outreach 

### Operation Model Considerations 
*Daily*
- Automated Extraction
- Delta Lineage updates
- Sync with DG/Purview - automated in Snowflake 

*Weekly*
 - Exception Review
 - Confidence updates if needed 

*Monthly*
- Coverage Metrics 
    - % assets with lineage
    - % assets with high confidence 

    
