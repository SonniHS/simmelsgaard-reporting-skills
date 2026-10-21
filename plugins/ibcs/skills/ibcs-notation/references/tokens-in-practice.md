# Design tokens in practice

> The bundled `assets/ibcs-tokens.json` (paths in this file are relative to this skill's
> directory, `${CLAUDE_SKILL_DIR}` in SKILL.md) holds every concrete value of the notation:
> colours, patterns, geometry ratios, line widths, typography, number and date formats,
> abbreviations, polarity codes and page-grid defaults. This page explains its structure, the provenance
> labels, how to override it for an organisation, and how to consume it from CSS, JavaScript,
> Vega-Lite and Power BI. Tool-specific building belongs to the implementation skills (the
> [ibcs-web-charts](../../ibcs-web-charts/SKILL.md) skill in this plugin, and the `ibcs-power-bi`
> and `ibcs-deneb` skills of plugin `ibcs-power-bi`).

## Contents
1. File structure
2. Provenance labels
3. Load order (base + overrides)
4. Overriding: what may change
5. Consuming the tokens (CSS, JavaScript, Vega-Lite, Power BI)
6. Property map
7. Variance colour logic
8. Checking a token set

## 1. File structure

The file follows the W3C Design Tokens (DTCG) format:

- A **token** is an object with `$value` (and optionally `$description`). A **group** is any other
  object; `$type` set on a group applies to every token below it.
- **Aliases**: a `$value` of the form `"{color.scenario.ac}"` points to another token and is
  resolved after merging overrides (so overriding `color.scenario.ac` also changes the PL outline
  and the FC stripe that alias it).
- **Provenance** sits in `$extensions.ibcs` on a token or group: `src` (label, §2), `ref` (IBCS
  rule and page, e.g. `UN 3.2, p. 45`) and an optional `note`. A token without its own block
  inherits the nearest ancestor's.
- The root `$extensions.ibcs.meta` names the schema version, the IBCS version followed, the
  licence (MIT for the data) and the override file name.

| Group | Contains | Examples |
|---|---|---|
| `color.scenario` | AC, PY, PL, BU, FC fills/strokes, stack grays | `color.scenario.ac`, `color.scenario.fc.stripe` |
| `color.variance` | impact colours for graphics, contrast-safe text variants for tinted numbers, CVD and black-and-white variants | `color.variance.good`, `color.variance.goodText`, `color.variance.bw.bad` |
| `color.marker`, `color.text`, `color.axis`, `color.table`, `color.background` | highlight, scale band, assisting lines, text, variance axes, table rules | `color.marker.scaleBandFill`, `color.axis.plReference` |
| `pattern.fcHatch` | forecast hatch geometry and an SVG `<pattern>` template | `pattern.fcHatch.svgTemplate` |
| `geometry` | width ratios, pin, offsets, triangles (ratios plus px clamps), category width per period | `geometry.barWidthRatio.absolute`, `geometry.pin.headPx.max` |
| `stroke` | line widths (pt for print/Power BI, px for screens), variance axes, table rules | `stroke.varianceAxis.plGapPx` |
| `typography` | font families (Power BI, web), weights, sizes in pt and px | `typography.size.label.px` |
| `number` | max digits, separators, signs, N/A, scaling prefixes, format patterns (d3 and Excel) | `number.format.variance.excel`, `number.format.relativeVariance1.d3`, `number.format.plainRatio.excel` |
| `date` | period label patterns and analysis notation (span, YTD, moving, Ø) | `date.notation.ytd` |
| `abbreviation` | scenario, variance and analysis codes, scenario/variance order | `abbreviation.scenarioOrder` |
| `polarity` | +1 / −1 / 0 codes and the colour rule | `polarity.lowerIsBetter` |
| `layout` | canvas, margin, gutter, header/footer bands, table gaps, small-multiple limit | `layout.marginPx` |

## 2. Provenance labels

| `src` | Meaning | May an organisation change it? |
|---|---|---|
| `STD` | stated by IBCS v2.0 (often as an ISO 24896 requirement) | no — changing it is a notation error |
| `REC` | recommended by IBCS ("works well", "a good choice") | yes, if the alternative is documented and used consistently |
| `FIG` | measured from an IBCS figure; IBCS does not prescribe the exact value | yes (typically colour codes, offsets, hatch spacing) |
| `OURS` | our default where IBCS is silent (pixel sizes, grid, format patterns) | yes |
| `ORG` | an organisation's override (set by you, §4) | — |

Many tokens mix two levels; the `ref` text says which part is which, e.g. "rule STD, hex FIG":
the rule (impact colours are bright green / dark red / blue) is fixed, the hex code is not.

## 3. Load order (base + overrides)

1. Read the bundled `ibcs-tokens.json`.
2. If the project has an `ibcs-tokens.overrides.json` (start from the bundled
   `assets/ibcs-tokens.overrides.example.json`), deep-merge it on top: objects merge
   key by key, the override wins, arrays are replaced wholesale.
3. Resolve `{path}` aliases (after the merge, so overrides propagate).
4. Inherit `$type` and `$extensions.ibcs` from the nearest ancestor where a token has none.

Where the override file lives is the project's choice (repo root, a `design/` folder, next to
the report). Keep exactly one per organisation or report family and point every consumer at it.

```sh
# merge with jq (no alias resolution)
jq -s '.[0] * .[1]' path/to/ibcs-tokens.json ibcs-tokens.overrides.json > tokens.effective.json
```

Minimal resolver (Python, stdlib):

```python
import json, re

def merge(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return {**a, **{k: merge(a[k], v) if k in a else v for k, v in b.items()}}
    return b

def value(tokens, path, depth=0):
    node = tokens
    for part in path.split("."):
        node = node[part]
    v = node["$value"]
    if isinstance(v, str) and re.fullmatch(r"\{[^{}]+\}", v) and depth < 10:
        return value(tokens, v[1:-1], depth + 1)
    return v

tokens = merge(json.load(open("ibcs-tokens.json")), json.load(open("ibcs-tokens.overrides.json")))
print(value(tokens, "color.scenario.pl.stroke"))   # follows the alias to color.scenario.ac
```

Never copy a hex value from this page or from the IBCS book into code — read the effective token.

## 4. Overriding: what may change

Override only `$value` (and optionally `$description`) of **existing** token paths, and mark each
override with `"$extensions": {"ibcs": {"src": "ORG", "ref": "<notation manual section>"}}`.
New paths are not consumed by anything and hide typos.

| Allowed (document in the notation manual) | Not allowed (notation errors) |
|---|---|
| hex codes of grays and impact colours, keeping the guardrails: scenario inks neutral, AC darker than PY, good brighter than bad, hues still green / red / blue | scenarios coded by hue (a "forecast colour") |
| font families and sizes | impact colours on non-variance elements |
| decimal sign, thousands separator, negative style, locale-specific date labels | bar width ratios other than 2/3 and 1/3 |
| pixel sizes, hatch spacing, offsets, page grid | a plus sign on plain values; more than 3/4 digits |
| currency code (EUR is only the example) | independent scales for the same unit |

Typical overrides: corporate font (`typography.family.web`), decimal comma
(`number.separator.decimal`), a darker corporate green (`color.variance.good`), a different
highlight blue (`color.marker.highlight`). The example file shows all four. When you change an
impact colour, check its text variant too (`color.variance.goodText` / `badText` /
`neutralText`): it must stay in the same hue family and keep ≥ 4.5:1 on the page background —
the linter (§8) checks both.

Locale and currency are settings, not hard-coded: the format patterns in `number.format.*` use
"," as the group placeholder and "." as decimal; the consumer swaps in `number.separator.*`
after formatting (Excel/Power BI format strings take separators from the report culture).

## 5. Consuming the tokens

### CSS (custom properties)

Generate the stylesheet from the effective tokens rather than writing values by hand:
`node scripts/gen_tokens.mjs --out src/ibcs/tokens.generated.css` writes one `--ibcs-<path>`
property per token, named after its path with dots as dashes: `--ibcs-color-scenario-ac`,
`--ibcs-color-variance-good`, `--ibcs-color-variance-goodText`,
`--ibcs-typography-size-label-px`. Use these names in `var()`; do not mix them with a
hand-written shorter naming, or `var()` resolves to nothing.

Put the FC hatch from `pattern.fcHatch.svgTemplate` into one `<defs>` per page and reference it
with `fill="url(#ibcs-fc-hatch)"`. For no-colour output (print, `forced-colors`), switch the
impact variables to `color.variance.bw.*`; for a colour-vision-deficiency variant to
`color.variance.cvd.*`.

### JavaScript / TypeScript

Generate the module at build time with the bundled script `scripts/gen_tokens.mjs` (Node 18+,
no dependencies, ESM). It runs the same steps as the Python resolver above — deep-merge the
overrides, then resolve aliases — and writes only resolved values:

```sh
# from the app's root; the overrides file is found in the current directory or a parent
node "<this skill's directory>/scripts/gen_tokens.mjs" --out src/ibcs/tokens.generated.ts
node "<this skill's directory>/scripts/gen_tokens.mjs" --out src/ibcs/tokens.generated.css   # custom properties
node "<this skill's directory>/scripts/gen_tokens.mjs" --out tokens.effective.json \
  --overrides path/to/ibcs-tokens.overrides.json        # or --no-overrides; --tokens for another base file
```

`.ts` gives `export const tokens = {…} as const` (plus `export type IbcsTokens`), `.json` the
plain nested object, `.css` one `--ibcs-<path>` property per colour, typography, layout and
stroke token (`--ibcs-color-variance-goodText`, `--ibcs-typography-size-label-px: 12px`). A
missing alias target or an unknown extension exits with code 2. Copy the script into the app
(e.g. `scripts/`) if the build must not depend on the skill's location, and re-run it whenever
the base tokens or the overrides change; commit the generated file or generate it in the build.

Chart components import the generated module and never contain literals. Format numbers with
`Intl.NumberFormat`, or d3-format with an **unsigned** pattern (`number.format.absolute.d3`,
`.ratio.d3`), then replace the group separator with `number.separator.thousands` (U+202F) and add
"+" only to a variance whose value, rounded at the displayed decimals, is > 0; a value that rounds
to 0 stays unsigned. Do not prepend "+" to the signed d3 tokens (`variance`, `relativeVariance`,
`percentagePoints` already contain it, and print `+0.0` for 0.04). Reference implementation:
`formatValue()` in the formatting reference of the `ibcs-web-charts` skill ([formatting-a11y-print.md](../../ibcs-web-charts/references/formatting-a11y-print.md)).

### Vega-Lite / Deneb

Map tokens into `config` (font, font sizes, `view.stroke: null`, `axis.grid: false`) and into
explicit `scale.range` arrays for scenario colours; impact colours go into a `condition` on a
computed `impact` field. Vega-Lite has no pattern fill: hatch FC with a stripe layer or use Vega
/ SVG. The `ibcs-deneb` skill (plugin `ibcs-power-bi`) ships ready templates with a token sync.

### Power BI

Generate the report theme from the tokens: `dataColors` = grays (AC, PY, white, stack grays),
`good`/`bad`/`neutral` from `color.variance.*`, `textClasses` from `typography.*` (pt values),
visual defaults with legend, gridlines, borders and shadows off. Number formats from
`number.format.<kind>.excel`; display units fixed per scale group (never "Auto"). The
`ibcs-power-bi` skill (plugin `ibcs-power-bi`) covers theme generation and the native-visual
compromises.

## 6. Property map

| Need | Token path | Power BI (theme / visual.json) | Vega-Lite / Deneb | CSS / SVG |
|---|---|---|---|---|
| AC fill | `color.scenario.ac` | `dataColors[0]`; `dataPoint.fill` for the AC measure | `color: {value}` / scale range | `--ibcs-color-scenario-ac` |
| PY fill | `color.scenario.py` | `dataColors[1]`; series `dataPoint.fill` | scale range | `--ibcs-color-scenario-py` |
| PL outlined | `color.scenario.pl.fill` + `.stroke`, `stroke.outlinePx` | white fill + `borderShow`, `borderColor`, `borderSize` | `fill`, `stroke`, `strokeWidth` | `fill` / `stroke` |
| FC hatch | `pattern.fcHatch.*`, `color.scenario.fc.*` | not native → SVG measure / Deneb-Vega / certified visual | stripe layer or Vega/SVG `<pattern>` | `svgTemplate` in `<defs>` |
| Stacked shades | `color.scenario.stackGrays` | `dataColors[3..]` | `scale.range` | — |
| Impact colours | `color.variance.good/bad/neutral` | theme `good`/`bad`/`neutral`; colour measure for conditional formatting | `condition` on `datum.impact` | `--ibcs-color-variance-good` … |
| CVD / B&W | `color.variance.cvd.*`, `color.variance.bw.*` | alternate theme | alternate config | print / `forced-colors` stylesheet |
| Highlight | `color.marker.highlight` | ellipse shape / SVG | unfilled `point` or ellipse path | `<ellipse fill="none">` |
| Scale band | `color.marker.scaleBandFill/Line` | constant line + shaded area | `rect` y = 0..band | `<rect>` |
| Bar width | `geometry.barWidthRatio.*` | inner padding ≈ 1 − ratio (33 % abs, 67 % rel) | `scale.paddingInner: 1 − ratio` or `size: {band: ratio}` | — |
| Overlap offset | `geometry.referenceOffsetRatio.*` | `clusteredGapOverlaps` + `clusteredGapSize` | `xOffset` / `yOffset` | translate |
| Pins | `geometry.pin.*` (ratios, clamped to `stemPx` / `headPx` min..max) | error-bar workaround or SVG | `rule` + square `point` | `<line>` + `<rect>` |
| Triangles | `geometry.triangleSizeRatio`, clamped to `geometry.triangleSizePx` | SVG measure / Deneb | `point` shape `triangle-right` / `triangle-down` | `<path>` |
| Tinted variance numbers | `color.variance.goodText` / `badText` / `neutralText` (≥ 4.5:1) | font colour measure | `condition` on `datum.impact` for `text` marks | `--ibcs-color-variance-goodText` … |
| Variance axis | `color.axis.pyReference/plReference`, `stroke.varianceAxis.*` | not native → SVG/Deneb | one thick `rule` (PY) / two `rule`s offset ±`plGapPx/2` (PL) | two `<line>` |
| Category step | `geometry.categoryStepPx.*` | fixed visual width per period type | `width: {step: N}` | grid column width |
| Lines | `stroke.line.*` | series `strokeWidth` | `strokeWidth` | `stroke-width` |
| Fonts | `typography.family.*`, `typography.size.*.pt/px`, `typography.weight.*` | `textClasses` (pt) | `config.font`, `fontSize` (px) | `font-family`, `font-size` |
| Number formats | `number.format.<kind>.excel` / `.d3` (`relativeVariance1` for one-decimal Δ%, `plainRatio` for ratios such as book-to-bill) | format string / dynamic format string | `format` + replace separators | `Intl.NumberFormat` + replace |
| Separators | `number.separator.*` | report culture; U+202F via label measures | replace `,` → U+202F | same |
| Prefixes | `number.scaling.*` | display units fixed (never "Auto") | pre-scale values (d3 `s` gives M/G, not m/b) | pre-scale |
| Dates | `date.*` | label columns in the date table | label field from the model | — |
| Page grid | `layout.*` | canvas, margins, header/footer bands | `autosize`, `padding` | CSS grid |

## 7. Variance colour logic (same everywhere)

```
// colour only — geometry (bar direction, position) always uses delta itself
shown  = round(delta, displayDecimals)             // at the visual's factor and decimals
color  = shown == 0           ? none               // FIRST: no bar; unsigned "0.0" in default colour — never bad or neutral
       : modelImpact != null  ? modelImpact        // the model's Impact column wins over polarity
       : polarity == 0        ? neutral            // blue
       : delta * polarity > 0 ? good : bad
relVar = ref == null or ref <= 0 ? "N/A"           // OURS operational rule for "not interpretable"
       : (value - ref) / ref                       // signed ref, never ABS
// e.g. PL 100, AC -20 → -120 % (shown);  PL -30, AC -10 → N/A
```

A Δ that **rounds to zero at the displayed precision** (book-to-bill +0.0005 shown with two
decimals) is treated like Δ = 0: unsigned label, no impact colour, no mark (`OURS`). Graphics use
`color.variance.{good,bad,neutral}`; a variance **number** may be tinted only with the
contrast-safe `color.variance.*Text` variant, otherwise it stays `color.text.primary` (see the
ibcs-notation SKILL.md, §3).

Take `polarity` from the data model as a per-measure attribute (see the `semantic-model-ibcs`
skill of plugin `reporting-data`), never infer it from the sign. Neutral (polarity 0) is **blue**
in IBCS v2.0, not gray.

## 8. Checking a token set

Run the linter of the [ibcs-review](../../ibcs-review/SKILL.md) skill on the merged set; it
checks the guardrails above (neutral scenario inks, AC/PY contrast, empty PL/FC ground, impact
hues and brightness order, text contrast including the `*Text` variance colours, width ratios,
plus sign, digit limits). The linter is
`../ibcs-review/scripts/ibcs_lint.py` relative to this skill's directory; from the project root,
with `${CLAUDE_SKILL_DIR}` replaced by the absolute path of this skill's directory (it is
substituted in SKILL.md only, not in this file):

```sh
python3 -I "${CLAUDE_SKILL_DIR}/../ibcs-review/scripts/ibcs_lint.py" tokens path/to/ibcs-tokens.json \
  --overrides ibcs-tokens.overrides.json
```
