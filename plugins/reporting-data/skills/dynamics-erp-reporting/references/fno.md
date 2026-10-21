# Dynamics 365 Finance & Operations (F&O) → Fabric → IBCS star

Status: October 2026. Table/field names are F&O's standard schema as exported by Link to
Fabric / Synapse Link (lower-case in the Lakehouse SQL endpoint); authority: Microsoft Learn.
Enum integer values are **not** hard-coded here: decode them from `GlobalOptionsetMetadata`.
Items marked *(verify)* were not checked against a live environment.

Useful Learn pages:
- Choose F&O data in Synapse Link / Link to Fabric (incl. known limitations): https://learn.microsoft.com/power-apps/maker/data-platform/azure-synapse-link-select-fno-data
- Transition from Export to Data Lake: https://learn.microsoft.com/power-apps/maker/data-platform/azure-synapse-link-transition-faq
- Link to Fabric FAQ: https://learn.microsoft.com/power-apps/maker/data-platform/fabric-link-faq
- Removed/deprecated platform features (Export to Data Lake dates): https://learn.microsoft.com/dynamics365/fin-ops-core/fin-ops/get-started/removed-deprecated-features-platform-updates
- Financial dimension framework: https://learn.microsoft.com/dynamics365/fin-ops-core/dev-itpro/financial/dimension-fk-edt-usage
- Business performance analytics: https://learn.microsoft.com/dynamics365/finance/business-performance-analytics/business-performance-analytics-home-page

## Contents
1. Route: Link to Fabric (and the Export to Data Lake migration)
2. Known table behaviours in the export
3. Key tables per subject
4. Company, partition, posting layer, periods
5. Enum decoding
6. Financial dimension decoding (DAVC → wide dimension)
7. Silver/gold SQL: GL lines → FactGlDetail → FactFinance
8. Budget register → BU scenario
9. Fiscal calendar → DimDate period status
10. Currency and exchange rates
11. Chart of accounts and financial-statement rows → report lines
12. Sales and supply-chain facts
13. Pitfalls checklist

---

## 1. Route

**Link to Fabric** (Power Apps maker portal → Azure Synapse Link → *Link to Microsoft
Fabric*): Dataverse writes Delta into Dataverse-managed storage and creates a Lakehouse with
shortcuts in your Fabric workspace.

- Prerequisites: F&O environment linked to a Power Platform environment (Tier-2+ / unified);
  Fabric capacity in the **same region** as the Dataverse environment; the replica counts
  toward **Dataverse database capacity** (licence cost).
- Select F&O **tables** explicitly (*Manage tables*); they're not auto-selected. Standard
  tables are change-tracking enabled with app updates; custom tables need row-version change
  tracking. Prefer tables over data entities (many entities fail change-tracking validation);
  rebuild entity shapes in silver (Microsoft's FastTrack implementation assets include a tool
  that generates SQL from entity definitions).
- **Low-latency sync** (Dataverse → Delta directly): existing profiles must be **unlinked and
  relinked** to switch (full initial sync).
- Limits: a maximum number of change-tracked tables per link; database restores (UAT refresh
  from prod) require re-adding the F&O tables.
- Not for bulk analytics: virtual entities/virtual tables (OData proxies), BYOD (legacy).
- Alternative for non-Fabric consumers: Azure Synapse Link to your own ADLS Gen2 (Delta or
  incremental CSV).

### Export to Data Lake end of service

Microsoft Learn (checked 2026-10): Export to Azure Data Lake was retired on 1 Nov 2024 and
**reaches end of service on 30 Nov 2026**, with **no extensions**; from then on no new or
changed data is exported. Files already exported stay. Link to Fabric and Synapse Link are not
affected. A pipeline still on Export to Data Lake must move to Link to Fabric or Synapse Link.

Migration checklist (Export to Data Lake CSV/CDM folders → Link to Fabric Delta):

| Area | Export to Data Lake | Link to Fabric / Synapse Link | Action |
|---|---|---|---|
| Format | CSV + CDM manifests per table | Delta tables (shortcuts) | Repoint silver readers; drop CDM-manifest parsing |
| Deletes | rows physically removed in full exports / CDC folders | rows kept with `IsDelete` | add `COALESCE(IsDelete, 0) = 0` everywhere |
| Enums | integers | integers + `GlobalOptionsetMetadata` | keep integer keys, join labels |
| Derived tables | base fields included | base fields **missing** (`CompanyInfo` has no `Name`) | join base tables on `RecId` |
| Ids | `RecId` | `RecId` + Dataverse `Id` (GUID), F&O `Id` → `FnO_Id` | keep joining on `RecId` |
| Long text | full | memo fields truncated | don't depend on long texts |
| Reserved-word columns | as is | trailing `_` (`Level_`) | rename in silver |
| Kernel tables (`DATAAREA`, `USERINFO`…) | near-real-time | refreshed daily | fine for dimensions |
| Data entities | many exported | only change-tracking-valid entities | switch to tables |
| Latency | minutes | tens of minutes (classic), lower with low-latency sync | check close-day SLAs |

Plan: inventory every table read from the lake → add them in Link to Fabric (one profile per
environment) → run both side by side and reconcile row counts and GL totals per company and
month → switch silver to the new source → keep the old files as an archive → uninstall the
add-in in LCS. Allow time for the initial sync of large tables (`GeneralJournalAccountEntry`).

## 2. Known table behaviours in the export

See the migration table above; the same rules apply to new builds. Also: master-company data
sharing tables are exported for all companies (filter to the master company); `TimeZoneID`
and binary fields are not exported.

## 3. Key tables per subject

| Subject | Tables | Key columns |
|---|---|---|
| GL voucher header | `GeneralJournalEntry` | `RecId`, `AccountingDate`, `Ledger`, `SubledgerVoucher`, `JournalCategory`, `PostingLayer`, `FiscalCalendarPeriod` |
| GL lines (**the AC fact**) | `GeneralJournalAccountEntry` | `GeneralJournalEntry`, `LedgerDimension` (→ DAVC), `MainAccount`, `AccountingCurrencyAmount`, `ReportingCurrencyAmount`, `TransactionCurrencyAmount`, `TransactionCurrencyCode`, `PostingType`, `IsCredit`, `Quantity` |
| Ledger per legal entity | `Ledger` | `PrimaryForLegalEntity` (→ `CompanyInfo.RecId`), `AccountingCurrency`, `ReportingCurrency`, `FiscalCalendar`, `ChartOfAccounts`, `DefaultExchangeRateType`, `BudgetExchangeRateType` |
| Legal entities | `CompanyInfo` + `DirPartyTable` | `DataArea` (company ID), name from `DirPartyTable.Name` via `RecId` |
| Chart of accounts | `MainAccount`, `MainAccountCategory`, `LedgerChartOfAccounts` | `MainAccountId` unique per chart only |
| Financial dimensions | `DimensionAttributeValueCombination`, `…ValueGroupCombination`, `…LevelValue`, `DimensionAttributeValue`, `DimensionAttribute`, `DimensionAttributeValueSet(Item)`, `DimensionFinancialTag`, `OMOperatingUnit` | §6 |
| Budget register | `BudgetTransactionHeader`, `BudgetTransactionLine`, `BudgetModel` | §8 |
| Budget planning | `BudgetPlanHeader`, `BudgetPlanLine`, `BudgetPlanScenario` | only if used |
| Calendars | `FiscalCalendar`, `FiscalCalendarYear`, `FiscalCalendarPeriod`, `LedgerFiscalCalendarPeriod` | §9 |
| Currency | `Currency`, `ExchangeRateType`, `ExchangeRateCurrencyPair`, `ExchangeRate` | §10 |
| Pre-aggregated balances | `GeneralLedgerBalance*` (financial dimension sets) | reconciliation only |
| Sales | `CustInvoiceJour`, `CustInvoiceTrans`, `CustTable`, `InventTable`, `EcoResProduct*` | §12 |

Before building a GL model from scratch, check **Business performance analytics** (BPA),
Microsoft's prebuilt F&O finance model; IBCS layouts and custom scenarios usually still need
your own gold layer.

## 4. Company, partition, posting layer, periods

- GL tables have **no `DataAreaId`**: company = `GeneralJournalEntry.Ledger →
  Ledger.PrimaryForLegalEntity → CompanyInfo.DataArea`.
- Company-specific tables carry `DataAreaId` in **lower case**; `UPPER()` it in silver before
  joining anything typed by humans or coming from BC/planning.
- `Partition`: one in cloud; include it in keys if on-prem/LBD data is also ingested.
- **Posting layer**: management reporting uses *Current* only; Operations/Tax layers hold
  other-GAAP adjustments.
- **Period types**: Opening and Closing periods hold year-start balances and year-end close
  postings: exclude both from monthly P&L; use opening transactions only for BS balances.
- Consolidation/elimination companies post through consolidation journals: flag them in
  `DimEntity` and decide legal vs consolidated views.

## 5. Enum decoding

```sql
-- silver helper: one row per (table, field, value) in the report language
SELECT EntityName, OptionSetName, [Option] AS EnumValue, LocalizedLabel AS EnumLabel
FROM   globaloptionsetmetadata
WHERE  LocalizedLabelLanguageCode = 1033;     -- choose the language explicitly (LCID)
```

Keep the integer as the key column, the label as an attribute; never hard-code integers in
DAX. Check the exact `EntityName`/`OptionSetName` casing in your environment. The label
strings used in the SQL below (`'Current'`, `'Operating'`, `'Completed'`) are the en-US
labels: if you decode in another language, compare against the integer or that language's
label.

## 6. Financial dimension decoding

Never split `DisplayValue` by delimiter: segment order differs per account structure and
advanced rule. Build a wide dimension once, keyed by DAVC `RecId`:

```sql
-- silver.fno_ledger_dimension (Spark SQL or SQL endpoint T-SQL)
SELECT  davc.recid                                    AS LedgerDimensionRecId,
        davc.displayvalue                             AS LedgerAccount,
        davc.mainaccountvalue                         AS MainAccountId,
        MAX(CASE WHEN da.name = 'BusinessUnit' THEN dalv.displayvalue END) AS BusinessUnit,
        MAX(CASE WHEN da.name = 'CostCenter'   THEN dalv.displayvalue END) AS CostCenter,
        MAX(CASE WHEN da.name = 'Department'   THEN dalv.displayvalue END) AS Department,
        MAX(CASE WHEN da.name = 'Project'      THEN dalv.displayvalue END) AS Project
FROM    dimensionattributevaluecombination      davc
JOIN    dimensionattributevaluegroupcombination dagc ON dagc.dimensionattributevaluecombination = davc.recid
JOIN    dimensionattributelevelvalue            dalv ON dalv.dimensionattributevaluegroup        = dagc.dimensionattributevaluegroup
JOIN    dimensionattributevalue                 dav  ON dav.recid = dalv.dimensionattributevalue
JOIN    dimensionattribute                      da   ON da.recid  = dav.dimensionattribute
WHERE   COALESCE(davc.isdelete, 0) = 0
GROUP BY davc.recid, davc.displayvalue, davc.mainaccountvalue;
```

- Dimension names (`BusinessUnit`, `CostCenter` …) are your `DimensionAttribute.Name` values:
  list them first (`SELECT name FROM dimensionattribute`).
- Default dimensions on master data (customer, vendor, project) use
  `DimensionAttributeValueSet` / `…SetItem` (EDT `DimensionDefault`), not DAVC.
- Names of dimension values: join `DimensionAttributeValue.EntityInstance` to the backing
  table (`OMOperatingUnit` for departments/cost centres, `DimensionFinancialTag` for custom
  lists).
- Newer versions denormalise per-dimension columns onto DAVC *(verify in your schema)*; if
  present they replace the join chain.
- Gold: `DimCostCenter` etc. keyed by `(Company, Code)`; the GL fact carries one key per
  dimension resolved through `fno_ledger_dimension`.

## 7. Silver/gold SQL: GL lines

```sql
-- silver.fno_gl_line
SELECT  gjae.recid                     AS GlLineRecId,
        CAST(gje.accountingdate AS date) AS PostingDate,
        gje.subledgervoucher           AS Voucher,
        UPPER(ci.dataarea)             AS CompanyId,
        gjae.ledgerdimension           AS LedgerDimensionRecId,
        gjae.accountingcurrencyamount  AS AmountLC,          -- accounting currency, debit +
        gjae.reportingcurrencyamount   AS AmountRC,
        gjae.transactioncurrencyamount AS AmountTC,
        gjae.transactioncurrencycode   AS CurrencyTC,
        l.accountingcurrency           AS CurrencyLC,
        gje.postinglayer               AS PostingLayerValue, -- integer enum: filter on this
        pl.LocalizedLabel              AS PostingLayer,
        pt.LocalizedLabel              AS FiscalPeriodType
FROM    generaljournalaccountentry gjae
JOIN    generaljournalentry  gje ON gje.recid = gjae.generaljournalentry
JOIN    ledger               l   ON l.recid   = gje.ledger
JOIN    companyinfo          ci  ON ci.recid  = l.primaryforlegalentity
JOIN    fiscalcalendarperiod fcp ON fcp.recid = gje.fiscalcalendarperiod
LEFT JOIN globaloptionsetmetadata pl ON pl.EntityName = 'generaljournalentry' AND pl.OptionSetName = 'postinglayer'
                                    AND pl.[Option] = gje.postinglayer AND pl.LocalizedLabelLanguageCode = 1033
LEFT JOIN globaloptionsetmetadata pt ON pt.EntityName = 'fiscalcalendarperiod' AND pt.OptionSetName = 'type'
                                    AND pt.[Option] = fcp.type AND pt.LocalizedLabelLanguageCode = 1033
WHERE   COALESCE(gjae.isdelete, 0) = 0 AND COALESCE(gje.isdelete, 0) = 0;
```

```sql
-- gold.FactGlDetail (line grain, AC only, management view)
SELECT  s.GlLineRecId, s.PostingDate, s.Voucher,
        COALESCE(e.EntityKey, -1)  AS EntityKey,
        COALESCE(a.AccountKey, -1) AS AccountKey,
        COALESCE(cc.CostCenterKey, -1) AS CostCenterKey,
        s.CurrencyLC AS CurrencyCode,
        s.AmountLC,                                   -- natural sign; P&L sign applied in FactFinance
        CASE WHEN s.FiscalPeriodType IN ('Opening', 'Closing') THEN 1 ELSE 0 END AS IsClosingEntry
                                                      -- a missed label lookup (NULL) keeps the row in the
                                                      -- P&L instead of dropping it; check: no NULL FiscalPeriodType
FROM    silver.fno_gl_line s
LEFT JOIN silver.fno_ledger_dimension ld ON ld.LedgerDimensionRecId = s.LedgerDimensionRecId
                                          -- LEFT: a missing DAVC row maps to -1 and shows in the
                                          -- trial-balance reconciliation instead of vanishing
LEFT JOIN gold.DimEntity     e  ON e.EntityCode = s.CompanyId
LEFT JOIN gold.DimAccount    a  ON a.ChartOfAccounts = e.ChartOfAccounts AND a.AccountNo = ld.MainAccountId
LEFT JOIN gold.DimCostCenter cc ON cc.Company = s.CompanyId AND cc.CostCenterCode = ld.CostCenter
                               AND s.PostingDate BETWEEN cc.ValidFrom AND cc.ValidTo
WHERE   s.PostingLayerValue = @CurrentLayer;          -- the integer enum value, not the label
```

Run this before the gold SELECT: resolve the integer once and assert it, so a label or casing mismatch in the option-set lookup
fails the load instead of filtering every row out (keep `postinglayer` as `PostingLayerValue`
in silver next to the decoded label):

```sql
DECLARE @CurrentLayer int = (SELECT [Option] FROM globaloptionsetmetadata
                             WHERE EntityName = 'generaljournalentry' AND OptionSetName = 'postinglayer'
                               AND LocalizedLabelLanguageCode = 1033 AND LocalizedLabel = 'Current');  -- (verify names)
IF @CurrentLayer IS NULL THROW 50001, 'Posting layer "Current" not found in globaloptionsetmetadata', 1;
-- load check: no GL line without a decoded layer
-- SELECT COUNT(*) FROM silver.fno_gl_line WHERE PostingLayer IS NULL;   -- must be 0
```

Then the monthly fact with FX conversion:
[tsql-scripts.md](../../sql-reporting-backend/references/tsql-scripts.md) §8. Labels such as
`'Current'`/`'Operating'` are the en-US enum labels *(verify)*. (`DimEntity.ChartOfAccounts`
and `DimAccount.ChartOfAccounts` extend the bundled schema for multi-chart setups.)

## 8. Budget register → BU scenario

```sql
SELECT  UPPER(ci.dataarea)               AS CompanyId,
        bth.budgetmodelid                 AS BudgetModel,       -- map to DimScenario.VersionCode
        CAST(btl.[date] AS date)          AS BudgetDate,
        btl.ledgerdimension               AS LedgerDimensionRecId,
        btl.accountingcurrencyamount      AS AmountLC,          -- GL sign (expense +) (verify per type)
        st.LocalizedLabel                 AS TransactionStatus,
        tt.LocalizedLabel                 AS BudgetTransactionType
FROM    budgettransactionline   btl
JOIN    budgettransactionheader bth ON bth.recid = btl.budgettransactionheader
JOIN    ledger                  l   ON l.recid   = bth.primaryledger
JOIN    companyinfo             ci  ON ci.recid  = l.primaryforlegalentity
LEFT JOIN globaloptionsetmetadata st ON st.EntityName = 'budgettransactionheader' AND st.OptionSetName = 'transactionstatus'
                                    AND st.[Option] = bth.transactionstatus AND st.LocalizedLabelLanguageCode = 1033
LEFT JOIN globaloptionsetmetadata tt ON tt.EntityName = 'budgettransactionheader' AND tt.OptionSetName = 'budgettransactiontype'
                                    AND tt.[Option] = bth.budgettransactiontype AND tt.LocalizedLabelLanguageCode = 1033
WHERE   COALESCE(btl.isdelete, 0) = 0 AND COALESCE(bth.isdelete, 0) = 0;
-- gold: keep TransactionStatus = 'Completed'; aggregate to month; decode LedgerDimension via §6;
-- convert at the ledger's BudgetExchangeRateType rates; BudgetModel (+ sub-model) -> VersionCode.
```

Revisions and transfers are separate transaction types: the "current budget" = original +
all completed revisions/transfers. Forecasts are usually *not* in the budget register; they
come from the planning database.

## 9. Fiscal calendar → period status

```sql
SELECT  UPPER(ci.dataarea)          AS CompanyId,
        CAST(fcp.startdate AS date) AS PeriodStart,
        CAST(fcp.enddate   AS date) AS PeriodEnd,
        fcy.name                    AS FiscalYearName,
        pt.LocalizedLabel           AS PeriodType,       -- Opening / Operating / Closing
        ps.LocalizedLabel           AS PeriodStatus      -- Open / On hold / Permanently closed
FROM    ledgerfiscalcalendarperiod lfcp
JOIN    fiscalcalendarperiod fcp ON fcp.recid = lfcp.fiscalcalendarperiod
JOIN    fiscalcalendaryear   fcy ON fcy.recid = fcp.fiscalcalendaryear
JOIN    ledger               l   ON l.recid   = lfcp.ledger
JOIN    companyinfo          ci  ON ci.recid  = l.primaryforlegalentity
LEFT JOIN globaloptionsetmetadata pt ON pt.EntityName = 'fiscalcalendarperiod' AND pt.OptionSetName = 'type'
                                    AND pt.[Option] = fcp.type AND pt.LocalizedLabelLanguageCode = 1033
LEFT JOIN globaloptionsetmetadata ps ON ps.EntityName = 'ledgerfiscalcalendarperiod' AND ps.OptionSetName = 'status'
                                    AND ps.[Option] = lfcp.status AND ps.LocalizedLabelLanguageCode = 1033
WHERE   COALESCE(lfcp.isdelete, 0) = 0 AND COALESCE(fcp.isdelete, 0) = 0
  AND   COALESCE(fcy.isdelete, 0) = 0;
```

`IsClosedPeriod` in `DimDate` is per group: a period counts as closed when **all**
consolidated companies have it on hold/closed (or per your close policy). If companies use
different fiscal calendars, map each to the group calendar in silver.

## 10. Currency and exchange rates

- `ExchangeRateCurrencyPair` (from/to currency, `ExchangeRateType`, display factor) +
  `ExchangeRate` (`ValidFrom`, `ValidTo`, rate). Rates are effective-dated, not monthly:
  build monthly AVERAGE (mean of daily or the ERP's average-rate type) and CLOSING (rate
  valid on the last day) in silver.
- **Stored value vs displayed rate**: F&O inherits AX's convention of storing rates per 100
  units and the pair's *display factor*; compare one converted voucher with the UI before
  trusting the arithmetic *(verify)*.
- `Ledger.ReportingCurrency` + `ReportingCurrencyAmount` can serve as group currency if the
  group configured one reporting currency consistently; otherwise convert in gold.
- Budget rates: the ledger's `BudgetExchangeRateType`.

## 11. Chart of accounts and report lines

- `MainAccount.Type` (P&L/BS/revenue/expense/total…, decode via labels) → `AccountType`,
  `PLSign = -1` for P&L accounts.
- `MainAccountCategory` → a first grouping level.
- Report layout: F&O Financial reports (Management Reporter) row definitions live outside the
  standard export *(verify for your setup)*; most projects maintain the report-line mapping as
  a governed table (account ranges per line) in the planning DB or a seed file, expanded with
  the range SQL in [tsql-scripts.md](../../sql-reporting-backend/references/tsql-scripts.md)
  §7.

## 12. Sales and supply-chain facts

| Fact | Tables | Grain / notes |
|---|---|---|
| Invoiced sales | `CustInvoiceJour`, `CustInvoiceTrans` | invoice line; `LineAmountMST` in accounting currency; `DataAreaId` |
| Customers | `CustTable` + `DirPartyTable` | `(DataAreaId, AccountNum)` |
| Products | `InventTable`, `EcoResProduct`, `EcoResProductTranslation` | shared products vs released per company |
| Inventory value | `InventTrans`, `InventSum` (snapshot) | stock measure → periodic snapshot in gold |
| Purchasing | `VendInvoiceJour`, `VendInvoiceTrans`, `PurchLine` | |

IBCS use: sales by product/customer (structure), sales volume × price variance analyses;
inventory as stock measure (growth waterfall).

## 13. Pitfalls checklist

- [ ] `IsDelete` filtered in every silver query.
- [ ] Company via Ledger → CompanyInfo; `DataAreaId` upper-cased.
- [ ] Posting layer Current only; Opening/Closing periods excluded from monthly P&L.
- [ ] Financial dimensions decoded once into a wide table, not by string splitting.
- [ ] Enum labels joined with an explicit language; integers kept as keys.
- [ ] Derived tables joined to base tables (`CompanyInfo` name from `DirPartyTable`).
- [ ] Main account keyed by (chart of accounts, MainAccountId).
- [ ] Exchange-rate storage factor verified against the UI.
- [ ] Budget register: Completed only, revisions included, versions mapped.
- [ ] Reconciliation: Σ AC per company/month = trial balance (or `GeneralLedgerBalance*`).
- [ ] Nothing reads Export to Data Lake any more (end of service **30 Nov 2026**).
