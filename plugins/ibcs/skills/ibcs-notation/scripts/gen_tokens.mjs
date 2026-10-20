#!/usr/bin/env node
// gen_tokens.mjs - write the effective IBCS design tokens as a TypeScript, JSON or CSS module.
//
// Same algorithm as the Python resolver in references/tokens-in-practice.md and the ibcs-review
// linter: read the bundled ibcs-tokens.json, deep-merge the organisation's
// ibcs-tokens.overrides.json on top (objects key by key, override wins, arrays replaced), then
// resolve "{a.b.c}" aliases after the merge, so an overridden colour propagates to its aliases.
// The output keeps only resolved values (no $description / $extensions / $type).
//
// Usage (Node 18+, no dependencies):
//   node gen_tokens.mjs --out src/ibcs/tokens.generated.ts
//   node gen_tokens.mjs --out tokens.effective.json --overrides path/to/ibcs-tokens.overrides.json
//   node gen_tokens.mjs --out src/ibcs/tokens.generated.css
// Options:
//   --out FILE         .ts (typed `as const` module), .json, or .css (custom properties); required
//   --tokens FILE      base token file (default: ../assets/ibcs-tokens.json next to this script)
//   --overrides FILE   organisation overrides (default: the first ibcs-tokens.overrides.json in the
//                      current directory or one of its parents)
//   --no-overrides     ignore any overrides file
//   --prefix NAME      CSS custom-property prefix (default: ibcs)
// Exit code: 0 = written, 2 = usage, parse or alias error. MIT.

import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, extname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const OVERRIDES_NAME = "ibcs-tokens.overrides.json";
const here = dirname(fileURLToPath(import.meta.url));

function fail(message) {
  console.error(`error: ${message}`);
  process.exit(2);
}

function parseArgs(argv) {
  const opts = { out: null, tokens: resolve(here, "../assets/ibcs-tokens.json"), overrides: undefined, prefix: "ibcs" };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const next = () => (i + 1 < argv.length ? argv[++i] : fail(`${a} needs a value`));
    if (a === "--out") opts.out = next();
    else if (a === "--tokens") opts.tokens = next();
    else if (a === "--overrides") opts.overrides = next();
    else if (a === "--no-overrides") opts.overrides = null;
    else if (a === "--prefix") opts.prefix = next();
    else if (a === "-h" || a === "--help") {
      console.log(readFileSync(fileURLToPath(import.meta.url), "utf8").split("\n").slice(1, 21).map((l) => l.replace(/^\/\/ ?/, "")).join("\n"));
      process.exit(0);
    } else fail(`unknown argument ${a}`);
  }
  if (!opts.out) fail("--out FILE is required (.ts, .json or .css)");
  if (!existsSync(opts.tokens)) {
    fail(`token file ${opts.tokens} not found; a copied script needs --tokens path/to/ibcs-tokens.json`);
  }
  return opts;
}

function readJson(file) {
  try {
    return JSON.parse(readFileSync(file, "utf8").replace(/^﻿/, ""));
  } catch (e) {
    fail(`cannot read ${file}: ${e.message}`);
  }
}

function findOverrides(start) {
  let dir = resolve(start);
  for (;;) {
    const cand = resolve(dir, OVERRIDES_NAME);
    if (existsSync(cand)) return cand;
    const up = dirname(dir);
    if (up === dir) return null;
    dir = up;
  }
}

const isObj = (x) => x !== null && typeof x === "object" && !Array.isArray(x);

export function merge(base, over) {
  if (isObj(base) && isObj(over)) {
    const out = { ...base };
    for (const [k, v] of Object.entries(over)) out[k] = k in base ? merge(base[k], v) : v;
    return out;
  }
  return over;
}

const ALIAS = /^\{([^{}]+)\}$/;

export function value(tokens, path, depth = 0) {
  let node = tokens;
  for (const part of path.split(".")) {
    node = isObj(node) ? node[part] : undefined;
    if (node === undefined) throw new Error(`token not found: ${path}`);
  }
  if (!isObj(node) || !("$value" in node)) throw new Error(`not a token (no $value): ${path}`);
  const v = node.$value;
  if (typeof v === "string" && ALIAS.test(v)) {
    if (depth >= 10) throw new Error(`alias chain too deep (cycle?) at ${path}`);
    return value(tokens, v.match(ALIAS)[1], depth + 1);
  }
  return v;
}

// Every token path with its resolved value, in file order.
export function flatten(tokens) {
  const flat = [];
  (function walk(node, path) {
    if (!isObj(node)) return;
    if ("$value" in node) {
      flat.push([path, value(tokens, path)]);
      return;
    }
    for (const [k, v] of Object.entries(node)) if (!k.startsWith("$")) walk(v, path ? `${path}.${k}` : k);
  })(tokens, "");
  return flat;
}

export function nest(flat) {
  const out = {};
  for (const [path, v] of flat) {
    const parts = path.split(".");
    let n = out;
    for (const p of parts.slice(0, -1)) n = n[p] ??= {};
    n[parts.at(-1)] = v;
  }
  return out;
}

function cssValue(path, v) {
  if (Array.isArray(v)) return v.map((x) => (typeof x === "string" && /\s/.test(x) ? `"${x}"` : x)).join(", ");
  if (typeof v === "number" && /(?:\.px|Px)$|Px\.(?:min|max)$/.test(path)) return `${v}px`;
  return String(v);
}

function main() {
  const o = parseArgs(process.argv.slice(2));
  if (!existsSync(o.tokens)) fail(`${o.tokens} does not exist`);
  let ovPath = o.overrides === undefined ? findOverrides(process.cwd()) : o.overrides;
  if (ovPath && !existsSync(ovPath)) fail(`${ovPath} does not exist`);
  if (ovPath && resolve(ovPath) === resolve(o.tokens)) ovPath = null;
  const tokens = ovPath ? merge(readJson(o.tokens), readJson(ovPath)) : readJson(o.tokens);
  let flat;
  try {
    flat = flatten(tokens);
  } catch (e) {
    fail(e.message);
  }
  const ext = extname(o.out).toLowerCase();
  let text;
  if (ext === ".ts") {
    text = `// GENERATED by gen_tokens.mjs (ibcs-notation skill) from the effective IBCS tokens. Do not edit;\n` +
      `// change ${OVERRIDES_NAME} and regenerate.\n` +
      `export const tokens = ${JSON.stringify(nest(flat), null, 2)} as const;\n` +
      `export type IbcsTokens = typeof tokens;\nexport default tokens;\n`;
  } else if (ext === ".json") {
    text = `${JSON.stringify(nest(flat), null, 2)}\n`;
  } else if (ext === ".css") {
    const lines = flat
      .filter(([, v]) => typeof v === "number" || typeof v === "string" || Array.isArray(v))
      .filter(([p]) => /^(color|typography|layout|stroke)\./.test(p))
      .map(([p, v]) => `  --${o.prefix}-${p.replaceAll(".", "-")}: ${cssValue(p, v)};`);
    text = `/* GENERATED by gen_tokens.mjs (ibcs-notation skill). Do not edit. */\n:root {\n${lines.join("\n")}\n}\n`;
  } else {
    fail(`--out must end in .ts, .json or .css (got ${o.out})`);
  }
  mkdirSync(dirname(resolve(o.out)), { recursive: true });
  writeFileSync(o.out, text);
  console.log(`${o.out}: ${flat.length} tokens${ovPath ? ` (overrides: ${ovPath})` : " (no overrides)"}`);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
