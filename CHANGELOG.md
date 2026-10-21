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
- `ibcs-web-charts` ships lean React + TypeScript + SVG reference components (MIT) in
  `assets/react-reference/`: column chart with variance tiers, pins and Total alignment, structure
  bars, variance waterfall, KPI card on a Fluent card, number formatting with the rounded-zero rule,
  a page scale registry, a renderer with hatch patterns and accessibility, 30 unit tests and
  rendered previews. The `ibcs-fabric-app` chart layer now starts from them.
