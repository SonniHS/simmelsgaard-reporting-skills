# Dynamics 365 Business Central (BC) → Fabric → IBCS star

Status: October 2026. Table and field names are BC's standard schema (authority: Microsoft
Learn, Business Central developer and API reference). Column names in the SQL below are
**silver names** (friendly, per company): each export tool names columns differently, so map
once in a silver view. Items marked *(verify)* were not checked against a live tenant.

Useful Learn pages:
- API v2.0: https://learn.microsoft.com/dynamics365/business-central/dev-itpro/api-reference/v2.0/
- `DataPerCompany` property: https://learn.microsoft.com/dynamics365/business-central/dev-itpro/developer/properties/devenv-datapercompany-property
- Operational limits: https://learn.microsoft.com/dynamics365/business-central/dev-itpro/administration/operational-limits-online
- Open mirroring in Fabric: https://learn.microsoft.com/fabric/mirroring/overview

## Contents
1. Routes into Fabric (and their status)
2. Silver naming: one mapping view per table
3. Key tables
4. Companies
5. Dimensions: global, shortcut, Dimension Set ID
6. G/L entries → FactGlDetail (closing dates)
7. G/L budgets → BU scenario
8. Accounting periods → period status
9. Currency
10. Chart of accounts, Totaling, account schedules → report lines
11. Sales and inventory
12. Pitfalls checklist

---

## 1. Routes

| Route | Status (Oct 2026) | Use when | Notes |
|---|---|---|---|
| **Native BC → Fabric mirroring** | Announced at the end of Sept 2026; a public preview with a BC 29.x update is expected per community reports. **Not documented on Learn at the time of writing (unverified)** | New builds once a preview is available and accepted | Per community reports: built on open mirroring; a BC setup page pushes selected **companies and tables** (incl. extension fields) into an open-mirroring database; deletes replicate; latency minutes; Fabric storage/query costs apply. *(unverified until Microsoft docs exist)* |
| **bc2adls** (community fork) → Lakehouse or **open mirroring** | Widely used today; Microsoft's original repo is archived; fork maturity varies — record fork + version | Today, any size | AL extension; incremental exports with deletions; per table/company; select fields in setup; check the fork's maintainer and support model |
| Partner open-mirroring connectors | Available | Managed alternative | Commercial |
| BC API v2.0 / custom API pages → pipelines / Dataflow Gen2 / notebooks | GA | Small/medium volume, few tables | Incremental on `lastModifiedDateTime`/`systemModifiedAt`; subject to operational limits; deletes need extra logic |
| Power BI BC connector (Import) | GA | One small company, no platform | Not a gold layer |

Decision now: build silver against **bc2adls/open mirroring** with a mapping view per table,
so switching to native mirroring later only changes the views.

## 2. Silver naming

bc2adls exports columns as `<FieldName>-<FieldNo>` and adds `$Company` and system columns
*(verify against your fork's version)*; native mirroring will use its own naming. Normalise:

```sql
-- silver.bc_gl_entry  (example for bc2adls naming; adjust to your export)
SELECT  UPPER([$Company])                   AS Company,
        [EntryNo-1]                         AS EntryNo,
        [GLAccountNo-3]                     AS GLAccountNo,
        [PostingDate-4]                     AS PostingDateTime,  -- keep the time part: closing dates
        [DocumentType-5]                    AS DocumentType,
        [DocumentNo-6]                      AS DocumentNo,
        [Amount-17]                         AS Amount,           -- LCY, debit +
        [AdditionalCurrencyAmount-68]       AS AmountACY,
        [GlobalDimension1Code-23]           AS GlobalDim1,
        [GlobalDimension2Code-24]           AS GlobalDim2,
        [DimensionSetID-480]                AS DimensionSetID,
        [SourceCode-28]                     AS SourceCode
FROM    bronze.bc_glentry_17;
```

Field numbers above follow the standard G/L Entry table *(verify the exact names/numbers in
your export; they are the contract, so pin them in tests)*.

## 3. Key tables

| Table [no.] | Purpose | Columns that matter |
|---|---|---|
| G/L Entry [17] | AC fact | Entry No., G/L Account No., Posting Date, Document Type/No., Amount, Debit/Credit Amount, Additional-Currency Amount, Global Dimension 1/2 Code, **Dimension Set ID**, Source Code |
| G/L Account [15] | CoA | No., Name, **Account Type** (Posting/Heading/Total/Begin-Total/End-Total), **Income/Balance**, Account Category, Account Subcategory Entry No., **Totaling**, Indentation |
| Dimension [348], Dimension Value [349] | dimensions | Code, Name, Dimension Value Type, Totaling |
| Dimension Set Entry [480] | set decoding | Dimension Set ID, Dimension Code, Dimension Value Code |
| G/L Budget Name [95], G/L Budget Entry [96] | budget | Budget Name, G/L Account No., Date, Amount, Global Dimension 1/2, Budget Dimension 1–4, Dimension Set ID |
| Accounting Period [50] | calendar | Starting Date, New Fiscal Year, Closed, Date Locked |
| Currency [4], Currency Exchange Rate [330] | FX | Starting Date, Exchange Rate Amount, Relational Exch. Rate Amount |
| General Ledger Setup [98] | per company | LCY Code, Additional Reporting Currency, Global Dimension 1/2 Code, Shortcut Dimension 3–8 Code |
| Company | list of companies | tables are per company when `DataPerCompany = true` (default); `false` tables are shared |

## 4. Companies

One environment holds many companies. Tables with `DataPerCompany = true` (the default) are
per company and `Entry No.` is unique only within a company; tables with
`DataPerCompany = false` hold one shared copy — don't multiply them per company. Check the
property per table. Union the per-company tables in silver, key on `(Company, …)`, and
upper-case the company name/ID before joining. Companies can live in several environments
(per country): add the environment to the key if so.

## 5. Dimensions

- Global dimensions 1 and 2 are denormalised on most entries; shortcut dimensions 3–8 and all
  others only through **Dimension Set ID**.
- Which code is "Global Dimension 1" differs per company (General Ledger Setup): map codes,
  not positions.

```sql
-- gold.DimDimensionSet: one row per company x set id, one column per dimension code
-- (the codes below are examples: list yours from the Dimension table first)
SELECT  Company, DimensionSetID,
        MAX(CASE WHEN DimensionCode = 'DEPARTMENT' THEN DimensionValueCode END) AS Department,
        MAX(CASE WHEN DimensionCode = 'PROJECT'    THEN DimensionValueCode END) AS Project,
        MAX(CASE WHEN DimensionCode = 'AREA'       THEN DimensionValueCode END) AS Area
FROM    silver.bc_dimension_set_entry
GROUP BY Company, DimensionSetID;
-- Dimension Set ID 0 = no dimensions: add a row per company with all NULL -> map to -1 members.
```

## 6. G/L entries → FactGlDetail

**Closing dates**: year-end closing entries post on a *closing date* (shown as C31.12.2026 in
the UI). In the database a closing date is the same calendar date with a non-midnight time
*(commonly described as 23:59:59; verify in your export)*; the API/exports may lose the time
part. Use two signals:

```sql
DECLARE @CloseIncomeSourceCode varchar(10) = '<your-close-income-source-code>';
SELECT  g.Company, g.EntryNo,
        CAST(g.PostingDateTime AS date)                                   AS PostingDate,
        g.GLAccountNo, g.Amount AS AmountLC,
        ds.Department, ds.Project,
        CASE WHEN CAST(g.PostingDateTime AS time) <> '00:00:00'
               OR g.SourceCode = @CloseIncomeSourceCode                  -- from Source Code Setup (Close Income Statement)
             THEN 1 ELSE 0 END                                            AS IsClosingEntry
FROM    silver.bc_gl_entry g
LEFT JOIN gold.DimDimensionSet ds ON ds.Company = g.Company AND ds.DimensionSetID = g.DimensionSetID;
```

Exclude `IsClosingEntry = 1` from monthly P&L; keep it for BS roll-forward. Only accounts of
type **Posting** carry entries.

## 7. G/L budgets → BU scenario

```sql
SELECT  UPPER(b.Company) AS Company,
        b.BudgetName,                              -- -> DimScenario.VersionCode (e.g. 'BU2026')
        CAST(b.[Date] AS date) AS BudgetDate,      -- usually first of month
        b.GLAccountNo,
        b.Amount AS AmountLC,                      -- GL sign
        ds.Department, ds.Project
FROM    silver.bc_gl_budget_entry b
LEFT JOIN gold.DimDimensionSet ds ON ds.Company = b.Company AND ds.DimensionSetID = b.DimensionSetID;
```

Budget dimensions 1–4 are defined per budget name: decode via Dimension Set ID, not by
position. Forecasts usually come from the planning database.

## 8. Accounting periods → period status

`Accounting Period` holds only period **start dates** (`Starting Date`, `New Fiscal Year`,
`Closed`, `Date Locked`). Derive period end = next start − 1 day:

```sql
SELECT  Company, StartingDate AS PeriodStart,
        DATEADD(day, -1, LEAD(StartingDate) OVER (PARTITION BY Company ORDER BY StartingDate)) AS PeriodEnd,
        NewFiscalYear, Closed, DateLocked
FROM    silver.bc_accounting_period;
```

`Closed` marks closed *fiscal years* (after Close Year); open months within a year are
controlled by posting-date restrictions in General Ledger Setup / User Setup, not by this
table. Define `IsClosedPeriod` from your close calendar (e.g. a governed close-status table)
if month-level status is needed *(verify the customer's process)*.

## 9. Currency

`Currency Exchange Rate`: rate = `Relational Exch. Rate Amount / Exchange Rate Amount` (LCY
per unit of the currency), effective from `Starting Date`; build monthly AVERAGE/CLOSING in
silver. `Additional-Currency Amount` (ACY) can serve as group currency if every company uses
the same ACY consistently; otherwise convert in gold.

## 10. Chart of accounts → report lines

- Fact uses only `Account Type = Posting`. `Income/Balance` → `AccountType` (P&L/BS),
  `PLSign = -1` for income-statement accounts.
- `Total`/`End-Total` accounts are formulas in **Totaling** (`4000..4999|6000..6999`): expand
  into the report-line bridge with the range SQL in
  [tsql-scripts.md](../../sql-reporting-backend/references/tsql-scripts.md) §7. Pad account
  numbers to equal length before text range compares.
- Indentation gives the CoA tree for drill (headings/begin-total/end-total pairs).
- Account schedules / Financial Reports (BC's row definitions) are the natural source for IBCS
  report lines; they're stored in `Acc. Schedule Line` *(verify table availability in your
  export)* with `Totaling` and `Totaling Type`.

## 11. Sales and inventory

| Fact | Tables |
|---|---|
| Sales (invoiced) | Value Entry [5802] (cost & sales amounts, item ledger link), Sales Invoice Line [113], Sales Cr.Memo Line [115] |
| Customers / items | Customer [18], Item [27], Item Category |
| Inventory | Item Ledger Entry [32], Value Entry [5802] |

`Value Entry` reconciles item value to the G/L; prefer it over document lines for revenue and
COGS by item.

## 12. Pitfalls checklist

- [ ] All companies unioned; keys include Company (and environment if several).
- [ ] Dimension Set ID decoded into a wide table; set 0 handled.
- [ ] Closing-date entries flagged and excluded from monthly P&L.
- [ ] Only Posting accounts in the fact; Totaling expanded into the bridge.
- [ ] Enums: captions (API) vs ordinals (exports) checked and decoded explicitly.
- [ ] Extension fields added in the export setup (bc2adls) or present (native mirroring, per
      community reports, unverified).
- [ ] Exchange rate = relational ÷ exchange-rate amount.
- [ ] Silver mapping views isolate the export tool's naming.
- [ ] Reconciliation: Σ G/L Entry per company/month = trial balance.
