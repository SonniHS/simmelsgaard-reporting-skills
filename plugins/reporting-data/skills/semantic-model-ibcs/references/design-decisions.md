# Design decisions for IBCS semantic models

Status: October 2026. Authority for platform behaviour is Microsoft Learn; the links below are
the pages to re-check, especially for anything marked preview.

- Direct Lake: https://learn.microsoft.com/fabric/fundamentals/direct-lake-overview
- Storage modes: https://learn.microsoft.com/power-bi/transform-model/desktop-storage-mode
- Calculation groups: https://learn.microsoft.com/power-bi/transform-model/calculation-groups
- DAX user-defined functions: https://learn.microsoft.com/dax/best-practices/dax-user-defined-functions
- Time intelligence (incl. calendar-based, preview): https://learn.microsoft.com/power-bi/transform-model/desktop-time-intelligence
- Composite models: https://learn.microsoft.com/power-bi/guidance/composite-model-guidance

## Contents
1. Storage mode
2. Scenario design: one fact or several
3. Grain and detail
4. Date table and fiscal calendars
5. Calc groups vs explicit measures
6. Sign convention and polarity
7. Report lines vs account hierarchy
8. Security
9. Multi-currency
10. Consumers: Power BI, org apps, Fabric Apps, Excel

---

## 1. Storage mode

| Situation | Choose | Notes |
|---|---|---|
| Gold tables in a Fabric Lakehouse/Warehouse | **Direct Lake on OneLake** | No DirectQuery fallback; can add Import tables (composite). Turn off automatic updates, frame after the load. Over a guardrail = refresh fails |
| Gold outside Fabric, small (month-grain P&L: < ~10 M rows) | **Import** | Through gateway (on-prem) or VNet gateway (private Azure SQL). Incremental refresh around the open periods; full reload at year-end close |
| Must stay in source, near-real-time, source-enforced security | DirectQuery | Worst fit for IBCS matrices (many measures per cell → many SQL queries). Dual dimensions, aggregations |
| Existing Direct Lake on SQL model | Keep or migrate | Views and SQL RLS force DirectQuery fallback; `directLakeBehavior: directLakeOnly` in dev |
| Planning/write-back data (BU/FC entry) | SQL database in Fabric → its OneLake mirror → Direct Lake (or Import) | Avoid DirectQuery for planning tables |

Mode-independent: calc groups, field parameters, UDFs and calculated tables without Direct
Lake references work in every mode, so the IBCS machinery doesn't change when the storage
changes. Calculated columns are not available in Direct Lake on SQL and only in preview on
OneLake: put derived columns (fiscal attributes, flags, flattened hierarchy levels) in SQL.

Direct Lake guardrails that matter for finance are per table and per capacity SKU (files,
row groups, rows); look up the current table on Learn. On small SKUs give the IBCS model a
monthly aggregate and keep line-level GL in a separate drill model.

## 2. Scenario design

**Default: one fact at the common grain with a Scenario dimension** (option A). One measure
set, scenarios are filters, new forecast versions are rows. Choose separate facts (option B)
only when AC detail dominates and plan is sparse; then every measure needs a plan twin plus
grain guards ([dax-patterns.md](dax-patterns.md) §11).

Scenario dimension rules:
- One row per **version** (`BU2026`, `FC2026-09`); `ScenarioType` carries the IBCS code.
- PY is never stored. FC "n+m" versions store the copied AC months so the version is a
  complete year.
- Disconnected `FC Version` picker; default = `IsLatestFC`.
- BU vs PL: keep both types if the organisation has an annual budget and a mid-term plan;
  IBCS uses PL as the generic plan code, so label carefully in titles.
- `IbcsNotation` (solid / outlined / hatched) on the dimension feeds custom visuals.

## 3. Grain and detail

- IBCS pages: month grain (or week for retail). AC aggregated from the GL in SQL.
- Drill to vouchers: a `FactGlDetail` at line grain with the same conformed dimensions
  (same model if within guardrails, otherwise a separate drill-through model).
- Reconcile both facts (Σ detail = Σ month per entity/account/period) in the load.
- Dimensions the plan lacks: `-2 Not applicable` member, not NULLs.

## 4. Date table and fiscal calendars

- One day-grain table, marked, covering every scenario year. Fiscal attributes from SQL:
  `FiscalYearNo`, `FiscalPeriod`, `FiscalPeriodSeq` (running), `IsClosedPeriod` from the ERP
  period status.
- Gregorian or shifted Gregorian: classic time intelligence works (`SAMEPERIODLASTYEAR`).
- 4-4-5 / 13 periods: offsets on `FiscalPeriodSeq`. Calendar-based time intelligence handles
  them natively but was **preview** in Oct 2026 and does not work in live-connected/composite
  models.
- ERP closing periods (F&O Closing/Opening, BC closing dates) are excluded from monthly P&L
  in SQL, not in DAX.

## 5. Calc groups vs explicit measures

| Need | Choose |
|---|---|
| Power BI matrices with scenario/variance columns | Calc group (Scenario Analysis) |
| Period views (YTD, R12, FY) crossed with scenarios | Second calc group, lower precedence |
| Fabric App queries | Calc group, referenced by `CALCULATE ( [m], 'Scenario Analysis'[Scenario] = "ΔPY" )` |
| Excel PivotTables, some custom visuals, fixed-column exports | Thin explicit measures **over** the calc items (`Revenue ΔPY%`) |
| Composite model on top of a certified model | Calc groups of the source work; the composite's own measures can't call the source's UDFs |

Never build two independent definitions; the explicit measures must call the calc items.

## 6. Sign convention and polarity

- **Stored** in P&L sign (revenue +, cost −), so subtotals are plain sums.
- **Displayed and compared** with `'Report Line'[DisplaySign]` (costs positive, profit lines
  as they are): ΔX and ΔX% are computed on displayed values, so cost lines get a meaningful
  Δ% and only real negative references (losses) are N/A.
- `VarianceDirection` per report line / KPI, relative to the displayed value: revenue/profit
  +1, costs −1, neutral 0. Drives colour only; never flip signs inside calc items.

## 7. Report lines vs account hierarchy

- **Account hierarchy** (CoA groups) for drill: flattened Level1..LevelN columns from SQL.
- **Report lines** (P&L/BS layout with subtotals and ratios) for IBCS tables and the
  calculation waterfall: `DimReportLine` + bridge (subtotal → all accounts beneath), one
  bidirectional relationship, `Report Value` SWITCH for ratio lines.
- ERP specifics: BC `Totaling` ranges and F&O financial-statement rows are expanded into the
  bridge in SQL ([dynamics-erp-reporting](../../dynamics-erp-reporting/SKILL.md)).

## 8. Security

- Dynamic RLS on dimensions (Entity, CostCenter) from an authoritative mapping table.
- Direct Lake: RLS in the semantic model + fixed-identity connection. OneLake security RLS is
  limited; SQL-endpoint RLS forces DirectQuery on Direct Lake on SQL.
- OLS only for whole objects (salary columns, payroll fact). Visuals touching OLS objects
  error for restricted users: separate pages or models.
- Fabric Apps with delegated auth run the DAX as the signed-in user: RLS/OLS apply. Org apps
  grant item access but not to the underlying model; grant Read on the model separately.
- Test with "View as" and with `EVALUATE` under an effective user in DAX query view.

## 9. Multi-currency

- Convert in SQL: P&L at monthly average, BS at closing, BU/FC at fixed plan rates per
  version. The model sums `AmountGC` (group currency, whatever you chose).
- Keep `AmountLC` for entity-level views (guard with `HASONEVALUE ( Entity[LocalCurrency] )`).
- FX-neutral comparisons need extra stored columns (`AmountGC_BudgetRate`, `AmountGC_CYRate`).

## 10. Consumers

| Consumer | What it needs from the model |
|---|---|
| Power BI report / org app | Calc groups on matrix columns, `fx Variance Colour` for conditional formatting, field parameters, Scale slicer, descriptions |
| Fabric App | Stable names (the contract), `///` descriptions (readable via `INFO.VIEW.MEASURES()`), raw values; the app formats by value kind ([visual-data-contract.md](visual-data-contract.md) §0.4). The tenant setting for the semantic-model Execute Queries REST API must be on |
| Excel | Explicit measures for key variances; consider a perspective |
| Copilot / data agents | Descriptions on every visible object, synonyms in the culture's linguistic metadata |
