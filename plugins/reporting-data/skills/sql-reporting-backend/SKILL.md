---
name: sql-reporting-backend
description: >
  Builds the SQL gold layer that Power BI / Fabric semantic models read for IBCS finance
  reporting, on Fabric Warehouse, Lakehouse SQL endpoint, SQL database in Fabric, Azure SQL or SQL
  Server; use it whenever someone writes T-SQL or Spark SQL for a reporting star schema, budget or
  forecast tables, FX conversion, hierarchy flattening, or asks which SQL platform or storage mode
  to feed a semantic model from, including portability between Fabric and SQL Server. Covers
  dimensional tables/views as the model contract, date and fiscal-calendar dimension, scenario
  dimension with budget/forecast versions and phasing, SCD2, currency conversion
  (average/closing/budget rates), chart-of-accounts flattening and report-line bridges, monthly
  facts from the GL, partitioning/columnstore, Direct Lake Delta requirements, gateway and
  mirroring connectivity, and load reconciliation checks.
---

# SQL reporting back end (gold layer for IBCS models)

The gold layer exists so the semantic model can stay simple: every derived attribute,
conversion and mapping is computed once in SQL, and the model only sums and compares. This
skill covers *what* gold must contain and the T-SQL to build it. For operating the platforms:

| Need | Where |
|---|---|
| Run T-SQL, COPY INTO, query diagnostics on Fabric Warehouse / SQL endpoint / mirrors | Microsoft's Fabric skills (`fabric-skills@fabric-collection`, https://github.com/microsoft/skills-for-fabric) or the Fabric CLI, `sqlcmd` |
| Bronze/silver/gold layout, notebooks vs materialized lake views | Microsoft Learn (Fabric medallion architecture), Microsoft's Fabric skills |
| Semantic model on top | [semantic-model-ibcs](../semantic-model-ibcs/SKILL.md) |
| ERP extraction and decoding (F&O, BC, Dataverse) | [dynamics-erp-reporting](../dynamics-erp-reporting/SKILL.md) |

Working example in [assets/sql/](assets/sql/01_schema.sql): portable DDL for the core star
(`01_schema.sql`), a set-based date dimension (`02_dim_date.sql`), platform-specific key and
index scripts (`04_optional_*.sql`) and load checks (`05_checks.sql`). Seed data is yours to
add (step 03).

## Settings to agree first

- **Group currency** (`EUR` in the examples; every script takes it as a variable or a
  `ToCurrency` filter you set once).
- **Fiscal year start month** and calendar type (Gregorian, shifted, 4-4-5, 13 periods).
- **Text collation / Unicode** on SQL Server (`nvarchar` or a `_UTF8` collation if names hold
  non-Latin characters).

## The contract

```
bronze  raw extracts, mirrors, Link to Fabric shortcuts   never modelled
silver  typed, de-duplicated, decoded, conformed keys
gold    Dim*, Fact*, Bridge*, Sec*                         the star
rpt     contract objects the model binds to                stable names, types, grain
```

| Model storage mode | Contract object |
|---|---|
| Import / DirectQuery (Azure SQL, SQL Server, SQL endpoint) | `rpt` **views** (thin: casts, renames) |
| Direct Lake on OneLake | gold **Delta tables** named as the contract (views unsupported) |
| Direct Lake on SQL endpoint | tables (views fall back to DirectQuery) |

Contract rules, each preventing a specific model failure:

1. **Integer surrogate keys** (`int`/`bigint`); no GUIDs (Direct Lake can't load them), no
   ERP `RecId`s as keys.
2. **Unique one-side keys** and a `-1 Unknown` / `-2 Not applicable` member in every
   dimension; facts never carry NULL keys (duplicate keys make Direct Lake queries fail).
3. **Explicit types**: `date` for dates, `decimal(19,4)` money, `varchar` text on Fabric.
4. **Month grain** for the IBCS fact (`PeriodDate` = first of month), all scenarios in one
   fact with `ScenarioKey`; line-level detail in a separate fact for drill.
5. **P&L sign** amounts stored (revenue +, cost −) plus `PLSign` on the account; on report
   lines `DisplaySign` (−1 for cost lines shown positive) and `VarianceDirection` (+1/−1/0,
   relative to the displayed value; costs −1). The model compares displayed values.
6. **Date dimension** with `FiscalYearNo`, `FiscalPeriod`, `FiscalPeriodSeq` (running) and
   `IsClosedPeriod` from the ERP.
7. **PY is not stored**; FC versions are immutable rows in `DimScenario`; plan in months.
8. **Currency converted in SQL** (average for P&L, closing for BS, budget rate per plan
   version); group and local currency columns.
9. **Business keys include the company** (`Company`/`DataAreaId`, code) everywhere.
10. **Checks pass before the model refreshes/frames** (see below).

## Workflow

1. **Decide platform and storage mode together**
   ([platform-cheatsheet.md](references/platform-cheatsheet.md) §7 and the semantic-model
   design decisions). Direct Lake → tables; Import → views.
2. **Write the DDL portable first** (`[portable]` scripts in
   [tsql-scripts.md](references/tsql-scripts.md)): varchar, date, decimal, no recursive CTE,
   explicit keys. Put platform-only pieces (PK/CCI on SQL Server, `NOT ENFORCED` keys on
   Fabric WH, V-Order/OPTIMIZE on Spark) in separate, labelled files, like
   `assets/sql/04_optional_*.sql`.
3. **Dimensions**: date (with ERP period status), scenario, entity, account (+ flattened
   hierarchy), report line + bridge, cost centre (SCD2 where organisation changes matter),
   security mapping.
4. **Facts**: monthly AC from GL detail (one batch per fiscal year or open period), BU/FC/PL
   from the planning store (approved versions only, phased to months, plan rates), n+m
   forecasts with copied AC months.
5. **Checks**: run the reconciliation and integrity queries; fail the pipeline on any row
   (`05_checks.sql` queries 1–6; query 7 only prints reference totals to compare by hand).
6. **Hand-off**: frame/refresh the model only after checks pass (Direct Lake auto-update off).

## Platform differences that change the SQL

| Topic | Fabric Warehouse | SQL Server / Azure SQL | Lakehouse |
|---|---|---|---|
| Hierarchies | fixed-depth self-joins (no recursive CTE) | recursive CTE fine | iterative joins in PySpark |
| Keys | explicit / `bigint IDENTITY` (not contiguous) | `INT IDENTITY` / `SEQUENCE` | `row_number` or hash |
| Unicode | `varchar` (UTF-8) | `nvarchar` or `_UTF8` collation | string |
| Reload a period | `DELETE … WHERE FY` + `INSERT … SELECT`, or CTAS + rename | partition `SWITCH` / `TRUNCATE … WITH (PARTITIONS)` | `replaceWhere` |
| Physical design | none (V-Order, auto stats, clustering preview) | CCI + partitioning | V-Order, `OPTIMIZE`, few files |
| Constraints | `NOT ENFORCED` only | enforced | none |

Full table: [platform-cheatsheet.md](references/platform-cheatsheet.md).

## Checks to run after every load

From [05_checks.sql](assets/sql/05_checks.sql) and [tsql-scripts.md](references/tsql-scripts.md)
§11: unique one-side keys; no orphan fact keys; month grain; fact grain unique; close flag not
stale (AC in the open period is fine during close days); bridge covers every detail/subtotal line; Σ month fact = Σ GL detail per
entity/month; phasing weights sum to 1; every FX rate needed exists (a missing rate in an
INNER JOIN silently drops rows); Σ budget = ERP budget register total.

## Gotchas

- T-SQL nests block comments: `/*` inside a comment (e.g. a path like `csv/*.csv`) breaks the
  script.
- Year-end closing/opening entries (F&O Closing/Opening periods, BC closing dates) must be
  excluded from monthly P&L, or December shows the result reversed.
- Trickle DML on Fabric WH/Delta creates many small files and breaks Direct Lake guardrails.
- A CCI on SQL database in Fabric stops that table from mirroring.
- SQL-side RLS is not inherited by Import or Direct Lake models; secure in the model.
- `HASHBYTES` returns varbinary: convert to hex `varchar` before it reaches Direct Lake.
- Not executed on a live engine by the author: `STRING_SPLIT`/`CROSS APPLY`,
  `CREATE OR ALTER VIEW`, `EXEC ('CREATE SCHEMA …')` and multi-row `INSERT … VALUES` on
  Fabric Warehouse are believed supported per the 2026 T-SQL surface area
  (https://learn.microsoft.com/fabric/data-warehouse/tsql-surface-area). The bundled scripts
  parse as T-SQL; verify on your platform.

## References

- [references/tsql-scripts.md](references/tsql-scripts.md) — scripts with platform tags:
  schemas/unknown members, date (incl. 4-4-5), scenarios/plan input/phasing/n+m forecasts,
  SCD2, FX, hierarchy flattening, range totals → bridge, monthly fact loads,
  partitioning/CCI/Spark, contract views vs tables, reconciliation, security mapping.
- [references/platform-cheatsheet.md](references/platform-cheatsheet.md) — T-SQL surface,
  types, performance tools, connectivity (gateways, VNet gateway, private endpoints),
  mirroring, Direct Lake requirements, platform choice.
