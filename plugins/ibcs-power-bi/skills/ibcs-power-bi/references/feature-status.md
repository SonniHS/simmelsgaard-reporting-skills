# Power BI features this plugin relies on (as of 2026-10)

Checked 2026-10 against Microsoft Learn and the Power BI Desktop release notes (features up to the
August 2026 release; the PBIR row against Learn on 2026-10-21; Deneb 2.0.0). The bundled theme is pinned to report theme schema 2.157 on purpose: newer
schemas (2.158, 2.159) still load it, and `build_pbi_theme.py --validate --schema` checks it against
any of them. Power BI changes monthly: re-check anything
marked preview or "rolling out" before you depend on it.

| Feature | Status as of 2026-10 | Used for | Docs |
|---|---|---|---|
| Visual calculations + custom totals | GA (May 2026) | per-visual Δ, Δ%, running sums | [visual calculations](https://learn.microsoft.com/power-bi/transform-model/desktop-visual-calculations-overview) |
| DAX user-defined functions | GA (June 2026), compatibility level ≥ 1702 | a reusable `Svg.*` function block | [DAX UDFs](https://learn.microsoft.com/dax/best-practices/dax-user-defined-functions) |
| Overlapping series for bar/column (`layout.clusteredGapOverlaps`) | available | AC in front of PY/PL with offset | [axis and layout](https://learn.microsoft.com/power-bi/visuals/power-bi-visualization-customize-x-axis-and-y-axis) |
| Error bars (by field or %, marker shapes incl. triangle) | available | compromise scenario markers | [Analytics pane](https://learn.microsoft.com/power-bi/transform-model/desktop-analytics-pane) |
| Outer padding for bar/column/line/waterfall | GA (Aug 2026) | consistent category width | [latest update](https://learn.microsoft.com/power-bi/fundamentals/desktop-latest-update) |
| Modern visual defaults and the Theme pane | GA (Aug 2026); the base theme no longer overrides fonts | theme fonts apply consistently | same |
| Button slicer showing SVG images | GA (Oct 2025) | single SVG charts | [update archive](https://learn.microsoft.com/power-bi/fundamentals/desktop-latest-update-archive) |
| Sparklines in table/matrix | GA (Jun 2025) | basic trends (no scenario coding) | same |
| PBIR as the default report format | GA and the default in the Service and in Desktop releases from September 2026; a PBIR-Legacy report is converted on save (backup kept 30 days in Desktop, 28 in the Service) | file-based authoring | [PBIR format](https://learn.microsoft.com/power-bi/developer/projects/projects-report#pbir-format) |
| Pattern / hatched fills in **core** visuals | **not available** (the schema contains an undocumented pattern property; do not rely on it) | FC hatch → Deneb or SVG | — |
| Deneb 2.0 (Vega 6.4.0 / Vega-Lite 6.4.3) | AppSource custom visual; `pbiPatternSVG()` pattern fills need the SVG renderer | IBCS charts | [deneb.guide](https://deneb.guide/) |
| FC hatch in Deneb vs web | Deneb's built-in `diagonal-stripe-N` tiles are fixed at 10 px (stripe period about 7.1 px); `sync_tokens.py` picks the N closest to the token stripe share (`pattern.fcHatch.stripeShare`), so the stripe share matches but the pitch is coarser than the token period (4 px) that web apps draw. Hatched pin heads use the same tile. Accepted difference; no workaround inside Deneb | FC columns, Δ columns, pin heads | `ibcs-deneb` SKILL.md (FC hatch) |
