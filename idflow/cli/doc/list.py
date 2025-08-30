from __future__ import annotations
import json
import typer
from pathlib import Path
from typing import Any, Dict, List
from idflow.core.io import read_frontmatter
from idflow.core.filters import match_filter
from idflow.core.repo import doc_paths

app = typer.Typer(add_completion=False)

def _parse_prop_eq_val(arg: str, flag: str) -> tuple[str, str]:
    if "=" not in arg:
        raise typer.BadParameter(f"{flag} erwartet property=EXPR, nicht: {arg}")
    return arg.split("=", 1)

def _get_dot(fm: Dict[str, Any], path: str) -> Any:
    cur: Any = fm
    for p in path.split("."):
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return None
    return cur

@app.command("list")
def list_docs(
    base_dir: str = typer.Option("data", "--base-dir"),
    filter_: List[str] = typer.Option(None, "--filter", help='property=EXPR (z.B. title="observ*" | priority=">0.5" | meta.owner="exists" | doc-ref="key")'),
    col: List[str] = typer.Option(None, "--col", help="Ausgabespalten (default: uuid)"),
):
    # Extract default values from typer objects for direct function calls
    if hasattr(base_dir, 'default'):
        base_dir = base_dir.default
    if hasattr(filter_, 'default'):
        filter_ = filter_.default
    if hasattr(col, 'default'):
        col = col.default
    docs = []
    for doc_path in doc_paths(Path(base_dir)):
        fm, _ = read_frontmatter(doc_path)
        if not fm:
            continue
        fm["_doc_path"] = doc_path
        docs.append(fm)

    def passes(fm: Dict[str, Any]) -> bool:
        for f in filter_ or []:
            prop, expr = _parse_prop_eq_val(f, "--filter")
            prop = prop.strip()
            expr = expr.strip().strip('"').strip("'")
            if prop == "doc-ref":
                keys = {x.get("key") for x in fm.get("_doc_refs", []) if isinstance(x, dict)}
                if expr not in keys:
                    return False
            elif prop == "file-ref":
                keys = {x.get("key") for x in fm.get("_file_refs", []) if isinstance(x, dict)}
                if expr not in keys:
                    return False
            else:
                val = _get_dot(fm, prop)
                if val is None and expr != "exists":
                    return False
                if not match_filter(val, expr):
                    return False
        return True

    filtered = [fm for fm in docs if passes(fm)]
    cols = col or ["id"]

    for fm in filtered:
        row = []
        for c in cols:
            if c in ("id", "uuid"):
                row.append(fm.get("id", ""))
            elif c == "status":
                row.append(fm.get("status", ""))
            elif c in ("_doc_refs", "doc-keys", "doc_keys", "doc-ref"):
                keys = sorted({x.get("key") for x in fm.get("_doc_refs", []) if isinstance(x, dict) and "key" in x})
                row.append(",".join(keys))
            elif c in ("_file_refs", "file-keys", "file_keys", "file-ref"):
                keys = sorted({x.get("key") for x in fm.get("_file_refs", []) if isinstance(x, dict) and "key" in x})
                row.append(",".join(keys))
            else:
                val = _get_dot(fm, c)
                if isinstance(val, (list, dict)):
                    row.append(json.dumps(val, ensure_ascii=False))
                else:
                    row.append("" if val is None else str(val))
        typer.echo(" | ".join(row))

