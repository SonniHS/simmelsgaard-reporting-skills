# Platform cheat sheet: Fabric Warehouse, Lakehouse, SQL database in Fabric, Azure SQL, SQL Server

Status: October 2026. Preview features change monthly: check Microsoft Learn before relying
on one. Pages worth bookmarking:

- Fabric Warehouse T-SQL surface area: https://learn.microsoft.com/fabric/data-warehouse/tsql-surface-area
- Fabric Warehouse data types: https://learn.microsoft.com/fabric/data-warehouse/data-types
- IDENTITY in Fabric Warehouse: https://learn.microsoft.com/fabric/data-warehouse/identity
- Warehouse performance guidelines: https://learn.microsoft.com/fabric/data-warehouse/guidelines-warehouse-performance
- V-Order: https://learn.microsoft.com/fabric/data-engineering/delta-optimization-and-v-order
- Direct Lake storage and guardrails: https://learn.microsoft.com/fabric/fundamentals/direct-lake-understand-storage
- Mirroring overview: https://learn.microsoft.com/fabric/mirroring/overview
- SQL database in Fabric mirroring limits: https://learn.microsoft.com/fabric/database/sql/mirroring-limitations

## Contents
1. T-SQL surface differences
2. Data types
3. Performance tools
4. Connectivity from Power BI / Fabric
5. Getting data into OneLake (mirroring)
6. What Direct Lake needs from gold tables
7. Choosing the gold platform

## 1. T-SQL surface

| Capability | Fabric Warehouse | Lakehouse SQL endpoint | SQL database in Fabric | Azure SQL DB / MI | SQL Server 2019–2025 |
|---|---|---|---|---|---|
| DML (INSERT/UPDATE/DELETE/MERGE) | Yes (MERGE GA) | **No, read-only** (write via Spark) | Yes | Yes | Yes |
| Views | Yes (Direct Lake: unsupported on OneLake / DQ fallback on SQL) | Yes | Yes | Yes | Yes |
| Recursive CTE | **No** | **No** | Yes | Yes | Yes |
| `GENERATE_SERIES` | verify | verify | Yes | Yes | 2022+ |
| Temp tables | `#temp` | — | Yes | Yes | Yes |
| IDENTITY | `bigint` only; not contiguous | — | Yes | Yes | Yes |
| Indexes / CCI | No (automatic) | No | Yes (CCI tables are **not mirrored**) | Yes | Yes |
| Table partitioning | No | Delta partitions (Spark) | Yes | Yes | Yes |
| Constraints | PK/UNIQUE/FK only `NONCLUSTERED … NOT ENFORCED` | — | Enforced | Enforced | Enforced |
| `ALTER TABLE … ALTER COLUMN` | preview | — | Yes | Yes | Yes |
| Materialized / indexed views | No | Materialized lake views (Spark) | Indexed views | Indexed views | Indexed views |
| Temporal tables | No | — | Yes | Yes | Yes |
| Cross-database query | Same workspace (3-part names) | Same workspace | Limited | Elastic query (DB) / yes (MI) | Linked servers |
| Row-level security | Yes (forces DQ fallback for Direct Lake on SQL) | Yes (same) | Yes (not mirrored) | Yes | Yes |

## 2. Data types

| Use | Portable choice | Notes |
|---|---|---|
| Text | `varchar(n)` | Fabric WH/endpoint: no `nvarchar`; UTF-8 collation stores Unicode in `varchar`. SQL Server: `varchar` with a non-UTF-8 collation can't hold Δ or non-Latin names → use `nvarchar` there, or a `_UTF8` collation (2019+) |
| Dates | `date` | Not `datetime2` at midnight; relationship keys must match types |
| Timestamps | `datetime2(6)` | Fabric max precision 6; mirroring truncates 7 → 6; a `datetime2(7)` PK blocks mirroring |
| Money | `decimal(19,4)` | No `money` in Fabric WH; precision > 18 isn't pushed down by data clustering |
| Rates | `decimal(19,8)` | |
| Keys | `int` / `bigint` | No GUIDs to Direct Lake: map `uniqueidentifier` to an int surrogate |
| Flags | `bit` | → boolean in the model |
| Small ints | `smallint` | No `tinyint` in Fabric WH |
| Hashes | `varchar(64)` hex | `varbinary` not loadable by Direct Lake |

## 3. Performance tools

| Platform | Use |
|---|---|
| SQL Server / Azure SQL | CCI on facts, partition by fiscal year with `SWITCH`, rowstore PK on dimensions, unique NC index on business keys, `UPDATE STATISTICS` after loads, Query Store |
| SQL database in Fabric | As Azure SQL, but CCI tables don't mirror: rowstore if Direct Lake reads the mirror; capacity CU shared with everything else |
| Fabric Warehouse | Batch DML only (CTAS, `INSERT…SELECT`, `COPY INTO`); data clustering (preview) on `PeriodDate`; single-column statistics; separate staging warehouse (V-Order may be disabled there, irreversibly) and gold warehouse (V-Order on); Query Insights for slow queries |
| Lakehouse | `readHeavyForPBI` resource profile or `delta.parquet.vorder.enabled` on gold, `OPTIMIZE`, `VACUUM`, low-cardinality partitioning, `replaceWhere` |

## 4. Connectivity

| Source | Power BI Import / DQ | Fabric pipelines / Copy job / Dataflow Gen2 | Notes |
|---|---|---|---|
| SQL Server on-prem / VM | On-premises data gateway (standard mode, cluster for HA) | Same gateway | Kerberos constrained delegation for DQ SSO. Make every Power Query step fold (that's why the `rpt` views exist) |
| Azure SQL public endpoint | Direct (firewall: Azure services / IP ranges) | Direct | Security teams rarely accept |
| Azure SQL private endpoint | **VNet data gateway** (managed, injected in a delegated subnet; billed as capacity) | VNet gateway; Spark via **managed private endpoints** | |
| Fabric Warehouse / Lakehouse / SQL DB in Fabric | Native (no gateway) | Native | Inbound protection via tenant/workspace Private Link |
| SQL endpoint for Import | `Sql.Database("<your-warehouse-endpoint>", "<database>")` | — | Same connector as SQL Server; copy the endpoint from the item's settings |

Gateway sizing: refresh is CPU/memory heavy on the gateway when queries don't fold. Monthly
aggregates in SQL keep refreshes small.

## 5. Mirroring into OneLake

| Source | Status (Oct 2026, verify) | Prerequisites / limits |
|---|---|---|
| Azure SQL DB | GA | Managed identity on the server; tables without PK allowed; CCI, json/vector columns block a table |
| Azure SQL MI | GA | PK not required in recent versions (restart replication to pick up older PK-less tables); table-count limit; update policy matters |
| SQL Server 2016–2022 | check the Learn banner | CDC: SQL Agent, PK per table, gateway; DDL breaks mirroring |
| SQL Server 2025 | GA | Change feed, Azure Arc + managed identity, on-prem only |
| SQL database in Fabric | automatic | CCI tables, computed columns, xml/hierarchyid not mirrored; DDL → reseed |
| Open mirroring | GA | Write Parquet + `_metadata.json` (key columns, `__rowMarker__`) to the landing zone |

Mirror caveats: source RLS/OLS/DDM not propagated; paused capacity stops replication;
short default retention for new mirrors; layout not tuned for Direct Lake. **A mirror is
bronze/silver input, not the reporting model**: build V-Ordered gold tables on top.

## 6. What Direct Lake needs from gold tables

1. Delta **tables**, not views (OneLake). Materialise logic (CTAS, notebooks, MLVs).
2. Supported types only (no GUID/binary/complex, long strings truncated, no NaN).
3. Unique one-side keys; equal types on both sides of each relationship.
4. V-Order on (Warehouse default; Spark: `readHeavyForPBI` or table property).
5. Few, large row groups (1–16 M rows); stay well under the SKU's file/row-group guardrails.
   Over a guardrail **refresh fails** on Direct Lake on OneLake.
6. Low-cardinality partitions only (fiscal year / month).
7. Append-friendly, batched loads (incremental framing keeps dictionaries).
8. Stable schema; Delta column mapping if renames are likely.
9. Frame after load (automatic updates off) so users never see half-loaded periods.
10. No voucher numbers/descriptions in the monthly fact (cardinality); detail fact for drill.

## 7. Choosing the gold platform

| Team / situation | Gold on | Model mode |
|---|---|---|
| T-SQL team, Fabric capacity | Fabric Warehouse (MERGE, IDENTITY) | Direct Lake on OneLake |
| Spark team, large ERP volumes | Lakehouse (notebooks / MLVs) | Direct Lake on OneLake |
| Existing Azure SQL DWH, no Fabric yet | Azure SQL (`rpt` views) | Import (incremental) |
| On-prem SQL Server DWH, data must stay | SQL Server (`rpt` views) | Import via gateway; mirror later |
| Planning write-back | SQL database in Fabric (`plan` schema) | via mirror into gold, then Direct Lake/Import |
