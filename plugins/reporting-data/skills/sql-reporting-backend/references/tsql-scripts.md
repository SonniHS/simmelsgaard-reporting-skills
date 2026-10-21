# T-SQL scripts for the gold layer

Every script carries a platform tag:

- **[portable]** SQL Server 2016+, Azure SQL DB/MI, SQL database in Fabric, Fabric Warehouse.
- **[SQL Server family]** SQL Server, Azure SQL, SQL database in Fabric (not Fabric Warehouse).
- **[Fabric WH]** Fabric Warehouse only.
- **[Spark]** Lakehouse notebooks (Spark SQL / PySpark).

Portable means: `varchar` (Fabric Warehouse has no `nvarchar`), `date`/`datetime2(6)`,
`decimal`, `int`/`bigint`, `bit`; no recursive CTEs, no `GENERATE_SERIES`, no `FORMAT`, no
indexes, no `IDENTITY` (Fabric WH supports `bigint IDENTITY`, but explicit keys keep loads
idempotent), batches not row by row. Beware `/*` inside block comments (T-SQL nests block
comments, so a path like `csv/*.csv` in a comment swallows the rest of the file).

The core star is in [../assets/sql/](../assets/sql/01_schema.sql) (`01_schema.sql`,
`02_dim_date.sql`, `04_optional_*.sql`, `05_checks.sql`). These scripts extend it. The group
currency is `EUR` in the examples: replace it (or bind `@GroupCurrency`) everywhere you see
`ToCurrency = 'EUR'`.

## Contents
1. Schemas and unknown members
2. Date dimension (Gregorian/shifted; 4-4-5 variant)
3. Scenario dimension, plan input, versions, phasing, n+m forecasts
4. SCD type 2 (load and fact lookup)
5. Currency rates and conversion
6. Hierarchy flattening (portable fixed depth; recursive CTE)
7. Range totals (BC Totaling, F&O row definitions) → report-line bridge
8. Monthly fact from GL detail; period reloads
9. Partitioning, columnstore, statistics
10. Contract objects: rpt views (Import) vs tables (Direct Lake)
11. Reconciliation and load checks
12. Security mapping

---

## 1. Schemas and unknown members [portable]

```sql
IF SCHEMA_ID('silver') IS NULL EXEC ('CREATE SCHEMA silver');
IF SCHEMA_ID('gold')   IS NULL EXEC ('CREATE SCHEMA gold');
IF SCHEMA_ID('rpt')    IS NULL EXEC ('CREATE SCHEMA rpt');    -- contract views (Import/DQ)
IF SCHEMA_ID('plan')   IS NULL EXEC ('CREATE SCHEMA plan');   -- planning input (OLTP side)

-- Every dimension gets -1 Unknown and -2 Not applicable; facts never carry NULL keys.
INSERT INTO gold.DimCostCenter (CostCenterKey, Company, CostCenterCode, CostCenterName,
                                ValidFrom, ValidTo, IsCurrent, IsInferred)
SELECT k, 'N/A', code, name, CAST('1900-01-01' AS date), CAST('9999-12-31' AS date), 1, 0
FROM (VALUES (-1, 'N/A', 'Unknown'), (-2, 'N/A-PLAN', 'Not applicable')) AS u(k, code, name)
WHERE NOT EXISTS (SELECT 1 FROM gold.DimCostCenter d WHERE d.CostCenterKey = u.k);
```

## 2. Date dimension

Gregorian and shifted fiscal years: [02_dim_date.sql](../assets/sql/02_dim_date.sql)
[portable] (`@FyStartMonth = 7` for July–June, FY named after the year it ends in). Add per
load:

```sql
-- [portable] period status from the ERP (F&O LedgerFiscalCalendarPeriod, BC Accounting Period)
UPDATE d
SET    d.IsClosedPeriod = CASE WHEN p.IsClosed = 1 THEN 1 ELSE 0 END
FROM   gold.DimDate d
JOIN   silver.erp_period_status p
  ON   d.[Date] BETWEEN p.PeriodStart AND p.PeriodEnd;
```

Keep relative flags (`IsCurrentFY`, `RelativeFiscalYear`) out of the table if the model is
Direct Lake and framed only nightly; compute "current" in DAX from `IsClosedPeriod` instead.
Month names: the script writes English abbreviations; for another language add columns from a
small translation table rather than relying on `DATENAME` (language-dependent per session).

**4-4-5 calendar** [portable]: generate fiscal weeks from the first day of each fiscal year,
then map week numbers to periods with a pattern table.

```sql
-- silver.fiscal_year_start(FiscalYearNo, StartDate, Weeks)   e.g. (2026, '2025-12-28', 52), 53 in long years
-- period pattern 4-4-5: weeks 1-4 -> P1, 5-8 -> P2, 9-13 -> P3, ...
INSERT INTO gold.DimDate445 ([Date], FiscalYearNo, FiscalWeek, FiscalPeriod, FiscalPeriodSeq)
SELECT  DATEADD(day, n.i, y.StartDate)                               AS [Date],
        y.FiscalYearNo,
        n.i / 7 + 1                                                   AS FiscalWeek,
        p.FiscalPeriod,
        y.FiscalYearNo * 12 + p.FiscalPeriod                         AS FiscalPeriodSeq
FROM    silver.fiscal_year_start y
CROSS JOIN (SELECT a.v + 10 * b.v + 100 * c.v AS i
            FROM (VALUES (0),(1),(2),(3),(4),(5),(6),(7),(8),(9)) a(v)
            CROSS JOIN (VALUES (0),(1),(2),(3),(4),(5),(6),(7),(8),(9)) b(v)
            CROSS JOIN (VALUES (0),(1),(2),(3)) c(v)) n            -- 0..399 days
JOIN    (VALUES (1,1,4),(2,5,8),(3,9,13),(4,14,17),(5,18,21),(6,22,26),
                (7,27,30),(8,31,34),(9,35,39),(10,40,43),(11,44,47),(12,48,53)) p(FiscalPeriod, WeekFrom, WeekTo)
  ON    n.i / 7 + 1 BETWEEN p.WeekFrom AND p.WeekTo
WHERE   n.i < y.Weeks * 7;
```

## 3. Scenarios, plan input, versions

```sql
-- [portable] scenario dimension: one row per version (also in 01_schema.sql)
CREATE TABLE gold.DimScenario (
    ScenarioKey int NOT NULL, ScenarioType varchar(2) NOT NULL, ScenarioCode varchar(2) NOT NULL,
    VersionCode varchar(12) NOT NULL, VersionLabel varchar(40) NOT NULL,
    IsCurrent bit NOT NULL, IsLatestFC bit NOT NULL, FcActualMonths int NULL,
    SortOrder int NOT NULL, IbcsNotation varchar(10) NOT NULL);

-- [SQL Server family; also SQL database in Fabric] planning input written by apps / translytical task flows
CREATE TABLE plan.PlanEntry (
    VersionCode      varchar(12)   NOT NULL,
    EntityCode       varchar(10)   NOT NULL,
    AccountNo        varchar(20)   NOT NULL,
    CostCenterCode   varchar(20)   NOT NULL,
    FiscalYearNo     int           NOT NULL,
    FiscalPeriod     int           NULL,        -- NULL = annual value, phase it
    AmountLC         decimal(19,4) NOT NULL,
    CurrencyCode     varchar(3)    NOT NULL,
    PhasingProfile   varchar(20)   NULL,
    Status           varchar(10)   NOT NULL,    -- Draft | Submitted | Approved
    EnteredBy        varchar(100)  NOT NULL,
    EnteredAt        datetime2(6)  NOT NULL);

CREATE TABLE plan.Phasing (ProfileCode varchar(20) NOT NULL, FiscalPeriod int NOT NULL, Weight decimal(9,6) NOT NULL);
-- Σ Weight per profile must be 1 (check below)
```

Load approved plan rows to the monthly fact [portable]:

```sql
DECLARE @Version varchar(12) = 'BU2026';
DECLARE @GroupCurrency varchar(3) = 'EUR';

DELETE f FROM gold.FactFinance f
JOIN gold.DimScenario s ON s.ScenarioKey = f.ScenarioKey
WHERE s.VersionCode = @Version;                     -- versions are reloaded whole

INSERT INTO gold.FactFinance (ScenarioKey, PeriodDate, DateKey, AccountKey, EntityKey,
                              CurrencyCode, AmountLC, AmountGC)
SELECT  s.ScenarioKey,
        d.MonthStart,
        YEAR(d.MonthStart) * 10000 + MONTH(d.MonthStart) * 100 + 1,
        COALESCE(a.AccountKey, -1),
        COALESCE(e.EntityKey, -1),
        p.CurrencyCode,
        SUM(p.AmountLC * COALESCE(ph.Weight, 1)) * COALESCE(a.PLSign, -1),   -- entry in GL sign -> P&L sign
        SUM(p.AmountLC * COALESCE(ph.Weight, 1) * r.Rate) * COALESCE(a.PLSign, -1)
FROM    plan.PlanEntry p
JOIN    gold.DimScenario s ON s.VersionCode = p.VersionCode
LEFT JOIN plan.Phasing ph  ON ph.ProfileCode = p.PhasingProfile AND p.FiscalPeriod IS NULL
JOIN    (SELECT DISTINCT FiscalYearNo, FiscalPeriod, MonthStart FROM gold.DimDate) d
  ON    d.FiscalYearNo = p.FiscalYearNo
 AND    d.FiscalPeriod = COALESCE(p.FiscalPeriod, ph.FiscalPeriod)
LEFT JOIN gold.DimEntity  e ON e.EntityCode = p.EntityCode
LEFT JOIN gold.DimAccount a ON a.AccountNo = p.AccountNo
                         -- several charts of accounts (AccountNo unique per chart only): add
                         -- AND a.ChartOfAccounts = e.ChartOfAccounts, as the GL load does (fno.md §7)
JOIN    gold.FxRate r ON r.FromCurrency = p.CurrencyCode AND r.ToCurrency = @GroupCurrency
                     AND r.RateType = 'BUDGET' AND r.VersionCode = p.VersionCode
                     AND r.MonthStart = d.MonthStart
WHERE   p.VersionCode = @Version AND p.Status = 'Approved'
GROUP BY s.ScenarioKey, d.MonthStart, a.AccountKey, e.EntityKey, p.CurrencyCode, a.PLSign;
```

Rules: versions are **immutable** after the cycle closes (new cycle = new `VersionCode`);
store months, never years; plan at a coarser grain maps to the `-2 Not applicable` member.
The join on `gold.DimDate` assumes one `MonthStart` per fiscal period (Gregorian or shifted
years). Under 4-4-5 a period spans parts of two months, so if `DimDate.FiscalPeriod` holds 4-4-5
periods the `DISTINCT` returns two rows per period and doubles the plan: phase the plan to months
(e.g. split each period by day count) before this load, or key the plan fact on the 4-4-5 period.
The FX table needs a row `FromCurrency = ToCurrency = @GroupCurrency, Rate = 1` so entities in
the group currency are not dropped by the inner join.

"n+m" forecast: copy closed AC months into the FC version when the version is created
[portable]. Order: load the FC version's plan rows first (the plan load above reloads the whole
version), then this copy, which replaces months 1..n:

```sql
DECLARE @Fc varchar(12) = 'FC2026-09', @N int = 9, @Fy int = 2026;
DELETE f FROM gold.FactFinance f
JOIN gold.DimDate d     ON d.[Date] = f.PeriodDate
JOIN gold.DimScenario s ON s.ScenarioKey = f.ScenarioKey
WHERE s.VersionCode = @Fc AND d.FiscalYearNo = @Fy AND d.FiscalPeriod <= @N;   -- no double grain
INSERT INTO gold.FactFinance (ScenarioKey, PeriodDate, DateKey, AccountKey, EntityKey, CurrencyCode, AmountLC, AmountGC)
SELECT  fc.ScenarioKey, f.PeriodDate, f.DateKey, f.AccountKey, f.EntityKey, f.CurrencyCode, f.AmountLC, f.AmountGC
FROM    gold.FactFinance f
JOIN    gold.DimScenario ac ON ac.ScenarioKey = f.ScenarioKey AND ac.ScenarioType = 'AC'
JOIN    gold.DimDate d      ON d.[Date] = f.PeriodDate
CROSS JOIN (SELECT ScenarioKey FROM gold.DimScenario WHERE VersionCode = @Fc) fc
WHERE   d.FiscalYearNo = @Fy AND d.FiscalPeriod <= @N;
UPDATE gold.DimScenario SET IsLatestFC = CASE WHEN VersionCode = @Fc THEN 1 ELSE 0 END WHERE ScenarioType = 'FC';
```

## 4. SCD type 2 [portable]

```sql
-- silver.CostCenter(Company, CostCenterCode, CostCenterName, DepartmentCode, SegmentCode, RowHash)
-- RowHash: CONVERT(varchar(64), HASHBYTES('SHA2_256', CONCAT_WS('|', CostCenterName, DepartmentCode, SegmentCode)), 2)
--   (hex text, not varbinary, so it can also be exposed to Direct Lake if ever needed)
DECLARE @LoadDate date = CAST(GETDATE() AS date);
DECLARE @MaxKey int = (SELECT COALESCE(MAX(CostCenterKey), 0) FROM gold.DimCostCenter);

-- 1) expire changed current rows
UPDATE d
SET    d.ValidTo = DATEADD(day, -1, @LoadDate), d.IsCurrent = 0
FROM   gold.DimCostCenter d
JOIN   silver.CostCenter s ON s.Company = d.Company AND s.CostCenterCode = d.CostCenterCode
WHERE  d.IsCurrent = 1 AND d.RowHash <> s.RowHash;

-- 2) insert new versions and new members (keys from ROW_NUMBER: deterministic, no IDENTITY needed)
INSERT INTO gold.DimCostCenter (CostCenterKey, Company, CostCenterCode, CostCenterName, DepartmentCode,
                                SegmentCode, ValidFrom, ValidTo, IsCurrent, IsInferred, RowHash)
SELECT  @MaxKey + ROW_NUMBER() OVER (ORDER BY s.Company, s.CostCenterCode),
        s.Company, s.CostCenterCode, s.CostCenterName, s.DepartmentCode, s.SegmentCode,
        @LoadDate, CAST('9999-12-31' AS date), 1, 0, s.RowHash
FROM    silver.CostCenter s
LEFT JOIN gold.DimCostCenter d
  ON    d.Company = s.Company AND d.CostCenterCode = s.CostCenterCode AND d.IsCurrent = 1
WHERE   d.CostCenterKey IS NULL;

-- 3) "as-is" columns: current attributes on every historical row
UPDATE h
SET    h.CurrentDepartmentCode = c.DepartmentCode, h.CurrentSegmentCode = c.SegmentCode
FROM   gold.DimCostCenter h
JOIN   gold.DimCostCenter c ON c.Company = h.Company AND c.CostCenterCode = h.CostCenterCode AND c.IsCurrent = 1;
```

Fact lookup ("as-was"): join on business key **and** `PostingDate BETWEEN ValidFrom AND
ValidTo`; unmatched → inferred member (`IsInferred = 1`) or `-1`.

## 5. Currency [portable]

`gold.FxRate` in the bundled `01_schema.sql` has the grain every load below joins on: month ×
rate type × version (`MonthStart`, `FromCurrency`, `ToCurrency`, `RateType` AVERAGE | CLOSING
| BUDGET, `VersionCode` 'AC' for actual rates or the plan version for BUDGET, `Rate` =
ToCurrency per 1 FromCurrency, display factor applied).

```sql
-- Triangulate when the ERP only holds X -> base (here EUR) and the group currency is USD
INSERT INTO gold.FxRate (MonthStart, FromCurrency, ToCurrency, RateType, VersionCode, Rate)
SELECT x.MonthStart, x.FromCurrency, 'USD', x.RateType, x.VersionCode, x.Rate / u.Rate
FROM   gold.FxRate x
JOIN   gold.FxRate u ON u.MonthStart = x.MonthStart AND u.RateType = x.RateType
                    AND u.VersionCode = x.VersionCode AND u.FromCurrency = 'USD' AND u.ToCurrency = 'EUR'
WHERE  x.ToCurrency = 'EUR' AND x.FromCurrency <> 'USD';
```

| Amount | Rate |
|---|---|
| P&L AC | monthly AVERAGE; YTD = Σ converted months |
| BS AC | CLOSING of the period; difference → translation reserve |
| BU / FC / PL | BUDGET rate fixed per version |
| AC at budget rate (FX-neutral ΔBU) | extra column `AmountGC_BudgetRate` |
| PY at current-year rates (constant currency) | extra column `AmountGC_CYRate` |

Monthly average rates: if the ERP stores daily rates, average them in silver per month and
pair; check the ERP's rate *display factor* (per 1/10/100 units) before multiplying.

## 6. Hierarchy flattening

Portable fixed depth (Fabric Warehouse has no recursive CTEs) [portable]:

```sql
-- silver.AccountNode(NodeKey, ParentNodeKey, NodeCode, NodeName)
WITH anc AS (
    SELECT  n0.NodeKey AS LeafKey,
            n0.NodeName AS N0, n1.NodeName AS N1, n2.NodeName AS N2, n3.NodeName AS N3,
            n4.NodeName AS N4, n5.NodeName AS N5,
            CASE WHEN n1.NodeKey IS NULL THEN 1 WHEN n2.NodeKey IS NULL THEN 2
                 WHEN n3.NodeKey IS NULL THEN 3 WHEN n4.NodeKey IS NULL THEN 4
                 WHEN n5.NodeKey IS NULL THEN 5 ELSE 6 END AS Depth
    FROM    silver.AccountNode n0
    LEFT JOIN silver.AccountNode n1 ON n1.NodeKey = n0.ParentNodeKey
    LEFT JOIN silver.AccountNode n2 ON n2.NodeKey = n1.ParentNodeKey
    LEFT JOIN silver.AccountNode n3 ON n3.NodeKey = n2.ParentNodeKey
    LEFT JOIN silver.AccountNode n4 ON n4.NodeKey = n3.ParentNodeKey
    LEFT JOIN silver.AccountNode n5 ON n5.NodeKey = n4.ParentNodeKey
)
SELECT  LeafKey, Depth,
        -- Level k = ancestor (Depth - k) steps above the leaf; ragged levels repeat the leaf
        CASE Depth WHEN 1 THEN N0 WHEN 2 THEN N1 WHEN 3 THEN N2 WHEN 4 THEN N3 WHEN 5 THEN N4 ELSE N5 END AS Level1,
        CASE WHEN Depth < 2 THEN N0 ELSE CASE Depth WHEN 2 THEN N0 WHEN 3 THEN N1 WHEN 4 THEN N2 WHEN 5 THEN N3 ELSE N4 END END AS Level2,
        CASE WHEN Depth < 3 THEN N0 ELSE CASE Depth WHEN 3 THEN N0 WHEN 4 THEN N1 WHEN 5 THEN N2 ELSE N3 END END AS Level3,
        CASE WHEN Depth < 4 THEN N0 ELSE CASE Depth WHEN 4 THEN N0 WHEN 5 THEN N1 ELSE N2 END END AS Level4,
        CASE WHEN Depth < 5 THEN N0 ELSE CASE Depth WHEN 5 THEN N0 ELSE N1 END END AS Level5,
        N0 AS Level6
FROM    anc;
-- Fail the load if any chain is deeper than 6: SELECT ... WHERE n5.ParentNodeKey IS NOT NULL
```

(CTEs themselves are fine in Fabric Warehouse; only *recursive* ones are not.)

Recursive version [SQL Server family]:

```sql
WITH h AS (
    SELECT NodeKey, ParentNodeKey, NodeName, 1 AS Depth, CAST(NodeName AS nvarchar(4000)) AS PathNames
    FROM   silver.AccountNode WHERE ParentNodeKey IS NULL
    UNION ALL
    SELECT c.NodeKey, c.ParentNodeKey, c.NodeName, h.Depth + 1, CAST(h.PathNames + N'|' + c.NodeName AS nvarchar(4000))
    FROM   silver.AccountNode c JOIN h ON c.ParentNodeKey = h.NodeKey
)
SELECT * FROM h OPTION (MAXRECURSION 32);
```

[Spark]: iterate joins in PySpark until no new rows, or use the fixed-depth SQL above.

## 7. Range totals → report-line bridge [portable]

```sql
-- silver.ReportLineRange(ReportLineKey, Totaling)   Totaling like '4000..4999|6000..6999|7110'
INSERT INTO gold.BridgeReportLineAccount (ReportLineKey, AccountKey)
SELECT DISTINCT r.ReportLineKey, a.AccountKey
FROM   silver.ReportLineRange r
CROSS APPLY STRING_SPLIT(r.Totaling, '|') part
CROSS APPLY (SELECT CASE WHEN CHARINDEX('..', part.value) > 0
                         THEN LEFT(part.value, CHARINDEX('..', part.value) - 1) ELSE part.value END AS RangeFrom,
                    CASE WHEN CHARINDEX('..', part.value) > 0
                         THEN SUBSTRING(part.value, CHARINDEX('..', part.value) + 2, 50) ELSE part.value END AS RangeTo) b
JOIN   gold.DimAccount a
  ON   a.AccountNo BETWEEN LTRIM(RTRIM(b.RangeFrom)) AND LTRIM(RTRIM(b.RangeTo))   -- text compare: pad account numbers to equal length
WHERE  a.IsPosting = 1;
```

Verify `STRING_SPLIT` / `CROSS APPLY` on your Fabric Warehouse build (listed in the surface
area; not executed by the author). Subtotals defined by position ("everything above EBIT")
instead of ranges:

```sql
INSERT INTO gold.BridgeReportLineAccount (ReportLineKey, AccountKey)
SELECT st.ReportLineKey, b.AccountKey
FROM   gold.DimReportLine st
JOIN   gold.DimReportLine dl ON dl.LineType = 'Detail' AND dl.SortOrder < st.SortOrder
JOIN   gold.BridgeReportLineAccount b ON b.ReportLineKey = dl.ReportLineKey
WHERE  st.LineType IN ('Subtotal', 'Total');
```

## 8. Monthly fact from GL detail [portable]

```sql
DECLARE @Fy int = 2026;
DECLARE @GroupCurrency varchar(3) = 'EUR';
DELETE f FROM gold.FactFinance f JOIN gold.DimDate d ON d.[Date] = f.PeriodDate
WHERE f.ScenarioKey = 1 AND d.FiscalYearNo = @Fy;

INSERT INTO gold.FactFinance (ScenarioKey, PeriodDate, DateKey, AccountKey, EntityKey, CurrencyCode, AmountLC, AmountGC)
SELECT  1, d.MonthStart, YEAR(d.MonthStart) * 10000 + MONTH(d.MonthStart) * 100 + 1,
        g.AccountKey, g.EntityKey, g.CurrencyCode,
        SUM(g.AmountLC * a.PLSign),
        SUM(g.AmountLC * a.PLSign * r.Rate)
FROM    gold.FactGlDetail g
JOIN    gold.DimDate d    ON d.[Date] = g.PostingDate
JOIN    gold.DimAccount a ON a.AccountKey = g.AccountKey
JOIN    gold.FxRate r     ON r.FromCurrency = g.CurrencyCode AND r.ToCurrency = @GroupCurrency AND r.VersionCode = 'AC'
                         AND r.MonthStart = d.MonthStart
                         AND r.RateType = CASE WHEN a.AccountType = 'BS' THEN 'CLOSING' ELSE 'AVERAGE' END
WHERE   d.FiscalYearNo = @Fy
  AND   g.IsClosingEntry = 0                 -- year-end closing / opening entries excluded from monthly P&L
GROUP BY d.MonthStart, g.AccountKey, g.EntityKey, g.CurrencyCode;
```

- One batch per fiscal year (or per open period during close), never row by row: Fabric
  Warehouse and Delta create files per transaction; trickle DML breaks Direct Lake guardrails.
- Balance-sheet balances are cumulative: build them from opening balance + movements, or
  store month-end balances as a separate fact.
- [Fabric WH] alternative: CTAS a new table and swap with `sp_rename` for a full rebuild.

## 9. Partitioning, columnstore, statistics [SQL Server family]

```sql
CREATE PARTITION FUNCTION pf_FiscalYear (int) AS RANGE RIGHT FOR VALUES (2023, 2024, 2025, 2026, 2027);
CREATE PARTITION SCHEME ps_FiscalYear AS PARTITION pf_FiscalYear ALL TO ([PRIMARY]);
-- FactFinance gets a persisted FiscalYearNo column and a CCI on ps_FiscalYear(FiscalYearNo)
CREATE CLUSTERED COLUMNSTORE INDEX CCI_FactFinance ON gold.FactFinance ON ps_FiscalYear (FiscalYearNo);

-- period reload: load stage table (same structure, same CCI, same partition), then
TRUNCATE TABLE gold.FactFinance WITH (PARTITIONS (5));          -- 2026 partition number
ALTER TABLE stage.FactFinance SWITCH PARTITION 5 TO gold.FactFinance PARTITION 5;
UPDATE STATISTICS gold.FactFinance;
```

- SQL database in Fabric: a table **created with a CCI is not mirrored** to OneLake. Keep
  rowstore there if Direct Lake reads the mirror.
- DirectQuery on SQL Server: add a nonclustered rowstore index on `(ScenarioKey, PeriodDate)`.
- [Fabric WH]: no indexes or partitions; data clustering (`CLUSTER BY`, preview) on
  `PeriodDate`; single-column `CREATE STATISTICS` only.
- [Spark] gold Delta: partition by `FiscalYearNo` only, write with V-Order, `OPTIMIZE` after
  loads, `replaceWhere` for period reloads:

```python
(df.write.format("delta").mode("overwrite")
   .option("replaceWhere", "FiscalYearNo = 2026")
   .saveAsTable("gold.FactFinance"))
spark.sql("OPTIMIZE gold.FactFinance VORDER")
```

## 10. Contract objects

Import/DirectQuery [portable]: thin `rpt` views, explicit casts, business names, no logic the
model needs to re-derive:

```sql
CREATE OR ALTER VIEW rpt.FactFinance AS            -- CREATE OR ALTER: SQL Server 2016 SP1+, Fabric WH
SELECT CAST(f.ScenarioKey AS int)        AS ScenarioKey,
       CAST(f.PeriodDate  AS date)       AS PeriodDate,
       CAST(f.AccountKey  AS int)        AS AccountKey,
       CAST(f.EntityKey   AS int)        AS EntityKey,
       CAST(f.CurrencyCode AS varchar(3)) AS CurrencyCode,
       CAST(f.AmountLC    AS decimal(19,4)) AS AmountLC,   -- the model's hidden `Amount LC` and its OLS
       CAST(f.AmountGC    AS decimal(19,4)) AS AmountGC
FROM   gold.FactFinance f;
```

Direct Lake on OneLake: **tables**, named as the contract (views are not supported; on the
SQL endpoint they force DirectQuery). Materialise with CTAS [Fabric WH] or materialized lake
views [Spark]:

```sql
DROP TABLE IF EXISTS gold.FactFinanceDL;
CREATE TABLE gold.FactFinanceDL AS
SELECT ScenarioKey, PeriodDate, AccountKey, EntityKey, CurrencyCode, AmountLC, AmountGC FROM gold.FactFinance;
```

## 11. Reconciliation and load checks [portable]

[05_checks.sql](../assets/sql/05_checks.sql) covers unique one-side keys, orphan keys, month
grain, grain uniqueness, a stale close flag (AC in an open period older than the latest closed
one; AC in the open period itself passes, so close-day reloads do not fail) and bridge coverage. Add for real sources:

```sql
-- AC month fact = GL detail per entity / month
SELECT COALESCE(m.EntityKey, g.EntityKey) AS EntityKey, COALESCE(m.PeriodDate, g.PeriodDate) AS PeriodDate,
       m.AmountLC AS FactLC, g.AmountLC AS GlLC
FROM  (SELECT EntityKey, PeriodDate, SUM(AmountLC) AS AmountLC FROM gold.FactFinance WHERE ScenarioKey = 1 GROUP BY EntityKey, PeriodDate) m
FULL JOIN (SELECT g.EntityKey, d.MonthStart AS PeriodDate, SUM(g.AmountLC * a.PLSign) AS AmountLC
           FROM gold.FactGlDetail g JOIN gold.DimDate d ON d.[Date] = g.PostingDate
           JOIN gold.DimAccount a ON a.AccountKey = g.AccountKey
           WHERE g.IsClosingEntry = 0 GROUP BY g.EntityKey, d.MonthStart) g
  ON  g.EntityKey = m.EntityKey AND g.PeriodDate = m.PeriodDate
WHERE ABS(COALESCE(m.AmountLC, 0) - COALESCE(g.AmountLC, 0)) > 0.01;

-- Phasing profiles sum to 1
SELECT ProfileCode, SUM(Weight) FROM plan.Phasing GROUP BY ProfileCode HAVING ABS(SUM(Weight) - 1) > 0.000001;

-- Annual plan rows without a known phasing profile (the §3 load would drop them silently)
SELECT p.* FROM plan.PlanEntry p
WHERE p.Status = 'Approved' AND p.FiscalPeriod IS NULL
  AND NOT EXISTS (SELECT 1 FROM plan.Phasing ph WHERE ph.ProfileCode = p.PhasingProfile);

-- Approved plan = loaded plan, per version (local currency, P&L sign as the §3 load stores it)
SELECT COALESCE(p.VersionCode, f.VersionCode) AS VersionCode, p.PlanLC, f.LoadedLC
FROM  (SELECT p.VersionCode, SUM(p.AmountLC * COALESCE(a.PLSign, -1)) AS PlanLC
       FROM plan.PlanEntry p LEFT JOIN gold.DimAccount a ON a.AccountNo = p.AccountNo
       WHERE p.Status = 'Approved' GROUP BY p.VersionCode) p
FULL JOIN (SELECT s.VersionCode, SUM(f.AmountLC) AS LoadedLC
           FROM gold.FactFinance f JOIN gold.DimScenario s ON s.ScenarioKey = f.ScenarioKey
           WHERE s.ScenarioType IN ('BU', 'PL') GROUP BY s.VersionCode) f
  ON  f.VersionCode = p.VersionCode
WHERE ABS(COALESCE(p.PlanLC, 0) - COALESCE(f.LoadedLC, 0)) > 0.01;

-- Every rate needed by the load exists (missing rates silently drop rows in an INNER JOIN).
-- Same predicate as the §8 load: group currency, version 'AC', AVERAGE for P&L, CLOSING for BS.
DECLARE @GroupCurrency varchar(3) = 'EUR';
SELECT DISTINCT g.CurrencyCode, d.MonthStart, a.AccountType
FROM gold.FactGlDetail g JOIN gold.DimDate d ON d.[Date] = g.PostingDate
JOIN gold.DimAccount a ON a.AccountKey = g.AccountKey
LEFT JOIN gold.FxRate r ON r.FromCurrency = g.CurrencyCode AND r.ToCurrency = @GroupCurrency
                       AND r.VersionCode = 'AC' AND r.MonthStart = d.MonthStart
                       AND r.RateType = CASE WHEN a.AccountType = 'BS' THEN 'CLOSING' ELSE 'AVERAGE' END
WHERE g.IsClosingEntry = 0 AND r.Rate IS NULL;
-- Plan loads (§3): the same against plan.PlanEntry with RateType 'BUDGET' and r.VersionCode = p.VersionCode.
```

Run the checks in the pipeline **before** refreshing or framing the model; fail the run on any
row.

## 12. Security mapping [portable]

```sql
CREATE TABLE gold.SecUserEntity (UserPrincipalName varchar(100) NOT NULL, EntityKey int NOT NULL);
-- Fill from an authoritative source (ERP user ↔ company, or an Entra group export), lower-case UPNs.
```

Source-side RLS (SQL `SECURITY POLICY`) is not inherited by Import or Direct Lake models and
forces DirectQuery fallback on Direct Lake on SQL. Secure in the semantic model.
