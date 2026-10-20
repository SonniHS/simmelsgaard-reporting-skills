/* ============================================================================
   Load checks: run after every load, before the semantic model is refreshed/framed.
   Queries 1-6 must return ZERO rows: fail the pipeline on any row. Query 7 is not a
   check: it prints reference totals to compare by hand, so leave it out of (or ignore
   it in) an automated "any row fails" step. Portable T-SQL.
   ========================================================================== */

-- 1. One-side keys unique (Direct Lake fails queries on duplicates; Import refresh fails)
SELECT 'DimDate'  AS tbl, CAST([Date] AS varchar(10)) AS k, COUNT(*) AS n FROM gold.DimDate     GROUP BY [Date]       HAVING COUNT(*) > 1
UNION ALL SELECT 'DimScenario', CAST(ScenarioKey AS varchar(10)), COUNT(*) FROM gold.DimScenario GROUP BY ScenarioKey HAVING COUNT(*) > 1
UNION ALL SELECT 'DimEntity',   CAST(EntityKey AS varchar(10)),   COUNT(*) FROM gold.DimEntity   GROUP BY EntityKey   HAVING COUNT(*) > 1
UNION ALL SELECT 'DimAccount',  CAST(AccountKey AS varchar(10)),  COUNT(*) FROM gold.DimAccount  GROUP BY AccountKey  HAVING COUNT(*) > 1
UNION ALL SELECT 'DimReportLine', CAST(ReportLineKey AS varchar(10)), COUNT(*) FROM gold.DimReportLine GROUP BY ReportLineKey HAVING COUNT(*) > 1;

-- 2. Orphan fact keys (should map to a real member or to -1 Unknown, never to nothing)
SELECT f.* FROM gold.FactFinance f LEFT JOIN gold.DimAccount  a ON a.AccountKey  = f.AccountKey  WHERE a.AccountKey  IS NULL;
SELECT f.* FROM gold.FactFinance f LEFT JOIN gold.DimEntity   e ON e.EntityKey   = f.EntityKey   WHERE e.EntityKey   IS NULL;
SELECT f.* FROM gold.FactFinance f LEFT JOIN gold.DimScenario s ON s.ScenarioKey = f.ScenarioKey WHERE s.ScenarioKey IS NULL;
SELECT f.* FROM gold.FactFinance f LEFT JOIN gold.DimDate     d ON d.[Date]      = f.PeriodDate  WHERE d.[Date]      IS NULL;

-- 3. Month grain: PeriodDate is always the first day of a month
SELECT * FROM gold.FactFinance WHERE DAY(PeriodDate) <> 1;

-- 4. Grain uniqueness of the fact
SELECT ScenarioKey, PeriodDate, AccountKey, EntityKey, COUNT(*) AS n
FROM gold.FactFinance GROUP BY ScenarioKey, PeriodDate, AccountKey, EntityKey HAVING COUNT(*) > 1;

-- 5. Close flag not stale. AC in the OPEN period is expected during close days (it is
--    reloaded several times a day), so it passes. An open period with AC that lies BEFORE
--    the latest closed period means IsClosedPeriod was not refreshed from the ERP.
SELECT f.PeriodDate, COUNT(*) AS n
FROM gold.FactFinance f
JOIN gold.DimDate d     ON d.[Date] = f.PeriodDate
JOIN gold.DimScenario s ON s.ScenarioKey = f.ScenarioKey
WHERE s.ScenarioType = 'AC' AND d.IsClosedPeriod = 0
  AND d.MonthStart < (SELECT MAX(MonthStart) FROM gold.DimDate WHERE IsClosedPeriod = 1)
GROUP BY f.PeriodDate;
--    With the ERP period status in silver (references/tsql-scripts.md section 2), also fail
--    on periods the ERP has closed but DimDate still flags open:
-- SELECT DISTINCT d.MonthStart FROM gold.DimDate d
-- JOIN silver.erp_period_status p ON d.[Date] BETWEEN p.PeriodStart AND p.PeriodEnd
-- WHERE p.IsClosed = 1 AND d.IsClosedPeriod = 0;

-- 6. Bridge coverage: every detail/subtotal/total line maps at least one account
SELECT rl.LineCode, COUNT(b.AccountKey) AS mapped_accounts
FROM gold.DimReportLine rl LEFT JOIN gold.BridgeReportLineAccount b ON b.ReportLineKey = rl.ReportLineKey
WHERE rl.LineType IN ('Detail', 'Subtotal', 'Total')
GROUP BY rl.LineCode HAVING COUNT(b.AccountKey) = 0;

-- 7. Reference totals (not a pass/fail check): revenue per scenario version for one year to date. Compare with the
--    semantic model's Revenue AC / BU YTD for the same month (set the dates to your period).
SELECT s.ScenarioType, s.VersionCode, SUM(f.AmountGC) AS RevenueGC
FROM gold.FactFinance f
JOIN gold.DimAccount  a ON a.AccountKey  = f.AccountKey
JOIN gold.DimScenario s ON s.ScenarioKey = f.ScenarioKey
WHERE a.ReportLineCode = 'REV' AND f.PeriodDate BETWEEN '2026-01-01' AND '2026-09-01'
GROUP BY s.ScenarioType, s.VersionCode
ORDER BY s.ScenarioType, s.VersionCode;
