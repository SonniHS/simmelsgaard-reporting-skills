/* ============================================================================
   Minimal seed: unknown members, scenarios, a small P&L layout and a few months of facts,
   so 05_checks.sql passes and the semantic-model test query (semantic-model-ibcs
   dax-patterns.md section 14) returns known numbers. Generic sample data; replace it with
   your loads. Run after 01_schema.sql and 02_dim_date.sql (DimDate must cover 2025-2027).
   Re-runnable: every table is emptied first. Portable T-SQL.

   Expected for 2026-09 YTD (only Jul..Sep are loaded), display sign (costs positive):
     REV    AC 330 000   PY 300 000   BU 315 000
     GP     AC 132 000   PY 120 000   BU 126 000
     EBIT   AC  57 000   PY  48 000   BU  48 000
     NET    AC  45 000   PY  37 500   BU  36 000
     EBIT_M AC 17.3 %    PY 16.0 %    BU 15.2 %
   ========================================================================== */

DELETE FROM gold.FactGlDetail;
DELETE FROM gold.FactFinance;
DELETE FROM gold.BridgeReportLineAccount;
DELETE FROM gold.DimReportLine;
DELETE FROM gold.DimAccount;
DELETE FROM gold.DimCostCenter;
DELETE FROM gold.DimEntity;
DELETE FROM gold.DimScenario;
DELETE FROM gold.FxRate;
DELETE FROM gold.SecUserEntity;

-- Every dimension: -1 Unknown, -2 Not applicable (plan rows at a coarser grain)
INSERT INTO gold.DimEntity (EntityKey, EntityCode, EntityName, Country, LocalCurrency, Region, GroupName) VALUES
    (-1, 'N/A', 'Unknown', 'N/A', 'EUR', 'N/A', 'Sample Group'),
    (-2, 'N/A-PLAN', 'Not applicable', 'N/A', 'EUR', 'N/A', 'Sample Group'),
    (1, 'E1', 'Sample Entity', 'Germany', 'EUR', 'Europe', 'Sample Group');

INSERT INTO gold.DimAccount (AccountKey, AccountNo, AccountName, AccountType, PLSign, ReportLineCode, ReportLineName, IsPosting) VALUES
    (-1, 'N/A', 'Unknown', 'P&L', -1, 'N/A', 'Unknown', 0),
    (-2, 'N/A-PLAN', 'Not applicable', 'P&L', -1, 'N/A', 'Not applicable', 0),
    (1, '4000', 'Revenue', 'P&L', -1, 'REV', 'Revenue', 1),
    (2, '5000', 'Cost of sales', 'P&L', -1, 'COGS', 'Cost of sales', 1),
    (3, '6000', 'Operating expenses', 'P&L', -1, 'OPEX', 'Operating expenses', 1),
    (4, '8000', 'Income tax', 'P&L', -1, 'TAX', 'Income tax', 1);

INSERT INTO gold.DimCostCenter (CostCenterKey, Company, CostCenterCode, CostCenterName, ValidFrom, ValidTo, IsCurrent, IsInferred) VALUES
    (-1, 'N/A', 'N/A', 'Unknown', '1900-01-01', '9999-12-31', 1, 0),
    (-2, 'N/A', 'N/A-PLAN', 'Not applicable', '1900-01-01', '9999-12-31', 1, 0);

-- One row per scenario version; PY is AC shifted in time, never stored
INSERT INTO gold.DimScenario (ScenarioKey, ScenarioType, ScenarioCode, VersionCode, VersionLabel, IsCurrent, IsLatestFC, FcActualMonths, SortOrder, IbcsNotation) VALUES
    (1, 'AC', 'AC', 'AC', 'Actual', 1, 0, NULL, 1, 'solid'),
    (2, 'BU', 'BU', 'BU2026', 'Budget 2026', 1, 0, NULL, 2, 'outlined'),
    (3, 'FC', 'FC', 'FC2026-09', 'Forecast 2026 (9+3)', 1, 1, 9, 3, 'hatched'),
    (4, 'PL', 'PL', 'PL2027', 'Plan 2027', 1, 0, NULL, 4, 'outlined');

-- P&L layout: DisplaySign -1 shows cost lines positive; VarianceDirection is for colour only
INSERT INTO gold.DimReportLine (ReportLineKey, LineCode, LineName, SortOrder, LineType, DisplaySign, VarianceDirection, IsBold, Indent) VALUES
    (1, 'REV', 'Revenue', 10, 'Detail', 1, 1, 0, 1),
    (2, 'COGS', 'Cost of sales', 20, 'Detail', -1, -1, 0, 1),
    (3, 'GP', 'Gross profit', 30, 'Subtotal', 1, 1, 1, 0),
    (4, 'OPEX', 'Operating expenses', 40, 'Detail', -1, -1, 0, 1),
    (5, 'EBIT', 'EBIT', 50, 'Subtotal', 1, 1, 1, 0),
    (6, 'TAX', 'Income tax', 60, 'Detail', -1, -1, 0, 1),
    (7, 'NET', 'Net income', 70, 'Total', 1, 1, 1, 0),
    (8, 'EBIT_M', 'EBIT margin', 80, 'Ratio', 1, 1, 0, 1);

-- A subtotal maps to every account beneath it; the ratio line maps to none
INSERT INTO gold.BridgeReportLineAccount (ReportLineKey, AccountKey) VALUES
    (1, 1), (2, 2), (4, 3), (6, 4),
    (3, 1), (3, 2),
    (5, 1), (5, 2), (5, 3),
    (7, 1), (7, 2), (7, 3), (7, 4);

-- Group currency EUR: the identity rate the loads join on, per month, type and version
INSERT INTO gold.FxRate (MonthStart, FromCurrency, ToCurrency, RateType, VersionCode, Rate)
SELECT DISTINCT d.MonthStart, 'EUR', 'EUR', t.RateType, t.VersionCode, 1
FROM gold.DimDate d
CROSS JOIN (VALUES ('AVERAGE', 'AC'), ('CLOSING', 'AC'), ('BUDGET', 'BU2026'), ('BUDGET', 'FC2026-09'), ('BUDGET', 'PL2027')) AS t(RateType, VersionCode)
WHERE d.[Year] BETWEEN 2025 AND 2027;

-- Facts in P&L sign (revenue +, cost -): AC Jul..Sep 2025 and 2026, BU2026 Jul..Sep
INSERT INTO gold.FactFinance (ScenarioKey, PeriodDate, DateKey, AccountKey, EntityKey, CurrencyCode, AmountLC, AmountGC)
SELECT v.ScenarioKey, CAST(v.PeriodDate AS date), CAST(REPLACE(v.PeriodDate, '-', '') AS int), v.AccountKey, 1, 'EUR', v.Amount, v.Amount
FROM (VALUES
    (1, '2025-07-01', 1,  95000), (1, '2025-07-01', 2, -57000), (1, '2025-07-01', 3, -24000), (1, '2025-07-01', 4, -3500),
    (1, '2025-08-01', 1, 100000), (1, '2025-08-01', 2, -60000), (1, '2025-08-01', 3, -24000), (1, '2025-08-01', 4, -3500),
    (1, '2025-09-01', 1, 105000), (1, '2025-09-01', 2, -63000), (1, '2025-09-01', 3, -24000), (1, '2025-09-01', 4, -3500),
    (1, '2026-07-01', 1, 100000), (1, '2026-07-01', 2, -60000), (1, '2026-07-01', 3, -25000), (1, '2026-07-01', 4, -4000),
    (1, '2026-08-01', 1, 110000), (1, '2026-08-01', 2, -66000), (1, '2026-08-01', 3, -25000), (1, '2026-08-01', 4, -4000),
    (1, '2026-09-01', 1, 120000), (1, '2026-09-01', 2, -72000), (1, '2026-09-01', 3, -25000), (1, '2026-09-01', 4, -4000),
    (2, '2026-07-01', 1, 105000), (2, '2026-07-01', 2, -63000), (2, '2026-07-01', 3, -26000), (2, '2026-07-01', 4, -4000),
    (2, '2026-08-01', 1, 105000), (2, '2026-08-01', 2, -63000), (2, '2026-08-01', 3, -26000), (2, '2026-08-01', 4, -4000),
    (2, '2026-09-01', 1, 105000), (2, '2026-09-01', 2, -63000), (2, '2026-09-01', 3, -26000), (2, '2026-09-01', 4, -4000)
) AS v(ScenarioKey, PeriodDate, AccountKey, Amount);

-- RLS test user (example.com is reserved for examples)
INSERT INTO gold.SecUserEntity (UserPrincipalName, EntityKey) VALUES ('controller@example.com', 1);
