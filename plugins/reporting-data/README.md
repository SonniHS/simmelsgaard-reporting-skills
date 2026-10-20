# reporting-data

The data behind reporting that follows the IBCS® Standards. `semantic-model-ibcs` designs and
reviews Power BI / Fabric semantic models for finance reporting: a Scenario dimension (AC, BU,
PL, FC versions, PY derived), fiscal date table, calculation groups for scenarios and signed
variances (ΔPY, ΔBU, ΔPY% with N/A for non-positive references, pp for ratios), polarity for
good/bad colouring, report lines for P&L tables and calculation waterfalls, unit scaling, RLS/OLS,
Direct Lake vs Import, and the exact DAX query each IBCS chart or table needs.
`sql-reporting-backend` builds the SQL gold layer that model reads, portable across Fabric
Warehouse, Lakehouse, SQL database in Fabric, Azure SQL and SQL Server, with a bundled core star
(DDL, date dimension, platform scripts, load checks). `dynamics-erp-reporting` gets Dynamics 365
Finance & Operations, Business Central and Dataverse/CE data into Fabric and maps it to that star,
including the move off Export to Data Lake before 30 November 2026. Group currency, fiscal year
and locale are settings you choose; examples use EUR and en-US. Product facts are dated
(as of 2026-10).

## Install

```
/plugin marketplace add SonniHS/simmelsgaard-skills
/plugin install reporting-data@simmelsgaard-skills
```

## Skills and agents

- `semantic-model-ibcs` (skill) — IBCS-ready semantic model design, TMDL reference model, DAX pattern library and the per-chart/table visual data contract.
- `sql-reporting-backend` (skill) — gold-layer contract, platform-tagged T-SQL (scenarios, phasing, SCD2, FX, hierarchies, bridges, monthly facts), platform cheat sheet, bundled SQL in `assets/sql/`.
- `dynamics-erp-reporting` (skill) — routes into Fabric, F&O / BC / Dataverse decoding, source-to-gold mapping and reconciliation.
- `semantic-model-architect` (agent) — designs, builds and reviews IBCS semantic models and their TMDL.
- `sql-backend-engineer` (agent) — writes and reviews portable gold-layer SQL with load checks.
- `dynamics-data-specialist` (agent) — plans ERP routes and writes silver/gold SQL that reconciles to the ERP.

## Examples

- "Design the semantic model for our group P&L with AC, BU and two forecast versions; Direct Lake on our Fabric Warehouse."
- "Add ΔFC and ΔFC% to the Scenario Analysis calc group and make ratio measures show pp."
- "Which DAX query does a variance table by entity need, and how should the app format the results?"
- "Port this recursive-CTE account hierarchy to Fabric Warehouse and add load checks."
- "We still read F&O data from Export to Data Lake. Plan the move to Link to Fabric and decode LedgerDimension into cost centre and department."

## Works with

- `ibcs` — the `ibcs-notation` skill (notation and design tokens behind the colours and
  scenario fills the model feeds), `ibcs-composition` (pages and titles), `ibcs-web-charts`
  (web charts that consume the visual data contract).
- `ibcs-power-bi` — the `ibcs-deneb` skill for Power BI visuals bound to this model.
- `fabric-apps` — the `ibcs-fabric-app` skill for Fabric Apps that query this model.
- Upstream tools: Microsoft Learn (authority for Power BI, Fabric and Dynamics 365 behaviour and
  schema); Microsoft's Fabric skills and the Fabric CLI (<https://github.com/microsoft/fabric-cli>);
  Tabular Editor and TMDL/PBIP tooling for model files; Microsoft's Dataverse tooling for live
  environment inspection.

## Licence

Prose (SKILL.md, references, agents, README) is shared under CC BY-SA 4.0; code and data (the SQL
in `assets/`) under the MIT License. See NOTICE, LICENSE-CC-BY-SA-4.0 and LICENSE-MIT in this
plugin.

Follows the IBCS® Standards; IBCS® is a registered trademark of IBCS Institute. Not affiliated
with or certified by IBCS Institute. Microsoft, Fabric, Power BI and Dynamics 365 are trademarks
of the Microsoft group of companies.
