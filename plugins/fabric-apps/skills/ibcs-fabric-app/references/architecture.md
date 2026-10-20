# Architecture: where a Fabric App fits

Product facts as of 2026-10; Fabric changes monthly, so re-check Microsoft Learn before relying on
a status.

## 1. "Fabric app" means one of four things

| Name | What it is | Status (as of 2026-10) | Use for reporting |
|---|---|---|---|
| **Org app** (item `OrgApp`, child `OrgAppAudience`) | Packages existing items (reports, paginated reports, Fabric Apps, notebooks, maps, real-time dashboards) with navigation, theme and audiences | GA; audiences GA since July 2026 | The default way to ship a reporting product |
| **Workspace app** (formerly "Power BI app") | One versioned app per workspace | GA, legacy but supported; not auto-migrated | Keep existing ones; don't start new ones |
| **Fabric App** (built with the Fabric Apps SDK / Rayfin CLI) | Code-first TypeScript web app hosted by Fabric: static hosting, generated API, SQL database, Entra sign-in, connectors to semantic models, lakehouses and warehouses | Preview since June 2026 | Fully custom IBCS pages on top of semantic models, shipped inside an org app |
| **Apps in Power BI** (agentic app creation) | Natural-language app generation from a semantic model, built on Fabric Apps | Announced 2026-09 | Prototypes; expect it to emit Fabric Apps |

Adjacent: translytical task flows + user data functions (writeback), Power BI Embedded
(app-owns-data for external users), template apps.

## 2. Choose the rendering route

| | A. Embed Power BI | B. Native charts on the semantic model | C. Hybrid |
|---|---|---|---|
| IBCS rendering | Power BI (theme, SVG measures, Deneb, certified custom visuals) | Your chart layer (`ibcs-web-charts` contract) | Statement tables native; drill via embedded report |
| Data access | Embed token; RLS through effective identity | DAX via the Fabric Apps semantic-model connector (delegated), `executeQueries` REST or XMLA from a back end | both |
| Strengths | One implementation for the service and the web; export and subscriptions; no chart code | Pixel-level IBCS (hatching, pins, one scale across charts, scenario axes), phone-first layouts, print control | Best of both |
| Weak spots | Iframe UX; theming limited to the report; third-party visual licences for embedded viewers are vendor-specific | You own notation, tests and accessibility; must reproduce format strings and sign logic | Two stacks |

A Fabric App is route **B** hosted by Fabric. Whatever the route, **compute scenarios and
variances in the semantic model** (calculation group / functions) and send *wide* rows (period,
line, AC, PY, PL, FC, ΔPY, ΔPY%, impact, isForecast) so the web and Power BI can never disagree on a
variance.

For Power BI reports, use the cheapest layer that works: theme, then core visuals with formatting,
then SVG measures, then Deneb (see the `ibcs-power-bi` plugin).

## 3. What changes per host

- **Org apps / workspaces**: everything in Power BI works; custom visuals must be allowed by the
  tenant (organisational visuals or AppSource policy).
- **Embedded (app owns data)**: core visuals, SVG measures and Deneb render as in the service;
  generate embed tokens server-side only.
- **Fabric Apps / custom web**: you render IBCS yourself from DAX results. The data-app template
  has no IBCS primitives; add them per the `ibcs-web-charts` contract.

## 4. Recommended setup for business reporting

1. One certified semantic model per domain (TMDL in Git), RLS via Entra groups.
2. Standard reports: Power BI reports with an IBCS theme + SVG/Deneb; paginated reports for
   statement-style packs.
3. Distribution: one org app per audience family; audiences instead of copies; dev/test/prod
   workspaces because org-app saves are live.
4. Custom IBCS views beyond what Power BI visuals can do (bridges, integrated variance tables,
   small multiples with one scale): a Fabric App reading the model via the delegated connector,
   included in the same org app.
5. Comments and writeback: translytical task flows or a Fabric App data entity in a SQL database.
6. External customers without Entra accounts: Power BI Embedded (app owns data), not org apps or
   Fabric Apps. Fabric Apps can expose entities anonymously (tenant setting, as of 2026-10), but the
   semantic-model connector needs a signed-in user and anonymous access must never carry report data.
