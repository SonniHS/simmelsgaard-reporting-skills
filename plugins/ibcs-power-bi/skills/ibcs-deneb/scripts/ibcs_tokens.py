"""Shared loader for the IBCS design tokens (stdlib only).

Rules: deep-merge an optional overrides file over the tokens (objects merge key by key, the
override wins, arrays replace wholesale), THEN resolve "{a.b.c}" aliases, then strip the DTCG
metadata so `tokens["color"]["scenario"]["ac"] == "#404040"`.

The default token file is the one bundled with this skill (../assets/ibcs-tokens.json). Keep your
organisation's changes in your own `ibcs-tokens.overrides.json` and pass it with --overrides;
never edit the bundled file.

    import ibcs_tokens
    tok = ibcs_tokens.load(tokens=None, overrides="my/ibcs-tokens.overrides.json")
    ibcs_tokens.get(tok, "color.scenario.ac")
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

DEFAULT_TOKENS = Path(__file__).resolve().parent.parent / "assets" / "ibcs-tokens.json"

_ALIAS = re.compile(r"^\{([^}]+)\}$")


def _is_obj(v: Any) -> bool:
    return isinstance(v, dict)


def deep_merge(base: Any, over: Any) -> Any:
    if not (_is_obj(base) and _is_obj(over)):
        return over
    out = dict(base)
    for k, v in over.items():
        out[k] = deep_merge(base[k], v) if k in base else v
    return out


def strip(node: Any) -> Any:
    """A node with $value becomes its value; other $-keys are dropped."""
    if not _is_obj(node):
        return node
    if "$value" in node:
        return node["$value"]
    return {k: strip(v) for k, v in node.items() if not k.startswith("$")}


def get(root: Any, path: str, default: Any = KeyError) -> Any:
    cur = root
    for part in path.split("."):
        if _is_obj(cur) and part in cur:
            cur = cur[part]
        else:
            if default is KeyError:
                raise KeyError(f"token not found: {path}")
            return default
    return cur


def resolve(root: Any, node: Any, seen: tuple[str, ...] = ()) -> Any:
    if isinstance(node, str):
        m = _ALIAS.match(node)
        if not m:
            return node
        path = m.group(1)
        if path in seen:
            raise ValueError(f"alias cycle: {' -> '.join(seen + (path,))}")
        return resolve(root, get(root, path), seen + (path,))
    if isinstance(node, list):
        return [resolve(root, x, seen) for x in node]
    if _is_obj(node):
        return {k: resolve(root, v, seen) for k, v in node.items()}
    return node


def source_paths(tokens: Path | str | None = None, overrides: Path | str | None = None) -> list[Path]:
    """The files that feed `load`, in merge order. A missing overrides file is an error."""
    out = [Path(tokens) if tokens else DEFAULT_TOKENS]
    if overrides:
        ov = Path(overrides)
        if not ov.exists():
            raise SystemExit(f"overrides file not found: {ov}")
        out.append(ov)
    return out


def load_raw(tokens: Path | str | None = None, overrides: Path | str | None = None) -> dict:
    """Merged tokens with metadata and aliases intact."""
    paths = source_paths(tokens, overrides)
    raw = json.loads(paths[0].read_text(encoding="utf-8"))
    for p in paths[1:]:
        raw = deep_merge(raw, json.loads(p.read_text(encoding="utf-8")))
    return raw


def load(tokens: Path | str | None = None, overrides: Path | str | None = None) -> dict:
    """Effective tokens: merged, metadata stripped, aliases resolved."""
    stripped = strip(load_raw(tokens, overrides))
    return resolve(stripped, stripped)
