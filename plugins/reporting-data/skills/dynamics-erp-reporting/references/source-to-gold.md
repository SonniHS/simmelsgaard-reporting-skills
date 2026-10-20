# Source-to-gold mapping: ERP → IBCS finance star

The target is the star in
[01_schema.sql](../../sql-reporting-backend/assets/sql/01_schema.sql) (same table and column
names), extended with the drill fact and SCD2 dimensions from
[sql-reporting-backend](../../sql-reporting-backend/SKILL.md).

## Contents
1. Medallion flow and orchestration
2. Mapping table per gold object
3. Conforming several ERPs (F&O + BC, acquisitions)
4. Scenario mapping
5. Sign, closing entries, currencies per source
6. Reconciliation per source

## 1. Flow

```
F&O ──Link to Fabric──┐
CE  ──Link to Fabric──┤ BRONZE (as delivered,   SILVER (Lakehouse: Spark /   GOLD (Warehouse or Lakehouse,
BC  ──mirror/bc2adls──┼─▶ read-only shortcuts, ─▶ materialized lake views) ─▶ V-Order): Dim*, Fact*, Bridge*,
Plan (SQL DB Fabric)──┘  mirrors)                • IsDelete filtered         Sec*  (contract)
                                                 • enums decoded (1 language)      │
                                                 • company resolved, upper case    ▼
                                                 • wide dimension tables      checks pass → frame / refresh
                                                 • FX monthly avg/closing      the semantic model
                                                 • period status, closing flags
```

Orchestration (Data Factory pipeline): wait for freshness (max `SinkModifiedOn` /
`modifiedon` / mirror status) → silver → gold (batch per fiscal year or open period) →
checks (fail on any row) → frame/refresh the model → warm the cache with the key queries.
During close days reload the open period several times a day; after close lock it
(`IsClosedPeriod`) and stop reloading except on an explicit reopen.

## 2. Mapping table

| Gold object | F&O | Business Central | Dataverse / CE |
|---|---|---|---|
| `DimEntity` | `CompanyInfo` + `DirPartyTable`; `Ledger` (currencies, calendar, CoA) | `Company`, `General Ledger Setup` | `businessunit` (if used) |
| `DimAccount` (+ PLSign, AccountType) | `MainAccount` (+ `MainAccountCategory`, `LedgerChartOfAccounts`) | `G/L Account` (Posting only), `Income/Balance`, categories | — |
| `DimReportLine` + `BridgeReportLineAccount` | governed mapping table (ranges) or Financial reports rows | `Totaling` ranges / account schedule lines | — |
| `DimCostCenter`, `DimDepartment`, `DimProject` (SCD2 as needed) | wide `fno_ledger_dimension` + backing tables (`OMOperatingUnit`, `DimensionFinancialTag`) | `Dimension Value`, `DimDimensionSet` | — |
| `DimDate.IsClosedPeriod` | `LedgerFiscalCalendarPeriod` status, `FiscalCalendarPeriod` type | close calendar / `Accounting Period` | — |
| `FxRate` | `ExchangeRate` + `ExchangeRateCurrencyPair` + `ExchangeRateType` | `Currency Exchange Rate` | (record rates only; don't use) |
| `FactGlDetail` (AC) | `GeneralJournalAccountEntry` + `GeneralJournalEntry` | `G/L Entry` | — |
| `FactFinance` AC | monthly aggregate of `FactGlDetail` (Current layer, Operating periods) | monthly aggregate (no closing entries) | — |
| `FactFinance` BU | `BudgetTransactionLine` (Completed) | `G/L Budget Entry` | — |
| `FactFinance` FC / PL | planning DB (e.g. SQL database in Fabric) | planning DB | — |
| Sales facts | `CustInvoiceTrans`/`Jour` | `Value Entry`, `Sales Invoice Line` | `opportunity` snapshot, `invoicedetail` |
| `SecUserEntity` | F&O user ↔ company (`UserInfo`, security roles by legal entity) or Entra groups | BC permission sets per company or Entra groups | business units / teams |

## 3. Conforming several ERPs

- **Entity key** `(SourceSystem, CompanyId)` → one `EntityKey`; `EntityCode` unique across
  systems (prefix if needed).
- **Group chart of accounts**: map every local account to a group account in a governed
  mapping table `(SourceSystem, Company, LocalAccountNo) → GroupAccountNo`; the bridge and
  report lines work on group accounts. Unmapped accounts → `-1` and a failing check.
- **Dimensions**: harmonise cost centre/department codes per source into one conformed
  dimension with a source column; keep local codes as attributes.
- **Calendars**: map each company's fiscal periods to the group calendar
  (`FiscalPeriodSeq`); different year-ends need a mapping, not a different Date table.
- **Currencies**: one group currency, one rate source (treasury or the parent's ERP).

## 4. Scenario mapping

| Scenario | Source | `DimScenario` row |
|---|---|---|
| AC | GL | `AC` (one row) |
| BU | F&O budget model / BC budget name, approved | `BU<year>` per budget; `IsCurrent` if several revisions |
| FC | planning DB versions (n+m) | `FC<year>-<mm>`; `FcActualMonths = n`; `IsLatestFC` on the newest approved |
| PL | mid-term plan in the planning DB | `PL<years>` |
| PY | **not mapped**: derived in the model | — |

## 5. Sign, closing entries, currencies

| Source | Amount sign | Closing/opening entries | Currency columns |
|---|---|---|---|
| F&O | `AccountingCurrencyAmount` debit + | Opening/Closing **period types**; posting layer ≠ Current | accounting (LC), reporting (RC), transaction (TC) |
| BC | `Amount` debit + | closing **dates** (time part / source code) | LCY `Amount`, ACY `Additional-Currency Amount` |
| Planning DB | as entered (define it!) | — | entry currency + plan rate |

Gold stores P&L sign (`× PLSign`) in `FactFinance`; `FactGlDetail` may keep the natural sign
for audit drill. Report lines carry `DisplaySign` (cost lines −1, shown positive) and
`VarianceDirection` (costs −1); the model compares displayed values.

## 6. Reconciliation per source

| Check | F&O | BC |
|---|---|---|
| AC month fact = GL detail | per company, main account, month | per company, G/L account, month |
| GL detail = ERP trial balance | `GeneralLedgerBalance*` or a trial-balance export | `G/L Account` balance at date (API) or trial balance report |
| BU = budget register | Σ `BudgetTransactionLine` Completed per model | Σ `G/L Budget Entry` per budget name |
| Unmapped accounts / companies | `AccountKey = -1` rows | same |
| Freshness | max `SinkModifiedOn` per table | max `systemModifiedAt` / mirror status |
