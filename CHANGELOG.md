# Changelog

All notable changes to this marketplace and its plugins. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed
- The repository and marketplace are renamed from `simmelsgaard-skills` to `simmelsgaard-reporting-skills`.
  The old marketplace name is gone: remove it with `/plugin marketplace remove simmelsgaard-skills`, then add
  `SonniHS/simmelsgaard-reporting-skills` and install with `<plugin>@simmelsgaard-reporting-skills`. GitHub
  redirects the old repository URL.

### Added
- Docs: [getting started](docs/getting-started.md) (model → visual spec → Power BI report or Fabric App
  → review → deploy, with the prompts), a [gallery](docs/gallery.md) and [troubleshooting](docs/troubleshooting.md).
- `examples/sample-sales`: a generic, IBCS-ready TMDL semantic model with calculated tables (AC, BU,
  FC stored; PY derived), its generator, CSVs, `expected_results.csv` and the Key figures visual spec.
- `ibcs-web-charts` ships lean React + TypeScript + SVG reference components (MIT) in
  `assets/react-reference/`: column chart with variance tiers, pins and Total alignment, structure
  bars, variance waterfall, KPI card on a Fluent card, number formatting with the rounded-zero rule,
  a page scale registry, a renderer with hatch patterns and accessibility, 30 unit tests and
  rendered previews. The `ibcs-fabric-app` chart layer now starts from them.
- Continuous integration: unit tests, generated-file `--check`s, the reference components' typecheck and tests,
  and `claude plugin validate --strict` for the marketplace and every plugin.
- `CONTRIBUTING.md`, `SECURITY.md`, issue and pull request templates, and `docs/prerequisites.md`.

### Fixed
- Rounded-zero rule applied everywhere: a variance that rounds to zero at the displayed decimals prints
  unsigned and uncoloured and draws no mark (checklist B5/E6, linter, token descriptions, calc-group
  format strings via `Ibcs.DeltaFormat ( value, … )`, Power BI card routes, SVG key message, apps).
  Colour logic checks zero first, then the model's impact, then polarity.
- `semantic-model-ibcs`: the ΔPY/ΔBU minuend is the constant item AC+FC; reading 'Time Calc' inside the
  items exhausted query memory in Fabric. New member items use `Ibcs.DeltaMember` so structure rows
  reconcile; text colours use the contrast-safe text tokens.
- `fabric-apps`: the dev loop never provisions tenant resources (`npm run dev` is `rayfin dev` in the
  dataapp template), every deploy names `--workspace` and `--item-name`, CI login works on Linux
  runners, Node 22/24 LTS, consumers need Read only.
- `ibcs-power-bi`: `to_pbir.py` registers Deneb in the report, `new_pbip.py --force` keeps report
  measures, `gen_reference.py --help` writes nothing, the theme's impact colours use the text tokens,
  Microsoft's `powerbi-authoring` skills are named.
- Stale product facts refreshed against Microsoft Learn (PBIR default, Business Central mirroring,
  org app Git support, fabric-cicd OrgApp support). The leak scan reads every UTF-8 file.

### Changed (first service render, rev 4)
- One notation for Power BI and web: pins at 1 px per pp with a minimum stem, one outlier rule (clip at
  ±100 % with a triangle at the clip point), end legends only right of the last month and the Total at
  their marks' y, the BU name at the upper part of its column, the scale band at the plot's left edge
  with its value label, the band behind the last closed month, the year label only across two years.
- Power BI rounded cards: the card look sits on the shape visual's container (the theme's basicShape
  styling rendered dark and failed the validator); content at z ≥ 1000; header geometry from the real
  17 px table header; own-scale Totals report their own range; PDF-export fallback for checks.
- Web reference components: label collision by priority against every mark of the tier, two-line
  names, a `keep` list for cited values, scale-band label, year line; contract and chart layer updated.

### Changed (waterfalls)
- One form per waterfall type in every renderer, chosen by the category type: structure decompositions
  as rows (card A-29, total variance as an arrow below AC), time decompositions as columns (card A-11,
  new Deneb template `waterfall-variance-time`, web `layoutTimeWaterfall`, arrow right of AC).
- Magnifying glass (CH 4.5) in web, Deneb and SVG-DAX (two-visual pattern): a steps-only panel at ×k
  when the largest step is under 5 % of the base (our default, knob `magnifyBelow`); base and total
  stay on the page scale.

### Fixed (proof run 2)
- Pin outliers: a pin beyond 3 × the next-largest |Δ%| of its tier (or the ±100 % clip) is clipped with
  the outlier triangle and its full label, and the tier scales from the other pins (web `outlierRatio`,
  Deneb `pinOutlierFactor`, `scale_layout.py`); a tier where most pins are too short fails a check (E12).
- Bridges fit their width: one shared fitted scale for bridges read together, the magnifier below at
  phone width, names wrap before they are cut; overflow is a failing check.
- Public copy: page text never carries internal notes ("proposed", "TBD", "model change"); footnotes
  state definitions only; new lint C16 (dom and pbir).
- Power BI: phone layout declared not supported in 1.0.0; key message 72 px and one title-line recipe;
  the calculation waterfall's scale band uses the band tokens; F6 exempts visuals without a base tier;
  Microsoft's `powerbi-authoring` skills named (`powerbi-report-cli`, `semantic-model-authoring`) with
  the `powerbi-report-author validate` step.
- Label thinning keeps the extremes first; deploy wording in the Fabric App builder requires the user's
  approval and a dry run.

### Changed (marked pin scales)
- A relative-variance tier whose scale differs from the page's other pin tiers carries a scaling marker
  (UN 5.2 / CH 4.3): a round-value band with its label, in the scale-band style (web `pctScaleBand`,
  Deneb `pinScaleBand`, set automatically by `scale_layout.py`). Charts read together share one scale.
  Our rule, stated in the contract, chart layer, page shell, visual spec format and notation skill; an
  unmarked differing pin scale fails the `pbir` and `dom` lint checks (F6).

### Fixed (proof run 1)
- Pins carry magnitude: each relative-variance tier has its own scale sized to the tier (48 px column,
  90 px bar tiers), the largest |Δ%| fills about 90 %; 6 px heads at the stem end; a rounded zero keeps a
  baseline marker; one decimal in both tools; a check that the largest stem is at least 40 % of its tier.
- Labels never cross axis, baseline or rule lines (render-time check in the Deneb previews, tests on the
  web); one magnifier form (frame, dashed connectors, panel) with the break glyph on the panel baseline.
- Period names never get an ellipsis (Jan → J → two rows); dimension names use the free space, then wrap.
- Rows that explain a total use the member variance items: blank AC with a reference counts as 0, the
  zero AC is labelled, and charts warn when the rows do not add up to the total.
- Builders' gaps: stable scale registry with several charts, tests that run in an app's jsdom setup,
  phone stacking of structure tiers, KPI card alignment, absolute-first Δ order, a second absolute
  tier, compare-with in title line 3, Power BI padding option, title-line heights, logo and mobile
  layout recipes, own-scale members in the linter and scale_layout, reference-date footers.

### Fixed (found by deploying the sample model)
- `semantic-model-ibcs`: inside a Δ item with its own format string expression,
  `SELECTEDMEASUREFORMATSTRING ()` returns the item's pp format, so `Ibcs.IsRatioFormat` now also
  recognises `" pp"`; before, variances of ratios came back as fractions instead of percentage points.
- `semantic-model-ibcs`: a UDF parameter named like a DAX function (`value`) makes the engine drop the
  function silently; the format helpers use `amount`, and the TMDL rules warn about it.

## [0.1.0] - 2026-10-20

### Added
- First public release of the marketplace with four plugins:
  - `ibcs`: notation, page composition with a visual spec, web chart behaviour, review checklist and linter.
  - `ibcs-power-bi`: IBCS-style Power BI reports with a route per visual, Deneb (Vega-Lite) templates with
    token sync, and SVG-in-DAX tables.
  - `fabric-apps`: reporting apps on Microsoft Fabric and Power BI org apps.
  - `reporting-data`: semantic model for IBCS visuals, SQL gold layer, Dynamics 365 ERP source mappings.
