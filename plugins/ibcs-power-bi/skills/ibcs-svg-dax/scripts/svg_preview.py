#!/usr/bin/env python3
"""Preview SVG-in-DAX measure results outside Power BI: HTML page plus an optional PNG.

    python3 -I svg_preview.py result.json --out ./svg-preview [--png] [--chrome PATH] [--scale 2]

result.json is either
  - the JSON response of the Power BI REST API "Datasets - Execute Queries" (executeQueries; the
    {"status_code", "text"} wrapper that `fab api` prints is unwrapped), whose
    query evaluated the SVG measure, e.g.
        DEFINE MEASURE 'Sales'[SVG Card Revenue] = <the measure expression>
        EVALUATE SUMMARIZECOLUMNS ( 'Company'[Company Code], "svg", [SVG Card Revenue] )
    (every text cell that starts with data:image/svg+xml is drawn, labelled with the row's other
    columns), or
  - a plain JSON list of SVG strings / {"label": ..., "svg": ...} objects (sample values), or
  - a plain JSON list of row objects (e.g. rows saved from a query): every data:image/svg+xml cell
    of a row is drawn, labelled with the row's other cells, as for executeQueries.

The SVGs are written inline into one HTML page (a data URI in an <img> would cut the string at the
first '#', so the page inlines the markup after the "data:image/svg+xml;utf8," prefix), each in a
box of its own width/height, on a white ground. --png screenshots the page with headless Chrome
(default macOS path; pass --chrome or set CHROME elsewhere). Nothing is sent anywhere.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.parse
from pathlib import Path

PREFIX = re.compile(r"^data:image/svg\+xml(;charset=utf-8)?(;utf8)?(;base64)?,", re.I)
DEFAULT_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def svg_of(cell: str) -> str | None:
    m = PREFIX.match(cell or "")
    if not m:
        return None
    body = cell[m.end():]
    if m.group(3):
        import base64
        return base64.b64decode(body).decode("utf-8")
    return urllib.parse.unquote(body) if "%3C" in body[:20].upper() else body


def unwrap(data):
    """`fab api` wraps the REST response as {"status_code": …, "text": {…} or "…json…"}."""
    if isinstance(data, dict) and "text" in data and "results" not in data:
        if data.get("status_code", 200) >= 400:
            raise SystemExit(f"request failed ({data['status_code']}): {json.dumps(data['text'])[:500]}")
        text = data["text"]
        return json.loads(text) if isinstance(text, str) else text
    return data


def items_from(data) -> list[tuple[str, str]]:
    out = []
    data = unwrap(data)
    if isinstance(data, dict) and "results" not in data:
        raise SystemExit(f"not an executeQueries response or a list of SVGs (keys: {sorted(data)[:8]})")
    if isinstance(data, dict):  # executeQueries response
        for res in data["results"]:
            if res.get("error"):
                raise SystemExit(f"query error: {json.dumps(res['error'])[:500]}")
            for table in res.get("tables", []):
                for row in table.get("rows", []):
                    out += row_items(row)
        return out
    for i, x in enumerate(data):
        if isinstance(x, str):
            out.append((str(i + 1), svg_of(x) or x))
        elif isinstance(x, dict) and "svg" in x:
            out.append((x.get("label", str(i + 1)), svg_of(x["svg"]) or x["svg"]))
        elif isinstance(x, dict):  # a query row: draw its SVG cells
            out += row_items(x)
        else:
            raise SystemExit(f"item {i + 1} is neither an SVG string nor an object")
    return out


def row_items(row: dict) -> list[tuple[str, str]]:
    """Every data:image/svg+xml cell of one row, labelled with the row's other cells."""
    svgs = [(k, svg_of(v)) for k, v in row.items() if isinstance(v, str)]
    label = " · ".join(f"{v}" for k, v in row.items() if not (isinstance(v, str) and svg_of(v)))
    return [(f"{label} {k}".strip(), s) for k, s in svgs if s]


def size_of(svg: str) -> tuple[float, float]:
    w = re.search(r"<svg[^>]*\swidth=['\"]([\d.]+)", svg)
    h = re.search(r"<svg[^>]*\sheight=['\"]([\d.]+)", svg)
    if w and h:
        return float(w[1]), float(h[1])
    vb = re.search(r"viewBox=['\"][\d.\s-]*?([\d.]+)\s+([\d.]+)['\"]", svg)
    return (float(vb[1]), float(vb[2])) if vb else (200.0, 40.0)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("result")
    ap.add_argument("--out", default="svg-preview")
    ap.add_argument("--png", action="store_true")
    ap.add_argument("--chrome", default=os.environ.get("CHROME", DEFAULT_CHROME))
    ap.add_argument("--scale", type=float, default=2.0, help="device scale factor of the PNG")
    a = ap.parse_args()

    items = items_from(json.loads(Path(a.result).read_text(encoding="utf-8")))
    if not items:
        raise SystemExit("no data:image/svg+xml cells found")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    boxes, total_h, max_w = [], 0.0, 0.0
    for n, (label, svg) in enumerate(items):
        # every cell is its own document in Power BI; inlined on one page, ids such as the hatch
        # pattern 'h' would clash across rows, so suffix them per item
        for ident in set(re.findall(r"\bid=['\"]([^'\"]+)['\"]", svg)):
            svg = re.sub(rf"(\bid=['\"]){re.escape(ident)}(['\"])", rf"\g<1>{ident}-{n}\g<2>", svg)
            svg = svg.replace(f"url(#{ident})", f"url(#{ident}-{n})")
        w, h = size_of(svg)
        if not re.search(r"<svg[^>]*\swidth=", svg):  # viewBox only: give it a box of that size
            svg = svg.replace("<svg", f"<svg width='{w}' height='{h}'", 1)
        boxes.append(f"<div class='row'><div class='lbl'>{html.escape(label)}</div>"
                     f"<div class='cell' style='width:{w}px;height:{h}px'>{svg}</div></div>")
        total_h += h + 12
        max_w = max(max_w, w)
    page = ("<!doctype html><html><head><meta charset='utf-8'><style>"
            "body{margin:8px;background:#fff;font:11px sans-serif;color:#595959}"
            ".row{display:flex;align-items:center;gap:8px;margin-bottom:4px}"
            ".lbl{width:160px;text-align:right}.cell{outline:1px dotted #ddd}"
            "</style></head><body>" + "".join(boxes) + "</body></html>")
    page_path = out / "preview.html"
    page_path.write_text(page, encoding="utf-8")
    print(f"wrote {page_path} ({len(items)} SVGs)")
    if a.png:
        if not Path(a.chrome).exists():
            print("no Chrome found; PNG skipped (pass --chrome)", file=sys.stderr)
            return 1
        png = out / "preview.png"
        png.unlink(missing_ok=True)
        with tempfile.TemporaryDirectory() as prof:
            p = subprocess.Popen([a.chrome, "--headless=new", "--disable-gpu", "--no-first-run",
                                  "--no-default-browser-check", f"--user-data-dir={prof}", "--hide-scrollbars",
                                  f"--force-device-scale-factor={a.scale}",
                                  f"--window-size={int(max_w + 200)},{int(total_h + 24)}",
                                  f"--screenshot={png.resolve()}", page_path.resolve().as_uri()],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            for _ in range(100):  # Chrome on macOS may not exit after the screenshot
                if png.exists():
                    break
                time.sleep(0.2)
            time.sleep(0.3)
            p.kill()
        print(f"wrote {png}" if png.exists() else "PNG failed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
