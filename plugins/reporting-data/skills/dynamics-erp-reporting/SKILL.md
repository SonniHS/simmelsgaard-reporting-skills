---
name: dynamics-erp-reporting
description: >
  Gets finance, supply-chain and sales data from Dynamics 365 Finance & Operations, Business
  Central and Dataverse/CE apps into Microsoft Fabric and into an IBCS-ready star schema (AC/BU/FC
  scenarios, report lines, currencies, fiscal periods); use it whenever ERP or CRM data from
  Dynamics must reach a lakehouse, warehouse or semantic model, or whenever someone mentions
  GeneralJournalAccountEntry, G/L Entry, DAVC, Dimension Set ID, Link to Fabric, bc2adls or Export
  to Data Lake. Covers the routes (Link to Fabric, Azure Synapse Link, BC bc2adls/open mirroring
  and the announced native BC mirroring), the end of service of Export to Data Lake and how to
  migrate off it, key tables, financial dimension and Dimension Set decoding, enum labels,
  DataAreaId/company resolution, closing periods, exchange rates, budget register, source-to-gold
  mapping and reconciliation.
---

# Dynamics ERP → Fabric → IBCS star

> **Export to Data Lake:** Export to Azure Data Lake (F&O, LCS add-in) was retired on 1 Nov 2024
> and **reaches end of service on 30 November 2026, with no extensions** (Microsoft Learn,
> checked 2026-10); from then on nothing new or changed is exported. A pipeline still on it
> must move to **Link to Fabric** (low-latency sync) or Azure Synapse Link.
> Migration checklist: [references/fno.md](references/fno.md) §1.

This skill is about the *analytics pipeline*: routes into Fabric, decoding ERP structures in
silver, and mapping to the gold star that
[sql-reporting-backend](../sql-reporting-backend/SKILL.md) defines and
[semantic-model-ibcs](../semantic-model-ibcs/SKILL.md) models. Table and field names are
Microsoft's public schema; the authority is Microsoft Learn (Dynamics 365 Finance, Business
Central and Power Apps / Dataverse documentation). Use other tools for:

| Need | Where |
|---|---|
| Interactive Dataverse access: connect, query records, inspect tables/columns, security roles | Microsoft's Dataverse skills/MCP server, if installed; Web API / TDS endpoint |
| F&O X++: custom tables, data entities, change tracking, deployable packages | an X++ skill, if installed; Learn F&O developer docs |
| Lakehouse notebooks, materialized lake views, medallion layout | Microsoft's Fabric skills (`fabric-skills@fabric-collection`, https://github.com/microsoft/skills-for-fabric) or the Fabric CLI |
| Gold DDL, SCD2, FX, hierarchy SQL, load checks | [sql-reporting-backend](../sql-reporting-backend/SKILL.md) |
| Semantic model on top | [semantic-model-ibcs](../semantic-model-ibcs/SKILL.md) |

## Routes

Status as of 2026-10.

| Source | Recommended | Alternatives | Ending / legacy |
|---|---|---|---|
| **F&O** | **Link to Fabric**, F&O **tables** selected explicitly, low-latency sync | Azure Synapse Link to own ADLS Gen2 (Delta/CSV) | **Export to Data Lake: end of service on 30 Nov 2026; move off it.** BYOD legacy for analytics; virtual entities not for bulk |
| **Business Central** | **bc2adls** (community fork) → Lakehouse or **open mirroring**; partner open-mirroring tools | API v2.0 / custom API pages → pipelines; Power BI BC connector for one small company | Microsoft's original bc2adls repo archived. **Native BC mirroring was announced in late Sept 2026; not yet documented on Learn at the time of writing: treat as unverified preview** |
| **Dataverse / CE** | **Link to Fabric** (all *Track changes* tables, no copy) | Synapse Link; TDS endpoint/connector for small Import models | Data Export Service retired |

Link to Fabric prerequisites that bite: Fabric capacity in the **same region** as the
Dataverse environment; the replica counts toward **Dataverse capacity**; relinking for
low-latency sync triggers a full initial sync; database restores require re-adding F&O
tables. Never point the semantic model at the shortcuts/mirrors: they're bronze, not tuned
for Direct Lake, and carry deleted rows. Learn:
https://learn.microsoft.com/power-apps/maker/data-platform/fabric-link-to-data-platform

## Workflow

1. **Inventory**: companies/environments, fiscal calendars, currencies, charts of accounts,
   financial dimensions in use, budget models/names, planning source, the report language
   for labels, and who may see which company (RLS source). Note any consumer still on Export
   to Data Lake.
2. **Land bronze** with the route above; select only needed tables (capacity cost).
3. **Silver per source** (one notebook/MLV set per domain): filter deletes, decode enums in
   one language, resolve company, upper-case company codes, build wide dimension tables
   (F&O DAVC → `fno_ledger_dimension`; BC Dimension Set ID → `DimDimensionSet`), monthly FX
   (average/closing), period status and closing flags. BC: a mapping view per table so the
   export tool's column naming is isolated.
4. **Gold** ([references/source-to-gold.md](references/source-to-gold.md)): conformed entity,
   group CoA mapping, report lines + bridge, SCD2 org dimensions, `FactGlDetail`, monthly
   `FactFinance` (AC + BU from the ERP, FC/PL from the planning DB), security mapping. SQL:
   account ranges and BC Totaling → report-line bridge in
   [tsql-scripts.md §7](../sql-reporting-backend/references/tsql-scripts.md#7-range-totals--report-line-bridge-portable);
   GL lines → monthly fact with FX in
   [tsql-scripts.md §8](../sql-reporting-backend/references/tsql-scripts.md#8-monthly-fact-from-gl-detail-portable).
5. **Reconcile** before framing: Σ AC = trial balance per company/month; BU = budget
   register; no unmapped accounts; freshness per source.
6. **Frame/refresh** the semantic model from the pipeline; automatic Direct Lake updates off.

## ERP traps that break IBCS numbers

| Trap | Effect if missed | Fix (where) |
|---|---|---|
| Deleted rows kept with `IsDelete` (Link to Fabric) | double counting | filter in every silver query |
| F&O GL has no `DataAreaId` | wrong/no company | Ledger → CompanyInfo ([fno.md](references/fno.md) §4) |
| F&O Opening/Closing periods, BC closing dates | December P&L shows the result reversed | exclude from monthly P&L ([fno.md](references/fno.md) §7, [business-central.md](references/business-central.md) §6) |
| F&O posting layers | other-GAAP adjustments in management P&L | Current layer only |
| Splitting F&O `DisplayValue` by delimiter | dimensions shifted per account structure | wide DAVC decode ([fno.md](references/fno.md) §6) |
| BC per-company tables (`DataPerCompany = true`), `Entry No.` per company | key collisions; shared (`false`) tables duplicated | key on (Company, …); don't fan out shared tables |
| BC Totaling formulas | subtotals missing or double | expand ranges into the bridge |
| Enum integers hard-coded | silent errors after updates/languages | `GlobalOptionsetMetadata` labels, integer kept as key |
| Derived F&O tables missing base fields | blank names (`CompanyInfo.Name`) | join base table on `RecId` |
| Exchange-rate storage factors | rates off by ×100 | verify one voucher against the UI ([fno.md](references/fno.md) §10) |
| CE `_base` money at record rates | FX effects inconsistent with finance | convert with finance rates |
| CE current-state tables | no pipeline history | monthly snapshot fact ([dataverse-ce.md](references/dataverse-ce.md)) |
| GUID keys | Direct Lake can't load them | int surrogates in gold |

## Unverified items (check before relying on them)

- Native BC → Fabric mirroring: scope, setup page, column naming and GA timing (community
  sources only, Sept/Oct 2026).
- bc2adls column naming `<Field>-<No>` and `$Company`: depends on the fork/version.
- F&O enum label strings (`Current`, `Operating`, `Completed`) and `GlobalOptionsetMetadata`
  `EntityName`/`OptionSetName` casing; F&O exchange-rate storage factor; whether DAVC carries
  denormalised dimension columns in your version; availability of Financial reports row
  definitions and BC account schedule lines in the export.
- BC closing-date representation in exports and the source code your environment assigns to the Close Income Statement batch job
  (Source Code Setup).
- CE metadata table column names (`State`, `Status`) in Link to Fabric.

## References

- [references/fno.md](references/fno.md) — Link to Fabric and the Export to Data Lake
  migration checklist, key tables, company/posting layer/periods, enum and financial-dimension
  decoding, GL/budget/period/FX SQL, CoA and report lines, sales/SCM tables, pitfalls.
- [references/business-central.md](references/business-central.md) — routes and status,
  silver mapping views, key tables, companies, Dimension Set decoding, closing dates, budgets,
  accounting periods, FX, Totaling/account schedules, sales/inventory, pitfalls.
- [references/dataverse-ce.md](references/dataverse-ce.md) — Link to Fabric for CE, labels,
  GUIDs, currency, time zones, polymorphic lookups, pipeline snapshot fact, gold mapping.
- [references/source-to-gold.md](references/source-to-gold.md) — medallion flow and
  orchestration, mapping table per gold object, conforming several ERPs, scenario mapping,
  sign/closing/currency per source, reconciliation per source.
