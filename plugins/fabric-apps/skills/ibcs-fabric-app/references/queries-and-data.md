# From visual spec to DAX to chart

Mechanics (file layout, factory signature, hook names, CLI) come from the in-project skills the
scaffold installed (as of 2026-10: `query-design`, `dax-authoring`, `fabric-sdk`, `fabric-cli`,
`rayfin-connectors`). The query text per IBCS card comes from the `semantic-model-ibcs` skill
(plugin `reporting-data`); the chart props from the data contract in the `ibcs-web-charts` skill
(plugin `ibcs`). This file is the glue.

## Contents
- [0. Data paths and the dev loop](#0-data-paths-and-the-dev-loop)
- [1. Mapping](#1-mapping)
- [2. Wiring pattern (per visual)](#2-wiring-pattern-per-visual)
- [3. Values the app must not compute](#3-values-the-app-must-not-compute)
- [3a. When the model must not change: query-scoped measures](#3a-when-the-model-must-not-change-query-scoped-measures)
- [4. Performance and throttling](#4-performance-and-throttling)
- [5. RLS/OLS-aware queries](#5-rlsols-aware-queries)
- [6. Portal value shapes (observed 2026-10)](#6-portal-value-shapes-observed-2026-10)

## 0. Data paths and the dev loop

Two ways to send DAX to a semantic model exist as of 2026-10. Pick **one** per app and never keep
both (Microsoft's data-app page says the same).

| | A. Fabric data client (what the `dataapp` scaffold generates) | B. Rayfin connector |
|---|---|---|
| Seen in | `create-rayfin` 1.36.2 `--template dataapp` (test, 2026-10) | Learn "Create an app connected to a semantic model" (2026-10); templates without `fabric.yaml` (`blankapp`, `todoapp`, `gettingstartedauth`) *(verify per template)* |
| Config | `fabric.yaml` (profiles → model aliases), `npx fabric-app-data generate -o src/fabric.generated.ts` | `connectors:` block in `rayfin/rayfin.yml` via `npx rayfin connector add --type fabric-semanticmodel … --operations executeQuery` (auth `delegated`) |
| Runtime | `@microsoft/fabric-app-data` `FabricClient` + `EmbedFabricApiProxy` (postMessage to the Fabric host): works **only inside the portal**. Opened on its static-hosting URL the app signs in but no query is ever sent and nothing errors (deployed test, 2026-10): users open the app item in the portal, and the app needs the load timeout below | `ConnectorsRayfinClient` + `fabricSemanticModel()`: `client.connectors.<name>.executeQuery({ query })`; connectors are cloud-only, so verify after `rayfin up` |
| Hook | template `useSemanticModelQuery({ connection, query })` | per the in-project `rayfin-connectors` skill |
| Read | in-project `fabric-cli`, `fabric-sdk` | in-project `rayfin-connectors`; `rayfin connector types --json` |

Both run the query as the signed-in user, so RLS/OLS apply, and both return
`{ status: "success", table }` or `{ status: "error", error: { category, message } }` without
throwing.

**Dev loop (path A, observed 2026-10).** A bare `http://localhost:<port>` cannot authenticate to
the model, so the page shows no data there.

1. Create the app item once: `npx rayfin up --workspace "<dev workspace>" --item-name "<app>"`.
   It is a deployment:
   only with the user's explicit approval in this task ([deploy-and-operate.md](deploy-and-operate.md) §1).
2. Start the **Vite-only** dev server, then open the app item in the Fabric portal and append
   `&devUri=http://localhost:<port>` to its URL. The portal hosts your local build and proxies the
   queries as you. Read the `scripts` in `package.json` first: in the `dataapp` template
   (`create-rayfin` 1.36.2, Microsoft's `samples/data-app/package.json`) `npm run dev` **is**
   `rayfin dev` and `dev:frontend` is plain `vite`. Run `npm run dev:frontend` or
   `npx vite --port <port> --strictPort`. `rayfin dev`, and any script that calls it or
   `rayfin up`, provisions resources in the tenant and needs the same approval as a deploy.
3. Without an app item (no tenant deployment yet), test queries only: `npx fabric-app-data query
   <alias> --file src/queries/<page>/<viz>.dax` (or `--query '<DAX>'`, `--limit 50`) runs the same
   SDK pipeline from the terminal as the developer.

**Prerequisite for any portal check: a browser signed in to the tenant that the agent can drive**
(a browser-automation tool attached to the user's session, or a persistent automation profile in
which the user signed in once). Never automate the sign-in. Without such a browser, do not claim
in-portal validation: report "portal check not run (no signed-in browser)", list the checks that
remain for the user (pages load, no error states, values match the terminal queries), and give the
exact item URL with `&devUri=…` to open.

**Debugging a portal-only failure (ours, 2026-10).** A query that passes in the terminal can still
fail in the portal (see the factory-output test in §2). The deployed app runs in nested
cross-origin frames, and its console was not readable from the portal tab with a browser tool, so:

1. Run the Vite-only dev server (`npm run dev:frontend`, never a script that runs `rayfin dev`)
   on the pinned port and open the app item with
   `&devUri=http://localhost:<port>`: the portal now frames your local build.
2. Chrome's Local Network Access check blocks a public site from framing `http://localhost`. A
   normal profile asks for local-network access: the user must allow it. An automated browser
   needs the flag that the `app-validation` skill describes (shipped in
   `node_modules/@microsoft/rayfin-cli/templates/data-app/.agents/skills/app-validation/` with CLI
   1.36.2, though the `dataapp` scaffold did not install it).
3. In dev builds only, show the raw error text under the user-facing error message
   (`{import.meta.env.DEV && <pre>{error.category}: {error.message}</pre>}`), so a screenshot can
   read it. Production builds keep the plain messages (SKILL.md §5).

**Port.** The scaffold's Vite default is 5173, and another dev server often holds it. Pick one
port per app and pin it in three places, or sign-in fails with a redirect error:
`server: { port: <port>, strictPort: true }` in `vite.config.ts` (fail instead of silently moving
to the next port), `http://localhost:<port>` under `services.auth.allowedRedirectUris` in
`rayfin/rayfin.yml`, and the `&devUri=` value. The redirect list reaches the tenant on the next
`rayfin up`.

**Client config.** The scaffold's `RayfinClient` sets `useProxy: false`. As of
`@microsoft/rayfin-client` 1.35 the option is deprecated and ignored (console warning
`RAYFIN_DEP_USE_PROXY`): routing depends only on `baseUrl` (`""` = same origin through a dev proxy,
an absolute URL = call the backend directly). Remove `useProxy` and keep `baseUrl`.

**Load timeout.** A query that never returns must not leave the page in skeletons forever (the
static-hosting URL case above, a portal frame that never answers). Give every page load a timeout
(about 20 s) that switches to the error state with "Open this app from its item in the Fabric
portal" when the page is not framed (`window.self === window.top`), and "This view is temporarily
unavailable" otherwise (SKILL.md §5).

**Results keyed by query.** The template's hook keeps its last `data` while a new query runs and
accepts answers in any order, so after a selection change the page shows the old selection's rows
for a moment, or for good if the old answer arrives last. Store each result together with the
query it answers, report loading until the answer to the current query arrives, drop late
answers, and put the timeout in the hook:

```ts
const key = `${connection}\u0000${query}`;
const [state, setState] = useState<{ key: string; data?: Result; error?: Error }>();
const current = useRef(key);
useLayoutEffect(() => { current.current = key; }, [key]);

useEffect(() => {
  let timer: ReturnType<typeof setTimeout> | undefined;
  const timeout = new Promise<never>((_, reject) => {
    timer = setTimeout(() => reject(new Error("timeout")), QUERY_TIMEOUT_MS);   // about 20 s
  });
  Promise.race([client.semanticModel(connection).query(query), timeout])
    .then((data) => { if (current.current === key) setState({ key, data }); })
    .catch((error) => { if (current.current === key) setState({ key, error }); })
    .finally(() => clearTimeout(timer));
}, [connection, query, key]);

const fresh = state?.key === key ? state : undefined;   // never the previous query's rows
return { data: fresh?.data, error: fresh?.error, isLoading: !fresh };
```

Unit-test it: change the query while the first one is pending, resolve the first one last, and
assert the hook reports loading and then the second result.

**No mock data.** The template's `AGENTS.md` forbids mock, fake or hard-coded data and in-memory
or local-storage copies. Ship no fixture or "offline" data mode in app code. Fixtures belong only
in unit tests, built from real query output with the real column names.

## 1. Mapping

| Visual spec field | Becomes |
|---|---|
| data grain + shape | one `.dax` file (one `EVALUATE`), with `ORDER BY` for stable output |
| time category | date-table columns: sort key + label, closed-period flag for AC&FC |
| scenarios / variances | `CALCULATE([Report Value], <scenario item> = "AC" \| "PL" \| "ΔPL" \| "ΔPL%")` columns (wide shape) |
| measure polarity | the model's impact column per variance, not a constant in TypeScript |
| top N | `TOPN` + "Other" remainder computed in DAX, with a row flag for the gap before the remainder |
| scale groups | one unit key per group in the page's scale registry |
| tiers | one chart per tier, same width, stacked in the spec's order |
| selective data labels | last-point labels or thinning |

## 2. Wiring pattern (per visual)

```
src/queries/sales-by-month.dax     // EVALUATE … (adapted from the per-card DAX)
src/queries/sales-by-month.ts      // query factory, per the in-project query-design skill
src/visuals/SalesByMonth.tsx       // hook → records → period rows → scenario column chart
```

**Factory shape.** The template's factories (`create-rayfin` 1.36.2 `dataapp`) return
`{ connection, query, columnMetadata, vegaLiteSpec }` and feed `toDataTable` and the template's
visual components. An IBCS factory returns `{ connection, query, columnKinds }` instead: no
Vega-Lite spec (the chart layer draws), and `columnKinds` declares each output column's kind for
`normalizeValue` (§6). Keep the template's shape only for a Vega-Lite visual you keep.

Illustrative only: take hook names and signatures from the in-project skills, and the chart props
from your implementation of the `ibcs-web-charts` contract.

```tsx
const scale = usePageScale("EUR");                                 // the page's scale registry: one unit key → scale factor + px per unit
const result = useSemanticModelQuery({ connection, query });      // queries never throw
const title = <TitleBlock what="Net sales" unit={scale.label} when={when} />;   // stays in every state (SKILL.md §5)
if (result.isLoading) return <Panel title={title}><ChartSkeleton height={180} /></Panel>;
if (result.error) return <Panel title={title}><ViewError error={result.error} /></Panel>;   // timeout or thrown error: SKILL.md §5 text
if (result.data?.status !== "success") return <Panel title={title}><ViewError error={result.data?.error} /></Panel>;
const records = toRecords(result.data.table);                     // bare column names, normalised values (§6)
const rows = toPeriodRows(records, { period: "MonthShort", ac: "AC", fc: "FC", pl: "PL", py: "PY",
                                     isClosed: "IsClosedPeriod" });
if (!rows.length) return <Panel title={title}><EmptyState who={who} when={when} /></Panel>;
scale.register(rows.flatMap((r) => [r.AC, r.FC, r.PL, r.PY]));   // every value the page shows in this unit
return <Panel title={title}>
         <ScenarioColumns data={rows} reference="PL" unit="EUR" factor={scale.factor} />
       </Panel>;
```

- Variance tiers come from the **same** query when the grain is the same (add ΔPL, ΔPL%, impact
  columns): one round trip, consistent numbers.
- Totals: additive values may be summed client-side from detail rows; ratios, distinct counts and
  Δ% of a total come from a separate summary query (one grain per file).
- Fill missing periods client-side from the period list; never `+ 0` in DAX.
- Test every `.dax` before wiring it: path A `npx fabric-app-data query <alias> --file <file>`;
  path B per the `rayfin-connectors` skill.
- Unit-test factories (parameters → query text) and adapters (fixture rows with the real column
  names → chart props).

**Selection substitution and the factory-output test.** A common factory keeps a valid default in
the `.dax` file and swaps tagged lines for the selection, e.g.
`VAR __Months = TREATAS ( { … }, 'Date'[Month] ) // @period` inside `DEFINE`. Match **only** the
tagged line, anchored, never `line.includes("// @period")`: a header comment such as
`// @period and @company lines are replaced …` also matches, the replacement `VAR` lands above
`DEFINE`, and the query fails with a DAX syntax error, in the portal only, because the terminal
test ran the raw file (seen 2026-10).

```ts
if (/^\s*VAR __Months\b.*\/\/ @period\s*$/.test(line)) return `    VAR __Months = ${months} // @period`;
```

- Test the **factory output**, not the `.dax` file. The factories import their `.dax` with Vite's
  `?raw`, so plain Node cannot load them: dump the queries from a vitest spec that is skipped by
  default, then run each dump against the model:

  ```ts
  // src/queries/dump.spec.ts — run with DUMP_QUERIES=1 npx vitest run src/queries/dump.spec.ts
  import { writeFileSync, mkdirSync } from "node:fs";
  import { describe, it } from "vitest";
  import { keyFiguresQueries } from "./key-figures";
  describe.skipIf(!process.env.DUMP_QUERIES)("dump factory queries", () => {
    it("writes default and non-default selections", () => {
      mkdirSync("tmp/queries", { recursive: true });
      for (const [name, sel] of [["default", {}], ["e1-q2", { entity: "E1", period: "2026-Q2" }]] as const)
        for (const [q, f] of Object.entries(keyFiguresQueries))
          writeFileSync(`tmp/queries/${q}-${name}.dax`, f(sel).query);
    });
  });
  ```

  then `npx fabric-app-data query <alias> --file tmp/queries/<file>.dax` for each file (keep
  `tmp/` in `.gitignore`).
- Unit-test that a comment mentioning the tag survives unchanged, that the tagged `VAR` occurs
  once and after `DEFINE`, and that equal selections give identical text (cache hits).

## 3. Values the app must not compute

ΔPY, ΔPL, ΔPY%, ΔPL%, AC&FC (the model's `AC+FC` item), PY, impact, YTD/FY views, report-line
subtotals: all in the model (calculation groups, explicit measures, functions). The app computes
only presentation: scaling, label decimals, remainder gaps, sort order, the AC/FC split from the closed-period flag. If a value is missing, ask
for a model change (`semantic-model-ibcs`) instead of recomputing it in TypeScript. A client-side
relative-variance helper is acceptable for prototypes only and must match the model's rule (signed
reference, N/A when not interpretable).

Map the queried columns straight into chart rows, e.g.
`{ category, AC, PL, variances: { "ΔPL": r["ΔPL"], "ΔPL%": r["ΔPL%"] }, impact: r.Impact }`. A
present variance value wins over any computed fallback (BLANK → `null` → N/A); impact changes colour
only and wins over a static polarity. The model's impact is BLANK only for an exact zero; the app
knows the displayed decimals, so it applies the **rounded-zero rule** itself: a Δ that rounds to
zero at the visual's factor and decimals gets no mark, no colour and an unsigned label (`0.0`),
whatever the impact column says. Check zero first, then impact, then polarity (the reference
components' `impactKey ( Δ, { impact, polarity, isZero } )` does it in that order).

## 3a. When the model must not change: query-scoped measures

A shared model sometimes lacks a value the spec needs (AC&FC, a full-period PY for forecast months,
FC−BU) and its owners cannot change it in time. Middle path: define the missing measures **in the
query** with `DEFINE MEASURE`, built only from the model's own measures and functions (for example
`Ibcs.Delta`, `Ibcs.DeltaPct`, `Ibcs.Impact`), never from raw arithmetic in TypeScript.

```dax
DEFINE
    MEASURE 'Measures'[q Revenue AC&FC] =            -- open month and later: FC (last CLOSED period decides)
        SUMX ( VALUES ( 'Date'[YearMonth] ),
            IF ( CALCULATE ( SELECTEDVALUE ( 'Date'[IsClosedPeriod] ) ), [Revenue], [Revenue FC] ) )
    MEASURE 'Measures'[q Revenue AC&FC ΔBU]  = Ibcs.Delta ( [q Revenue AC&FC], [Revenue BU] )
    MEASURE 'Measures'[q Revenue AC&FC ΔBU%] = Ibcs.DeltaPct ( [q Revenue AC&FC], [Revenue BU] )
EVALUATE
SUMMARIZECOLUMNS ( 'Date'[YearMonth], 'Date'[MonthLabel], 'Date'[IsClosedPeriod],
    "ACFC", [q Revenue AC&FC], "BU", [Revenue BU],
    "ΔBU", [q Revenue AC&FC ΔBU], "ΔBU%", [q Revenue AC&FC ΔBU%],
    "ImpactΔBU", Ibcs.Impact ( [q Revenue AC&FC ΔBU], [Revenue Polarity] ) )
ORDER BY 'Date'[YearMonth]
```

- Prefix query measures (`q …`) so they never collide with model names; the table named in
  `DEFINE MEASURE` must exist in the model (any table works, the measure lives only in the query).
- Put each such query on the model's change list and flag it in the page footnote ("AC&FC
  computed in the app query; model change requested"). Once the model has the measure, delete the
  `DEFINE` block.
- The full patterns (per-month SUMX for AC&FC, full-period PY for forecast months) are in the
  `semantic-model-ibcs` skill, `visual-data-contract.md`, explicit-measure models.
- Power BI reports use report-level measures for the same purpose (the `ibcs-power-bi` plugin).

## 4. Performance and throttling

| Lever | Practice |
|---|---|
| Grain | aggregate in DAX to the visual's grain; never fetch detail to roll up |
| Fan-out | small multiples by entity = **one** query with the entity in the group-by, split client-side |
| Parallelism | start all page queries together; render tiers as they arrive (skeletons keep the layout stable) |
| Cache | one client per app; same query text = cache hit, so build the text deterministically (sorted filter lists); bypass the cache only on explicit refresh |
| Filters | low cardinality → widen grain + filter client-side; high cardinality (dates, customers) → push to DAX |
| Limits | as of 2026-10, executeQueries: 100,000 rows / 1,000,000 values / 15 MB per query, **120 query requests per minute per user**; DAX only (no MDX, INFO functions or DMVs). Batch, debounce selector changes (≈ 300 ms), no per-row queries. Source: [Datasets - Execute Queries](https://learn.microsoft.com/rest/api/power-bi/datasets/execute-queries) |
| Identity | service principals are not supported against models with RLS or SSO, so always query delegated, as the user |
| Payload | only the columns the chart needs; `TOPN` for rankings; no `FORMAT()` |
| Model side | Direct Lake or Import beats DirectQuery for interactive pages; check slow measures with DAX query diagnostics before blaming the app |
| Prefetch | optional: prefetch the default drill target after first paint, within the request budget |

## 5. RLS/OLS-aware queries

- Queries run as the user: no `USERPRINCIPALNAME()` logic in the app; RLS lives in the model.
- A column hidden by OLS makes the whole query fail for that user. Keep OLS-sensitive columns in
  separate queries so the rest of the page renders, and show "not available for your role".
- Don't log result payloads (they are the user's data); log query names, durations and error
  categories.

## 6. Portal value shapes (observed 2026-10)

Inside the Fabric portal the data proxy delivered **Apache Arrow**, not the JSON that the Rayfin
data CLI prints. Measure columns arrived as a union type, and values differed by engine type:

| Engine value | CLI | Portal |
|---|---|---|
| Double (Δ%, ratios, `DIVIDE`) | `0.0782` | `0.0782` |
| Fixed decimal / currency (most amounts) | `144723758.21` | in a typed Arrow `Decimal` column: already scaled by `@microsoft/fabric-app-data` 1.1.0 (`makeDecimalCoercer` divides by 10^scale); in a measure column of **union** type: the **unscaled integer as a quoted string**, to divide by 10^4 |
| Date | ISO string | epoch milliseconds |
| Int64 (keys, counts, `SortOrder`) | not recorded in the 2026-10 observation *(verify with a portal sample)* | not recorded *(verify)*; never apply the 10^4 decimal rule to it |

**Mixed columns.** A column that holds amounts in some rows and ratios in others (a "one row per
KPI" query built with `UNION ( ROW ( … ), ROW ( … ) )`) has no single engine type and arrives as a
union column, so its currency values come as unscaled strings and its ratios as doubles. Give such
a column one type in the query: `CONVERT ( [Revenue], DOUBLE )`, `CONVERT ( [Gross Margin %], DOUBLE )`,
`CONVERT ( BLANK (), DOUBLE )`; or return one column per kind. Declare it `ratio`-like (`double`)
in the factory; the 10^4 rule then never applies to it.

Normalise every row centrally by column data type (one tested `normalizeValue`, fed with real
portal samples), never per page. Divide by 10^4 **only** string values of a union-typed or
`"unknown"` column declared as `amount`; a `number` that arrives in a `Decimal` column is final, or
you divide twice and amounts come out 10,000 times too small. Testing with the CLI or localhost alone will not show this:
amounts render blank only in the portal. Keep an in-app diagnostics toggle that lists each query's
columns, data types and first raw rows.

**When `dataType` is missing or `"unknown"`.** JSON results from the terminal (the CLI, and the
REST `executeQueries` response, which carries no column types) reported `dataType: "unknown"` in
the 2026-10 test. Do not branch on it. Declare each output column's kind once in the query
factory, next to its column metadata (`amount` = fixed decimal, `ratio` = double, `int`, `date`,
`text`), because you wrote the query and know which column is which; `normalizeValue` uses the
reported type when it is known and the declared kind otherwise. Never guess the kind from one
value (a digit string may be an unscaled amount or a code).
