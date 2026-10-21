/* ============================================================================
   IBCS finance star: gold-layer schema (DDL)
   ----------------------------------------------------------------------------
   Targets (one script for all):  SQL Server 2016+ | Azure SQL DB / MI |
                                  SQL database in Fabric | Fabric Warehouse
   Portability choices (why the script looks the way it does):
     - varchar, not nvarchar          -> Fabric Warehouse has no nvarchar (UTF-8 collation).
                                         SQL Server with non-Latin names: switch to nvarchar
                                         or a _UTF8 collation.
     - date / int / bigint / decimal / bit only; no datetime, money, tinyint
     - no IDENTITY, no constraints, no indexes here
                                      -> keys are supplied by your loads; PK/CCI scripts are
                                         split per platform in 04_optional_*.sql
     - DROP TABLE IF EXISTS           -> SQL Server 2016+ and Fabric Warehouse
   Lakehouse (Spark) users: create Delta tables with the same names and types instead.
   Sign convention: FactFinance amounts are STORED in P&L SIGN (revenue +, cost -), so
   subtotals are plain sums. They are DISPLAYED with DimReportLine.DisplaySign (costs
   positive); variances are computed on displayed values, colour from VarianceDirection
   (costs -1). Natural GL sign = AmountGC * DimAccount.PLSign.
   Group currency: AmountGC is in the group currency you choose (EUR in the examples).
   ========================================================================== */

IF SCHEMA_ID('gold') IS NULL
    EXEC ('CREATE SCHEMA gold');   -- dynamic SQL so the batch compiles when the schema exists

DROP TABLE IF EXISTS gold.FactGlDetail;
DROP TABLE IF EXISTS gold.FactFinance;
DROP TABLE IF EXISTS gold.BridgeReportLineAccount;
DROP TABLE IF EXISTS gold.SecUserEntity;
DROP TABLE IF EXISTS gold.FxRate;
DROP TABLE IF EXISTS gold.DimDate;
DROP TABLE IF EXISTS gold.DimScenario;
DROP TABLE IF EXISTS gold.DimAccount;
DROP TABLE IF EXISTS gold.DimReportLine;
DROP TABLE IF EXISTS gold.DimEntity;
DROP TABLE IF EXISTS gold.DimCostCenter;

-- Day grain, contiguous, covering every AC, PY, BU, FC and PL year.
CREATE TABLE gold.DimDate (
    DateKey            int          NOT NULL,   -- 20260930
    [Date]             date         NOT NULL,   -- relationship key (model marks it as date table)
    [Year]             int          NOT NULL,
    MonthNo            int          NOT NULL,
    YearMonth          int          NOT NULL,   -- 202609
    MonthStart         date         NOT NULL,
    MonthEnd           date         NOT NULL,
    MonthShort         varchar(3)   NOT NULL,   -- Sep
    MonthLabel         varchar(7)   NOT NULL,   -- 2026-09 (ISO 8601 month label)
    FiscalYearNo       int          NOT NULL,
    FiscalYear         varchar(6)   NOT NULL,   -- FY2026
    FiscalPeriod       int          NOT NULL,   -- 1..12
    FiscalQuarterNo    int          NOT NULL,
    FiscalYearQuarter  varchar(9)   NOT NULL,   -- FY2026-Q3
    FiscalYearPeriod   varchar(7)   NOT NULL,   -- 2026-09
    FiscalPeriodSeq    int          NOT NULL,   -- running period number: offsets for PY/R12
    IsoWeek            int          NOT NULL,
    IsClosedPeriod     bit          NOT NULL    -- 1 = period closed in the ERP (AC final)
);

-- One row per scenario VERSION. PY is not a scenario: it is AC shifted in time.
CREATE TABLE gold.DimScenario (
    ScenarioKey        int          NOT NULL,
    ScenarioType       varchar(2)   NOT NULL,   -- AC | BU | FC | PL   (IBCS codes)
    ScenarioCode       varchar(2)   NOT NULL,
    VersionCode        varchar(12)  NOT NULL,   -- BU2026, FC2026-09 ...
    VersionLabel       varchar(40)  NOT NULL,
    IsCurrent          bit          NOT NULL,
    IsLatestFC         bit          NOT NULL,   -- default forecast for the FC calc item
    FcActualMonths     int          NULL,       -- n of an "n+m" forecast
    SortOrder          int          NOT NULL,
    IbcsNotation       varchar(10)  NOT NULL    -- solid | outlined | hatched (for custom visuals)
);

CREATE TABLE gold.DimEntity (
    EntityKey          int          NOT NULL,   -- -1 = unknown member
    EntityCode         varchar(10)  NOT NULL,   -- ERP company / DataAreaId (upper case)
    EntityName         varchar(60)  NOT NULL,
    Country            varchar(40)  NOT NULL,
    LocalCurrency      varchar(3)   NOT NULL,   -- ISO 4217
    Region             varchar(20)  NOT NULL,
    GroupName          varchar(40)  NOT NULL
);

CREATE TABLE gold.DimAccount (
    AccountKey         int          NOT NULL,   -- -1 = unknown member
    AccountNo          varchar(20)  NOT NULL,
    AccountName        varchar(60)  NOT NULL,
    AccountType        varchar(10)  NOT NULL,   -- P&L | BS
    PLSign             int          NOT NULL,   -- -1 for P&L accounts (GL debit+ -> P&L sign)
    ReportLineCode     varchar(10)  NOT NULL,   -- detail line the account posts to
    ReportLineName     varchar(60)  NOT NULL,
    IsPosting          bit          NOT NULL
);

-- P&L layout: detail lines, subtotals, totals and ratio lines in calculation order.
CREATE TABLE gold.DimReportLine (
    ReportLineKey      int          NOT NULL,
    LineCode           varchar(10)  NOT NULL,   -- REV, GP, EBIT, EBIT_M ...
    LineName           varchar(60)  NOT NULL,
    SortOrder          int          NOT NULL,
    LineType           varchar(10)  NOT NULL,   -- Detail | Subtotal | Total | Ratio
    DisplaySign        int          NOT NULL,   -- +1 shown as stored; -1 cost lines shown positive
    VarianceDirection  int          NOT NULL,   -- colour only: +1 increase of the DISPLAYED value is good, -1 bad, 0 neutral
    IsBold             bit          NOT NULL,
    Indent             int          NOT NULL
);

-- A subtotal maps to ALL accounts beneath it; ratio lines map to none (computed in DAX).
CREATE TABLE gold.BridgeReportLineAccount (
    ReportLineKey      int          NOT NULL,
    AccountKey         int          NOT NULL
);

-- Month x rate type x version: the grain the loads in references/tsql-scripts.md join on
-- (AC: AVERAGE for P&L, CLOSING for BS, VersionCode 'AC'; BU/FC/PL: BUDGET per plan version).
-- Add a row FromCurrency = ToCurrency = group currency, Rate = 1, per month/type/version.
CREATE TABLE gold.FxRate (
    MonthStart         date         NOT NULL,   -- first day of the month
    FromCurrency       varchar(3)   NOT NULL,
    ToCurrency         varchar(3)   NOT NULL,   -- the group currency
    RateType           varchar(10)  NOT NULL,   -- AVERAGE | CLOSING | BUDGET
    VersionCode        varchar(12)  NOT NULL,   -- 'AC' for actual rates, plan version for BUDGET
    Rate               decimal(19,8) NOT NULL   -- group currency per 1 unit of FromCurrency (display factor applied)
);

-- Month grain, all scenarios. PeriodDate = first day of the month.
CREATE TABLE gold.FactFinance (
    ScenarioKey        int          NOT NULL,
    PeriodDate         date         NOT NULL,
    DateKey            int          NOT NULL,   -- yyyymmdd of PeriodDate (for int-keyed tools)
    AccountKey         int          NOT NULL,
    EntityKey          int          NOT NULL,
    CurrencyCode       varchar(3)   NOT NULL,   -- local currency of the entity
    AmountLC           decimal(19,4) NOT NULL,  -- local currency, P&L sign
    AmountGC           decimal(19,4) NOT NULL   -- group currency, P&L sign
);

-- SCD type 2 organisation dimension (references/tsql-scripts.md section 4). -1 Unknown, -2 Not applicable.
CREATE TABLE gold.DimCostCenter (
    CostCenterKey         int          NOT NULL,
    Company               varchar(10)  NOT NULL,
    CostCenterCode        varchar(20)  NOT NULL,
    CostCenterName        varchar(60)  NOT NULL,
    DepartmentCode        varchar(20)  NULL,       -- "as-was" attributes of this version
    SegmentCode           varchar(20)  NULL,
    CurrentDepartmentCode varchar(20)  NULL,       -- "as-is": attributes of the current version
    CurrentSegmentCode    varchar(20)  NULL,
    ValidFrom             date         NOT NULL,
    ValidTo               date         NOT NULL,   -- 9999-12-31 for the current version
    IsCurrent             bit          NOT NULL,
    IsInferred            bit          NOT NULL,   -- created by a fact load before the master data arrived
    RowHash               varchar(64)  NULL        -- SHA2_256 hex of the tracked attributes
);

-- GL line grain, AC only (management view; drill-through and reconciliation). Natural GL
-- sign: the monthly FactFinance applies DimAccount.PLSign (references/tsql-scripts.md section 8).
CREATE TABLE gold.FactGlDetail (
    GlLineId           varchar(40)  NOT NULL,   -- ERP line id (RecId, Entry No.), unique per entity
    PostingDate        date         NOT NULL,
    Voucher            varchar(40)  NULL,
    EntityKey          int          NOT NULL,
    AccountKey         int          NOT NULL,
    CostCenterKey      int          NOT NULL,
    CurrencyCode       varchar(3)   NOT NULL,   -- local currency of the entity
    AmountLC           decimal(19,4) NOT NULL,  -- natural GL sign
    IsClosingEntry     bit          NOT NULL    -- year-end closing / opening entries (excluded from monthly P&L)
);

-- Dynamic RLS mapping (UPN -> entity). Authoritative source in production: ERP/Entra extract.
CREATE TABLE gold.SecUserEntity (
    UserPrincipalName  varchar(100) NOT NULL,
    EntityKey          int          NOT NULL
);
