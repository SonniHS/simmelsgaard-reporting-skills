/* ============================================================================
   gold.DimDate population: portable, set-based
   ----------------------------------------------------------------------------
   Runs on SQL Server 2016+, Azure SQL, SQL database in Fabric, Fabric Warehouse.
   Deliberately avoids: recursive CTEs (not in Fabric Warehouse), GENERATE_SERIES
   (SQL Server 2022+ only), FORMAT/DATENAME (culture/language dependent).
   Set the four variables below for your calendar.
   ========================================================================== */

DECLARE @Start        date = '2024-01-01';   -- first day of the earliest scenario year
DECLARE @End          date = '2027-12-31';   -- last day of the latest plan year
DECLARE @FyStartMonth int  = 1;              -- 7 = fiscal year July..June (FY named by end year)
DECLARE @LastClosed   date = '2026-09-30';   -- in production: from the ERP period status

DELETE FROM gold.DimDate;

INSERT INTO gold.DimDate (
    DateKey, [Date], [Year], MonthNo, YearMonth, MonthStart, MonthEnd, MonthShort, MonthLabel,
    FiscalYearNo, FiscalYear, FiscalPeriod, FiscalQuarterNo, FiscalYearQuarter, FiscalYearPeriod,
    FiscalPeriodSeq, IsoWeek, IsClosedPeriod)
SELECT
    YEAR(x.d) * 10000 + MONTH(x.d) * 100 + DAY(x.d)                         AS DateKey,
    x.d                                                                      AS [Date],
    YEAR(x.d)                                                                AS [Year],
    MONTH(x.d)                                                               AS MonthNo,
    YEAR(x.d) * 100 + MONTH(x.d)                                             AS YearMonth,
    DATEFROMPARTS(YEAR(x.d), MONTH(x.d), 1)                                  AS MonthStart,
    EOMONTH(x.d)                                                             AS MonthEnd,
    SUBSTRING('JanFebMarAprMayJunJulAugSepOctNovDec', (MONTH(x.d) - 1) * 3 + 1, 3) AS MonthShort,
    CONCAT(YEAR(x.d), '-', RIGHT(CONCAT('0', MONTH(x.d)), 2))                AS MonthLabel,
    x.fy                                                                     AS FiscalYearNo,
    CONCAT('FY', x.fy)                                                       AS FiscalYear,
    x.fp                                                                     AS FiscalPeriod,
    (x.fp - 1) / 3 + 1                                                       AS FiscalQuarterNo,
    CONCAT('FY', x.fy, '-Q', (x.fp - 1) / 3 + 1)                             AS FiscalYearQuarter,
    CONCAT(x.fy, '-', RIGHT(CONCAT('0', x.fp), 2))                           AS FiscalYearPeriod,
    x.fy * 12 + x.fp                                                         AS FiscalPeriodSeq,
    DATEPART(iso_week, x.d)                                                  AS IsoWeek,
    CAST(CASE WHEN x.d <= @LastClosed THEN 1 ELSE 0 END AS bit)              AS IsClosedPeriod
FROM (
    SELECT  dt.d,
            ((MONTH(dt.d) - @FyStartMonth + 12) % 12) + 1                    AS fp,
            YEAR(dt.d) + CASE WHEN @FyStartMonth > 1 AND MONTH(dt.d) >= @FyStartMonth
                              THEN 1 ELSE 0 END                              AS fy
    FROM (
        SELECT DATEADD(day, n.i, @Start) AS d
        FROM (
            SELECT a.v + 10 * b.v + 100 * c.v + 1000 * e.v AS i      -- 0..9999 days
            FROM       (VALUES (0),(1),(2),(3),(4),(5),(6),(7),(8),(9)) AS a(v)
            CROSS JOIN (VALUES (0),(1),(2),(3),(4),(5),(6),(7),(8),(9)) AS b(v)
            CROSS JOIN (VALUES (0),(1),(2),(3),(4),(5),(6),(7),(8),(9)) AS c(v)
            CROSS JOIN (VALUES (0),(1),(2),(3),(4),(5),(6),(7),(8),(9)) AS e(v)
        ) AS n
        WHERE n.i <= DATEDIFF(day, @Start, @End)
    ) AS dt
) AS x;
