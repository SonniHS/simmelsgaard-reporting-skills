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

## [0.1.0] - 2026-10-20

### Added
- First public release of the marketplace with four plugins:
  - `ibcs`: notation, page composition with a visual spec, web chart behaviour, review checklist and linter.
  - `ibcs-power-bi`: IBCS-style Power BI reports with a route per visual, Deneb (Vega-Lite) templates with
    token sync, and SVG-in-DAX tables.
  - `fabric-apps`: reporting apps on Microsoft Fabric and Power BI org apps.
  - `reporting-data`: semantic model for IBCS visuals, SQL gold layer, Dynamics 365 ERP source mappings.
