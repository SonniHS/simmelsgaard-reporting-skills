---
name: ibcs-fabric-app
description: >
  Builds Microsoft Fabric Apps (Fabric Apps SDK / Rayfin CLI, React + TypeScript) that follow the
  IBCS® Standards, end to end; use it whenever someone builds, extends, reviews or deploys a
  Fabric App or other React data app for reporting, dashboards, variance analysis or management
  information, including "make a Fabric app from this semantic model / visual spec". The app
  queries a Power BI semantic model with DAX as the signed-in user (RLS/OLS apply). Covers page
  patterns (overview → drill → detail; period, scenario and comparison selectors that surface in
  the IBCS title lines), one DAX query per visual grain wired to chart components,
  loading/empty/error states, RLS/OLS testing, performance, deployment with `rayfin up` and GitHub
  Actions, and packaging into an org app. Replaces the data-app template's design guidance with
  IBCS rules and works alongside Microsoft's Rayfin skills, which stay authoritative for SDK and
  CLI mechanics.
---

# IBCS Fabric Apps

**Division of labour.** Microsoft's `rayfin` plugin (its `rayfin-getting-started` router), the
template's `AGENTS.md` and the in-project skills that the scaffold installs are **authoritative for
SDK/CLI mechanics**: project layout, `fabric.yaml` / `rayfin.yml`, connectors, the client and
query-hook API, `.dax` query files, the template's visual and grid components, schema discovery and
DAX authoring. The installed skills vary by template and version: `create-rayfin` 1.36.2 with
`--template dataapp` (2026-10) put `app-design`, `dax-authoring`, `fabric-cli`, `fabric-sdk`,
`query-design`, `rayfin`, `rayfin-connectors`, `rayfin-functions`, `schema-discovery` and `visuals`
under `.agents/skills/` (no browser-validation skill, although Microsoft Learn describes one). List
that folder instead of assuming names, and read the Rayfin docs shipped in `node_modules` as the
in-project `rayfin` skill says. Never answer Rayfin API questions from memory.

**This skill owns** the IBCS presentation, the page patterns, the DAX → chart data contract and
the operational decisions. Companion skills:

- the `ibcs-web-charts` skill (plugin `ibcs`): the chart behaviour contract (scenario columns,
  variance tiers, structure bars, waterfalls, small multiples, tables), formatting, one scale per
  unit, phone and print. Implement or choose a chart library that meets that contract; this skill
  does not ship one; there is no shipped IBCS chart library yet, see
  [references/chart-layer.md](references/chart-layer.md) for the module layout that worked.
- the `ibcs-composition` skill (plugin `ibcs`): the visual spec per page.
- the `ibcs-notation` and `ibcs-review` skills (plugin `ibcs`): notation and the review checklist.
- the `semantic-model-ibcs` skill (plugin `reporting-data`): the IBCS-ready model and per-card DAX.
- [fabric-org-apps](../fabric-org-apps/SKILL.md): distribution through an org app.

Background: [references/architecture.md](references/architecture.md) (embed vs native vs hybrid,
where Fabric Apps fit).

## 0. Override: the template's design guidance does not apply

The data-app template ships design guidance that conflicts with IBCS and with "no third parties on
page load": the `app-design` skill (its `AGENTS.md` says to load it before presentation code), the
palette and chart rules of the `visuals` skill, a light/dark theme context and dark CSS variables
(names as of 2026-10). **This skill replaces all of them** for charts and page design; follow this
section instead and say so in your summary.

| Template guidance | IBCS app does instead | Rule |
|---|---|---|
| Pick a "bold, distinctive" tone and signature detail | One house notation for every page and app of the organisation; no decoration | IBCS v2.0, SI 1–2, UN |
| Characterful heading font from a CDN `<link>` | Token font stack (`system-ui, "Segoe UI", …`); a brand font only self-hosted (`@font-face` with a local file) via your `ibcs-tokens.overrides.json` | SI 2.3; privacy |
| Customise primary colour, radius, colourful cards | Chart colours only from the IBCS token file (default in the `ibcs-notation` skill, plugin `ibcs`, plus your overrides); scenarios in grey patterns; colour = impact or highlight only | UN 3.2, UN 4.1, SI 2.2 |
| Vary card spans, avoid "spreadsheet" grids, layered effects | Grid from the visual spec, equal panels where comparison matters; no shadows, frames or gradients on marks. Cards as UI chrome are the default (house style, ours, not stated by IBCS): white surface, radius 8, 1 px ring at 10 % ink, soft shadow 2 / 4 px at 12 % ink, canvas 5 % ink; square cards are the option; every content rule holds inside the card: [references/report-shell.md](references/report-shell.md) §9 | CO 2, CH 4, SI 2.1 |
| Light/dark toggle | No dark charts. A dark shell may surround a white "paper" surface; default and print are white | SI 1.2 |
| CSS theme colours drive charts | Never let a CSS theme recolour scenario or variance marks; pass token colours explicitly | UN |
| Skeletons and destructive banners in brand style | States per §5 (title block stays, neutral text, no red banners: red means bad variance) | UN 4.1 |
| Icon set and component-library tokens | Fine for **controls** (selectors, menus); never icons in data areas, no traffic lights | SI 1, SI 1.1, EX 2.5 |
| `visuals` skill: Vega-Lite palettes (`data-palette-presets.json`), categorical colours, its default theme | No palette on charts: scenario notation and impact colours from tokens. A Vega-Lite visual you keep gets token colours in its spec | UN 3.2, UN 4.1 |
| Theme context (`useThemeContext()` with `isDark`/`toggleTheme`) and `.dark` CSS variables in `global.css` | Pin the theme to light: keep the provider (template components such as the data grid require a `theme`), drop the toggle and the `.dark` block | SI 1.2 |
| `validate:visual` before UX work | Still run it for Vega-Lite factories you keep; custom SVG charts are verified as in [references/chart-layer.md](references/chart-layer.md) | — |

Keep what is mechanical: the control components, the query factories, the in-portal validation
flow, spacing tokens for non-data UI.

## 1. Prerequisites check

| Item | Requirement | If missing |
|---|---|---|
| Visual spec | One spec per page (`ibcs-composition` format): message, title lines, visuals, data shape, scale groups, interactions | Ask for it or hand the brief to the `ibcs-visual-designer` agent (plugin `ibcs`); don't invent the page |
| Capacity | As of 2026-10: workspace on **Fabric capacity (F2+, Trial OK)** in a region where Fabric Apps are available. Some regions are Power BI-only (e.g. Denmark East); put the app workspace on a capacity elsewhere, the semantic model may stay | Stop and tell the user |
| Tenant settings | As of 2026-10: **Fabric Apps (preview)**; **Semantic Model Execute Queries REST API**; for CI, service principals may use Fabric APIs | Fabric admin |
| Permissions | Author: Edit on the workspace, **Build + Read** on the model. Consumers: Run/interact on the app + model access. Microsoft sources disagreed in 2026-09/10 on whether Read alone is enough; grant **Build + Read** until a tenant test shows Read works. Not granted by the org app (§7) | Grant via Entra groups |
| Model | IBCS-ready: scenario/variance calculation group or explicit measures, impact (polarity), report lines, closed-period flag (`semantic-model-ibcs`) | Fix the model first; if it must not change, use query-scoped `DEFINE MEASURE` on the model's own measures and functions, flagged in the footnote ([queries-and-data.md](references/queries-and-data.md) §3a). The app never computes variances in TypeScript |
| Tooling | Node.js 20, 22 or 24 (the `create-rayfin` 1.36.2 engines range, 2026-10); Learn says "Node.js 20 or later" | Install a supported Node version |

## 2. Workflow

1. **Get into a project**: `npx @microsoft/create-rayfin@<version> <dir> --template dataapp`
   (pin the version you tested; `--list-templates` lists the others, as of 2026-10 `blankapp`,
   `dataapp`, `gettingstartedauth`, `todoapp`), or the getting-started router. Read the template's
   `AGENTS.md` and its in-project skills. Choose **one data path**: the scaffold's Fabric data client
   (`fabric.yaml`, portal-hosted proxy) or a Rayfin semantic-model connector with **delegated** auth
   (`rayfin.yml`); both run as the signed-in user, so RLS/OLS apply
   ([queries-and-data.md](references/queries-and-data.md) §0). Never use a stored identity to read
   data on a user's behalf, and never add mock data (the template forbids it).
2. **Install the IBCS layer**: a chart layer that meets the `ibcs-web-charts` contract (module
   layout: [references/chart-layer.md](references/chart-layer.md)), the token module and CSS
   generated from the IBCS token file, and the report shell (header row, filter bar, page frame,
   cards, footer: [references/report-shell.md](references/report-shell.md)). Remove the template's
   font links and dark-mode toggle (§0). Give each page one scale registry.
3. **Queries**: one `.dax` file per visual **grain** from the spec's data shape, adapted from the
   per-card DAX in `semantic-model-ibcs`; test each from the terminal before wiring it
   (`npx fabric-app-data query <alias> --file <file>`, no app item needed).
   Rules and the wiring pattern: [references/queries-and-data.md](references/queries-and-data.md).
4. **Pages**: compose from [references/app-patterns.md](references/app-patterns.md) inside the
   shell of [references/report-shell.md](references/report-shell.md) (its §11 is a worked recipe
   for a Key figures page): header (key
   message + title block with active filters in line 1 and period/scenarios in line 3), visuals in
   the spec's grid, footnote with sources and the data timestamp. Map each spec visual type to a
   chart role in `ibcs-web-charts` and each scale group to one unit key.
5. **States**: loading, empty, error, partial and N/A per §5.
6. **Verify**: typecheck + unit tests (query factories, adapters, formatters, chart layout
   functions); `validate:visual` for Vega-Lite factories only. In-portal run: the queries need a
   deployed app item (`npx rayfin up` once to a dev workspace, only with the owner's approval),
   then open the item in the portal with `&devUri=http://localhost:<port>` while `npm run dev` runs
   (one pinned port, also in `allowedRedirectUris`; never `rayfin dev`); bare localhost cannot
   authenticate. Before any deployment, check layout with a test-only harness on captured fixtures
   ([references/chart-layer.md](references/chart-layer.md)). Screenshots at 390 px, ≈ 1050 px (portal content width) and 1280 px with device-width emulation (recipe in
   the `ibcs-web-charts` testing reference); `ibcs-review` on each page; the page quality rubric
   in [references/page-quality.md](references/page-quality.md); RLS test matrix (§4).
7. **Deploy only when the owner approves it in this task**
   ([references/deploy-and-operate.md](references/deploy-and-operate.md)); `--dry-run` counts too,
   it signs in and resolves the tenant target. Always `--workspace` + `--item-name`; production
   through CI. Users open the app item in the **portal**, not the static-hosting URL.
8. **Distribute** through an org app ([fabric-org-apps](../fabric-org-apps/SKILL.md)), granting
   semantic-model access separately.

## 3. Page and app patterns (summary)

- **Overview → drill → detail.** Entry page = message page (key message, one multi-tier time chart
  + one structure chart with variances); drill pages = one argument each (small multiples by
  entity, variance waterfall); detail = variance table or lookup grid.
- **Selectors** are IBCS concepts: reporting period (last closed month by default), period view,
  comparison (PL | PY | FC), entity filters. Every active selection appears in the title (filters
  → line 1; period and scenarios → line 3). Keep them in the URL so deep links, back button and
  bookmarks work. Hide controls in print.
- **Message text**: dynamic messages may only *detect* (template filled from measures);
  explanations come from governed commentary, otherwise mark the page `analysis`.
- Details, wireframe, period grammar and the URL contract: [references/app-patterns.md](references/app-patterns.md).

## 4. RLS / OLS testing

The connector runs DAX **as the signed-in user**, so the model's roles apply, and workspace
Admins, Members and Contributors see **everything** (RLS does not apply to them).

- Test with dedicated **test accounts** that only have app access + model access, one per role;
  never with the author's account, never by acting as a real user. "Test as role" / "View as" on
  the model checks the DAX side.
- Matrix per page: role × visual → expected rows and totals (from a reference query run as that
  role). Check totals, small-multiple panel count, the key message (must re-scope or hide), title
  line 1, drill targets, and OLS (the app shows "not available for your role", not an error dump).
- Shared scales and "Other" remainders are computed per user context; a restricted user gets
  different scales, which is correct.
- Never cache results across users: keep the SDK cache per client instance in the browser; no
  shared server cache of delegated results.

## 5. Loading, empty, error, N/A

| State | Show | Never |
|---|---|---|
| Loading | Title block + key-message placeholder, chart frame at its final height with a light grey skeleton, `aria-busy` | Spinners over the title; animated shimmer (SI 1.3) |
| Empty | Title stays; "No values for {who}, {when}" in secondary text; selectors stay usable | Zero-filled charts |
| Error | Neutral message by category: query → "This view is temporarily unavailable" (log the DAX error for developers); 401/403 → "You don't have access to this data"; 429 → retry after `Retry-After`; network → retry button | Red banners, raw DAX errors to users |
| Partial (one tier failed) | Render what succeeded, mark the failed tier; hide the page message if it depends on the failed query | Silent omission |
| N/A relative variance | No pin, label `N/A` | 0 % |
| Stale cache | Footnote shows the data timestamp; a Refresh control bypasses the cache | Hiding the as-of date |
| Selection changed, new query running | Loading state for the affected charts at once; the previous selection's rows are never drawn under the new title ([queries-and-data.md](references/queries-and-data.md) §0 "Results keyed by query") | Old rows under a new selection; a late answer to an old query overwriting the new one |
| No answer (timeout, about 20 s) | Error state; outside the portal frame: "Open this app from its item in the Fabric portal" ([queries-and-data.md](references/queries-and-data.md) §0) | Skeletons forever |

## 6. Performance (short)

Aggregate in DAX to the visual's grain; one query per grain; run a page's queries in parallel;
widen the grain for low-cardinality filters and filter client-side; reuse one client (and its
cache) across pages; bypass the cache only on explicit refresh; `TOPN` + remainder in DAX for long
structures. Budget: about 6–8 queries per page view. The executeQueries limits (as of 2026-10:
100,000 rows / 1,000,000 values per query, 120 query requests per minute per user) mean a page
that fans out per entity must batch. Details: [references/queries-and-data.md](references/queries-and-data.md) §4.

## 7. Distribution and ALM (short)

As of 2026-10, Fabric App items are **not** in Git integration or deployment pipelines: the repo is
the source, and `rayfin up` deploys code, schema and static content per environment (dev, test,
prod workspaces). Destructive schema changes need `--force`; keep it behind a manual, reviewed
workflow. Package for users in an **org app**; it grants access to the app item but **not** to its
related items, so grant semantic-model access to the same Entra groups
([fabric-org-apps](../fabric-org-apps/SKILL.md)).

## References

- [references/architecture.md](references/architecture.md): embed vs native vs hybrid; what changes between reports, org apps, embedded and Fabric Apps.
- [references/app-patterns.md](references/app-patterns.md): archetypes, grid, selectors and title wiring, period grammar, URL state, message sources, hub pages.
- [references/queries-and-data.md](references/queries-and-data.md): data paths and dev loop; spec → `.dax` → factory → adapter → chart; query-scoped measures; batching, caching, throttling, OLS, portal value shapes.
- [references/report-shell.md](references/report-shell.md): the frame around every page: header row, filter bar with "compare with", headline, KPI and chart cards, footer, layout tokens, breakpoints, state; recipe for a Key figures page from scratch.
- [references/chart-layer.md](references/chart-layer.md): module layout of an IBCS chart layer (tokens → scale registry → pure layout → SVG renderer) and the tests that replace `validate:visual`.
- [references/page-quality.md](references/page-quality.md): page quality rubric (value, proportions, both widths) and the shell checks.
- [references/deploy-and-operate.md](references/deploy-and-operate.md): environments, `rayfin up`, GitHub Actions, capacity/region/licensing, release checklist, monitoring, rollback.
