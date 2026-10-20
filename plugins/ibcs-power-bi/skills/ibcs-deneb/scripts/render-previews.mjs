#!/usr/bin/env node
// Render the IBCS Deneb templates to SVG (and PNG) with sample data, outside Power BI.
//
//   VEGA_HOME=<dir with node_modules/vega + vega-lite> node render-previews.mjs [template ...]
//       [--assets <skill directory>/assets] [--out <dir>] [--png] [--chrome <path> | env CHROME]
//
// One-time setup in a scratch dir (pinned to the versions Deneb 2.0 bundles; never global):
//   VG=6.4.0; VL=6.4.3
//   npm install --prefix "$VEGA_HOME" --no-audit --no-fund --ignore-scripts "vega@$VG" "vega-lite@$VL"
//
// What it emulates from Deneb, so the previews match the visual:
//   - data: the template's {"name": "dataset"} is filled from assets/sample-data/<id>.json
//   - config: assets/config/deneb-config.json (generated from the tokens) is passed as Deneb does
//   - width/height "container": replaced by usermeta.ibcs.preview.{width,height}
//   - pbiPatternSVG(id, fg, bg): returns url(#…) and the <pattern> is injected into the SVG,
//     with the geometry of Deneb's built-in diagonal-stripe-N patterns (10x10 tile, stroke N)
//   - __selected__ / __highlight fields are absent (= nothing selected), like a fresh visual
// Variants (usermeta.ibcs.previewVariants) may set params, sampleData and preview {width, height};
// previewGroups render several members of one scale group side by side into one preview. A member
// with pxPerUnit is checked: its value scale must render at that px per unit (else WARN, exit 1).
// It does NOT emulate pbiFormat, pbiColor or the pbiContainer* signals: templates avoid them.
// PNG: headless Chrome screenshots an HTML page holding the SVG (device scale 2).
//
// Live data for a PBIR Deneb visual (the spec and config written into a report):
//   VEGA_HOME=… node render-previews.mjs --visual <…/visuals/<v>/visual.json>=<rows.json> [--visual …] \
//       [--out DIR] [--png] [--name page]
//   rows.json: the executeQueries response of the visual's fields (raw, or as `fab api` prints it),
//   or a plain list of row objects. Columns "Table[Column]" / "[Measure]" are mapped to the names
//   Deneb exposes (the projection's displayName, else its nativeQueryRef). The container size is
//   the visual's position.width/height minus its own padding (visualContainerObjects.padding). Several --visual pairs render one composite at their page
//   positions (scale groups, tiers stacked across visuals). Query the fields in the same filter
//   context as the page (slicer defaults, visual filters), e.g. SUMMARIZECOLUMNS over the category.

import { readFileSync, writeFileSync, existsSync, readdirSync, mkdirSync, rmSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join, resolve, basename } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { spawn } from "node:child_process";

const here = dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const opt = (n, d) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : d; };
const flags = new Set(args.filter((a) => a.startsWith("--")));
const valued = ["--assets", "--out", "--chrome", "--visual", "--name"];
const positional = args.filter((a, i) => !a.startsWith("--") && !(i > 0 && valued.includes(args[i - 1])));
const visualPairs = args.flatMap((a, i) => (a === "--visual" ? [args[i + 1]] : []));

const assets = resolve(opt("--assets", join(here, "..", "assets")));
const outDir = resolve(opt("--out", visualPairs.length ? "deneb-preview" : join(assets, "previews")));
const vegaHome = process.env.VEGA_HOME;
if (!vegaHome) { console.error("set VEGA_HOME (see header)"); process.exit(2); }
const req = createRequire(join(resolve(vegaHome), "noop.js"));
const vega = await import(pathToFileURL(req.resolve("vega")).href);
const vl = await import(pathToFileURL(req.resolve("vega-lite")).href);

// ---- Deneb shims ---------------------------------------------------------------------------
let failed = 0;
const patterns = new Map();
const cssId = (s) => String(s).replace(/[^A-Za-z0-9_-]/g, "");
vega.expressionFunction("pbiPatternSVG", (id, fg, bg) => {
  const key = `pp-${cssId(id)}-${cssId(fg)}-${cssId(bg ?? "none")}`;
  patterns.set(key, { id, fg: fg ?? "#000000", bg });
  return `url(#${key})`;
});
function patternDefs() {
  // Deneb's diagonal-stripe-N: 10x10 user-space tile, stripes rising bottom-left -> top-right,
  // stroke width N (1..6). Same path as the patternfills library Deneb ships.
  return [...patterns].map(([key, p]) => {
    const n = Number(/diagonal-stripe-(\d)/.exec(p.id)?.[1] ?? 1);
    const bg = p.bg ? `<rect width="10" height="10" fill="${p.bg}"/>` : "";
    return `<pattern id="${key}" patternUnits="userSpaceOnUse" width="10" height="10">${bg}` +
      `<path d="M-1,1 l2,-2 M0,10 l10,-10 M9,11 l2,-2" stroke="${p.fg}" stroke-width="${n}"/></pattern>`;
  }).join("");
}

function replaceContainer(spec, w, h) {
  const walk = (o) => {
    if (Array.isArray(o)) return o.forEach(walk);
    if (o && typeof o === "object") {
      if (o.width === "container") o.width = w;
      if (o.height === "container") o.height = h;
      Object.values(o).forEach(walk);
    }
  };
  walk(spec);
}

function injectData(spec, values, isVega) {
  if (isVega) {
    const d = spec.data.find((x) => x.name === "dataset");
    if (!d) throw new Error("Vega template needs data[name=dataset]");
    d.values = values;
    return;
  }
  const walk = (o) => {
    if (Array.isArray(o)) return o.forEach(walk);
    if (o && typeof o === "object") {
      if (o.data && o.data.name === "dataset" && !o.data.values) o.data = { values };
      Object.values(o).forEach(walk);
    }
  };
  walk(spec);
}

async function renderOne(templatePath, variant = null, write = true) {
  patterns.clear();
  const id = basename(templatePath).replace(/\.(vl|vg)\.json$/, "") + (variant?.suffix ?? "");
  const isVega = templatePath.endsWith(".vg.json");
  const spec = JSON.parse(readFileSync(templatePath, "utf8"));
  for (const [k, v] of Object.entries(variant?.params ?? {})) {
    const p = (spec.params ?? spec.signals ?? []).find((x) => x.name === k);
    if (!p) throw new Error(`variant param ${k} not in template`);
    p.value = v;
  }
  const meta = spec.usermeta?.ibcs ?? {};
  const dataFile = join(assets, "sample-data", variant?.sampleData ?? meta.sampleData ?? `${id}.json`);
  const values = JSON.parse(readFileSync(dataFile, "utf8"));
  const config = JSON.parse(readFileSync(join(assets, "config", "deneb-config.json"), "utf8"));
  const { width = 480, height = 300 } = variant?.preview ?? meta.preview ?? {};
  replaceContainer(spec, width, height);
  injectData(spec, values, isVega);

  let vgSpec;
  if (isVega) vgSpec = { ...spec, config: { ...config, ...(spec.config ?? {}) } };
  else vgSpec = vl.compile(spec, { config }).spec;

  const view = new vega.View(vega.parse(vgSpec), { renderer: "none" });
  await view.runAsync();
  const ppu = variant?.params?.pxPerUnit;
  if (ppu > 0 && meta.layout) {
    // pxPerUnit check: the value scale must render at exactly the requested px per unit
    const sc = view.scale(meta.layout.valueAxis === "width" ? "x" : "y");
    const d = sc.domain(), r = sc.range();
    const got = Math.abs(r[1] - r[0]) / (d[d.length - 1] - d[0]) / (meta.layout.unit === "percentage point" ? 100 : 1);
    const ok = Math.abs(got - ppu) / ppu < 0.005;
    console.log(`${ok ? "ok  " : "WARN"} ${id}: ${got.toFixed(3)} px per unit (pxPerUnit ${ppu})`);
    if (!ok) failed++;
  }
  let svg = await view.toSVG();
  const defs = patternDefs();
  if (defs) svg = svg.replace(/(<svg[^>]*>)/, `$1<defs>${defs}</defs>`);
  view.finalize();
  return write ? writeSvg(id, svg) : { id, svg };
}

function writeSvg(id, svg) {
  mkdirSync(outDir, { recursive: true });
  const svgPath = join(outDir, `${id}.svg`);
  writeFileSync(svgPath, svg);
  console.log(`svg  ${svgPath}`);
  return { id, svgPath, svg };
}

// usermeta.ibcs.previewGroups: members of one scale group rendered side by side, bottom-aligned
// (same baseline), each at its own container size, so the same px per unit is visible.
async function renderGroup(templatePath, group) {
  const parts = [];
  for (const [k, m] of group.members.entries()) parts.push(await renderOne(templatePath, { ...m, suffix: `${group.suffix}-${k}` }, false));
  const gap = 24, sizes = parts.map((p) => sizeOf(p.svg));
  const w = sizes.reduce((a, [x]) => a + x, 0) + gap * (parts.length - 1), h = Math.max(...sizes.map(([, y]) => y));
  let x = 0, body = "";
  parts.forEach((p, k) => {
    const [pw, ph] = sizes[k];
    body += p.svg.replace(/<svg /, `<svg x="${x}" y="${h - ph}" `);
    x += pw + gap;
  });
  const id = basename(templatePath).replace(/\.(vl|vg)\.json$/, "") + group.suffix;
  return writeSvg(id, `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${body}</svg>`);
}

function sizeOf(svg) {
  const m = /<svg[^>]*width="([\d.]+)"[^>]*height="([\d.]+)"/.exec(svg);
  return m ? [Math.ceil(+m[1]), Math.ceil(+m[2])] : [800, 600];
}

async function toPng({ id, svgPath, svg }) {
  const chrome = opt("--chrome", process.env.CHROME || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome");
  if (!existsSync(chrome)) { console.warn("no Chrome found, PNG skipped"); return; }
  const [w, h] = sizeOf(svg);
  const html = join(outDir, `.${id}.html`);
  writeFileSync(html, `<!doctype html><html><body style="margin:0;background:#fff">${svg}</body></html>`);
  const png = join(outDir, `${id}.png`);
  if (existsSync(png)) rmSync(png);
  const prof = join(outDir, ".chrome-profile");
  const p = spawn(chrome, ["--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
    `--user-data-dir=${prof}`, "--hide-scrollbars", "--force-device-scale-factor=2",
    `--window-size=${w},${h}`, `--screenshot=${png}`, pathToFileURL(html).href], { stdio: "ignore" });
  // Chrome on macOS writes the screenshot and then may not exit: poll for the file, then kill.
  for (let i = 0; i < 100 && !existsSync(png); i++) await new Promise((r) => setTimeout(r, 200));
  await new Promise((r) => setTimeout(r, 300));
  p.kill("SIGKILL");
  rmSync(html, { force: true });
  console.log(existsSync(png) ? `png  ${png}` : `png  FAILED for ${id}`);
}

// ---- --visual: live data for PBIR Deneb visuals --------------------------------------------
const unLiteral = (o) => {
  const v = o?.expr?.Literal?.Value;
  if (typeof v !== "string" || !v.startsWith("'")) throw new Error("vega object without a text literal");
  return v.slice(1, -1).replace(/''/g, "'");
};

function rowsOf(file) {
  let d = JSON.parse(readFileSync(file, "utf8"));
  if (d && !Array.isArray(d) && "text" in d && !("results" in d)) {
    if ((d.status_code ?? 200) >= 400) throw new Error(`${file}: request failed (${d.status_code})`);
    d = typeof d.text === "string" ? JSON.parse(d.text) : d.text;
  }
  if (Array.isArray(d)) return d;
  const res = d?.results?.[0];
  if (!res || res.error) throw new Error(`${file}: ${res?.error ? JSON.stringify(res.error).slice(0, 300) : "no results"}`);
  return res.tables[0].rows;
}

function unLiteralOr(prop) {
  // a PBIR literal {"expr": {"Literal": {"Value": "12D"}}} or a plain value
  return prop?.expr?.Literal?.Value ?? prop ?? "";
}

async function renderVisual(pair) {
  const [vPath, dPath] = pair.split("=");
  if (!dPath) throw new Error(`--visual ${pair}: give <visual.json>=<rows.json>`);
  const container = JSON.parse(readFileSync(vPath, "utf8"));
  const v = container.visual;
  const props = v?.objects?.vega?.[0]?.properties;
  if (!props) throw new Error(`${vPath}: not a Deneb visual with a spec`);
  const spec = JSON.parse(unLiteral(props.jsonSpec));
  const config = props.jsonConfig ? JSON.parse(unLiteral(props.jsonConfig)) : {};
  const isVega = props.provider && unLiteral(props.provider) === "vega";
  // executeQueries names columns "Table[Column]" and measures "[Measure]"; map both exactly, and a
  // bare name only when it is unambiguous (Date[Name] and Company[Name] must not collapse)
  const exact = new Map(), bare = new Map(), wanted = [];
  for (const p of v.query?.queryState?.dataset?.projections ?? []) {
    const kind = p.field?.Column ? "Column" : p.field?.Measure ? "Measure" : null;
    const prop = p.field?.[kind]?.Property ?? p.nativeQueryRef ?? p.queryRef.split(".").pop();
    const entity = p.field?.[kind]?.Expression?.SourceRef?.Entity;
    const name = p.displayName ?? p.nativeQueryRef ?? prop;
    wanted.push(name);
    if (kind === "Column" && entity) exact.set(`${entity}[${prop}]`, name);
    if (kind === "Measure") exact.set(`[${prop}]`, name);
    bare.set(prop, bare.has(prop) ? null : name);
  }
  const values = rowsOf(dPath).map((r) => Object.fromEntries(Object.entries(r).map(([k, val]) => {
    const b = /\[([^\]]+)\]$/.exec(k)?.[1] ?? k;
    return [exact.get(k) ?? bare.get(b) ?? b, val];
  })));
  const missing = wanted.filter((n) => !values.length || !(n in values[0]));
  if (missing.length) console.warn(`WARN ${basename(dirname(vPath))}: no column for ${missing.join(", ")}`);
  // the visual's own padding (visualContainerObjects.padding) is inside its position: Deneb gets
  // position minus padding, offset by the left/top padding (a theme-level padding is not in the file)
  const padObj = (v.visualContainerObjects ?? container.visualContainerObjects)?.padding?.[0]?.properties ?? {};
  const pad = (k) => { const n = parseFloat(String(unLiteralOr(padObj[k])).replace(/D$/, "")); return Number.isFinite(n) ? n : 0; };
  const { x: px = 0, y: py = 0 } = container.position;
  const width = container.position.width - pad("left") - pad("right");
  const height = container.position.height - pad("top") - pad("bottom");
  const x = px + pad("left"), y = py + pad("top");
  patterns.clear();
  replaceContainer(spec, width, height);
  injectData(spec, values, isVega);
  const vgSpec = isVega ? { ...spec, config: { ...config, ...(spec.config ?? {}) } } : vl.compile(spec, { config }).spec;
  const view = new vega.View(vega.parse(vgSpec), { renderer: "none" });
  await view.runAsync();
  let svg = await view.toSVG();
  const defs = patternDefs();
  if (defs) svg = svg.replace(/(<svg[^>]*>)/, `$1<defs>${defs}</defs>`);
  view.finalize();
  return { id: container.name ?? basename(dirname(vPath)), svg, x, y };
}

if (visualPairs.length) {
  try {
    const parts = [];
    for (const pair of visualPairs) parts.push(await renderVisual(pair));
    let r;
    if (parts.length === 1) r = writeSvg(parts[0].id, parts[0].svg);
    else {
      const x0 = Math.min(...parts.map((p) => p.x)), y0 = Math.min(...parts.map((p) => p.y));
      let w = 0, h = 0, body = "";
      for (const p of parts) {
        const [pw, ph] = sizeOf(p.svg);
        w = Math.max(w, p.x - x0 + pw); h = Math.max(h, p.y - y0 + ph);
        body += p.svg.replace(/<svg /, `<svg x="${p.x - x0}" y="${p.y - y0}" `);
      }
      r = writeSvg(opt("--name", "page"), `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="${Math.ceil(w)}" height="${Math.ceil(h)}" viewBox="0 0 ${Math.ceil(w)} ${Math.ceil(h)}">${body}</svg>`);
    }
    if (flags.has("--png")) await toPng(r);
  } catch (e) {
    console.error(`FAIL ${e.message}`);
    process.exit(1);
  }
  rmSync(join(outDir, ".chrome-profile"), { recursive: true, force: true });
  process.exit(0);
}

const dir = join(assets, "templates");
const templates = positional.length ? positional.map((p) => resolve(p))
  : readdirSync(dir).filter((f) => /\.(vl|vg)\.json$/.test(f)).sort().map((f) => join(dir, f));
for (const t of templates) {
  try {
    const spec = JSON.parse(readFileSync(t, "utf8"));
    for (const variant of [null, ...(spec.usermeta?.ibcs?.previewVariants ?? [])]) {
      const r = await renderOne(t, variant);
      if (flags.has("--png")) await toPng(r);
    }
    for (const group of spec.usermeta?.ibcs?.previewGroups ?? []) {
      const r = await renderGroup(t, group);
      if (flags.has("--png")) await toPng(r);
    }
  } catch (e) {
    failed++;
    console.error(`FAIL ${t}: ${e.message}`);
  }
}
rmSync(join(outDir, ".chrome-profile"), { recursive: true, force: true });
process.exit(failed ? 1 : 0);
