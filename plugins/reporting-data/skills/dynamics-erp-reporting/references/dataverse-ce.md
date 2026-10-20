# Dataverse apps (Sales, Customer Service, Field Service, Project Operations) → IBCS star

Status: October 2026. Authority: Microsoft Learn (Power Apps / Dataverse):

- Link to Fabric: https://learn.microsoft.com/power-apps/maker/data-platform/fabric-link-to-data-platform
- Choice labels in Synapse Link / Link to Fabric: https://learn.microsoft.com/power-apps/maker/data-platform/azure-synapse-link-choice-labels
- Date/time column behaviour: https://learn.microsoft.com/power-apps/maker/data-platform/behavior-format-date-time-field
- Multi-select choices: https://learn.microsoft.com/power-apps/developer/data-platform/multi-select-picklist

Interactive Dataverse work (connect, query records, inspect metadata, security roles) is out
of scope here; this file covers the analytics pipeline only.

## Route: Link to Fabric

- Default for analytics: every table with *Track changes* is selected (deselect what you
  don't need; storage counts toward Dataverse capacity). Fabric gets a Lakehouse with
  shortcuts and a SQL endpoint. **No default semantic model** is created any more (Microsoft
  decoupled the old ones in 2025; if one is left, don't publish it); build your own gold and
  model.
- Alternatives: Azure Synapse Link to own storage; Dataverse connector / TDS endpoint
  (Import) for small models. Data Export Service is long retired.

## Labels

Choice/option-set labels: `OptionsetMetadata` (local), `GlobalOptionsetMetadata` (global),
`StateMetadata` (`statecode`), `StatusMetadata` (`statuscode`); join on `EntityName`,
`OptionSetName`, `Option`, filter `LocalizedLabelLanguageCode` (the LCID of your report
language, e.g. 1033 for en-US, 1031 for de-DE).

```sql
DECLARE @Lcid int = 1033;   -- report language
SELECT o.opportunityid, o.name, sm.LocalizedLabel AS StateLabel, st.LocalizedLabel AS StatusLabel
FROM   opportunity o
LEFT JOIN statemetadata  sm ON sm.EntityName = 'opportunity' AND sm.[State]  = o.statecode  AND sm.LocalizedLabelLanguageCode = @Lcid
LEFT JOIN statusmetadata st ON st.EntityName = 'opportunity' AND st.[Status] = o.statuscode AND st.LocalizedLabelLanguageCode = @Lcid
WHERE  COALESCE(o.isdelete, 0) = 0;
```

(Column names `State`/`Status` in the metadata tables: *verify in your export*.)

## Data rules

| Topic | Rule |
|---|---|
| Keys | GUID primary keys: map to int surrogates in gold (Direct Lake can't load GUIDs) |
| Deletes | `isdelete` flag in Link to Fabric; filter in silver |
| Currency | money fields have `_base` twins converted at the **record's** `exchangerate` at save time, not period rates: for group reporting convert transaction-currency values with the finance rate table |
| Time | by column behaviour: *User local* = UTC → convert to the business time zone before deriving the date; *Date only* / *Time zone independent* are **not** UTC-shifted → don't convert (read `DateTimeBehavior` from metadata) |
| Polymorphic lookups | `customerid` (+ `customeridtype`: account/contact), `ownerid` (user/team): resolve in silver |
| Multi-select choices | separator depends on the path (Web API: commas; formatted labels: semicolons; Link output observed `;`, unverified) — check a sample, then split in silver into a bridge |
| History | Dataverse keeps current state only (auditing aside) |

## Pipeline facts need snapshots

`opportunity` (`estimatedvalue`, `estimatedclosedate`, `closeprobability`, `statecode`,
`actualvalue`, `actualclosedate`) is a current-state table. IBCS time series of the pipeline
("open pipeline AC vs PY by month") need a **periodic snapshot fact** written by the gold load
at each month end:

```sql
-- [portable] gold.FactPipelineSnapshot, appended once per month end
DECLARE @MonthEnd date = EOMONTH(GETDATE(), -1);
DECLARE @GroupCurrency varchar(3) = 'EUR';
INSERT INTO gold.FactPipelineSnapshot (SnapshotDate, OpportunityKey, CustomerKey, OwnerKey,
                                       EstimatedCloseMonth, StageCode, EstimatedValueGC, WeightedValueGC)
SELECT  @MonthEnd, o.OpportunityKey, o.CustomerKey, o.OwnerKey,
        DATEFROMPARTS(YEAR(o.EstimatedCloseDate), MONTH(o.EstimatedCloseDate), 1),
        o.StageCode,
        o.EstimatedValueTC * r.Rate,
        o.EstimatedValueTC * r.Rate * o.CloseProbability / 100.0
FROM    silver.crm_opportunity o
JOIN    gold.FxRate r ON r.FromCurrency = o.CurrencyCode AND r.ToCurrency = @GroupCurrency
                     AND r.RateType = 'CLOSING' AND r.VersionCode = 'AC'
                     AND r.MonthStart = DATEFROMPARTS(YEAR(@MonthEnd), MONTH(@MonthEnd), 1)
WHERE   o.StateLabel = 'Open';
```

Snapshot facts are **stock** measures (not additive over time): in the model use
`LASTNONBLANK`-style month-end logic, and in IBCS charts a growth waterfall for movements.
Won/lost revenue (`actualvalue`, `actualclosedate`) is a flow measure and can join the monthly
finance star as a separate fact on the same Date/Entity/Customer dimensions.

## Gold mapping

| Gold object | Dataverse source |
|---|---|
| DimCustomer | `account` (+ `contact` for B2C), resolved from `customerid` |
| DimOwner / sales org | `systemuser`, `team`, `businessunit` |
| DimProduct | `product`, `productpricelevel` (align codes with ERP items) |
| FactPipelineSnapshot | `opportunity`, `opportunityproduct` |
| FactOrders / FactInvoices (if CRM-side) | `salesorder`, `salesorderdetail`, `invoice`, `invoicedetail` |
| FactCases | `incident` (+ SLA KPIs) |
| Project Operations | `msdyn_project`, `msdyn_actual` (actuals), with F&O integration for financials |
