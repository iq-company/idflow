from __future__ import annotations
import json
import typer
from pathlib import Path
from typing import Any, Dict, List, Optional
from idflow.core.fs_markdown import FSMarkdownDocument
from idflow.core.filters import match_filter

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
    filter_: List[str] = typer.Option(None, "--filter", help='property=EXPR (z.B. title="observ*" | priority=">0.5" | meta.owner="exists" | doc-ref="key")'),
    col: List[str] = typer.Option(None, "--col", help="Ausgabespalten (default: uuid)"),
    status: Optional[str] = None,
    columns: Optional[List[str]] = None,
    doc_ref: Optional[str] = None,
    file_ref: Optional[str] = None,
    priority: Optional[str] = None,
    exists: Optional[str] = None,
    tags: Optional[str] = None,
):
    # Extract default values from typer objects for direct function calls
    if hasattr(filter_, 'default'):
        filter_ = filter_.default
    if hasattr(col, 'default'):
        col = col.default

    # Build filters from individual parameters
    filters = []
    if status:
        filters.append(f"status={status}")
    if priority:
        filters.append(f"priority={priority}")
    if exists:
        filters.append(f"{exists}=exists")
    if doc_ref:
        filters.append(f"doc_ref={doc_ref}")
    if file_ref:
        filters.append(f"file_ref={file_ref}")
    if tags:
        filters.append(f"tags={tags}")

    # Combine with explicit filters
    if filter_:
        filters.extend(filter_)

    # Use columns parameter if provided, otherwise use col
    cols = columns or col or ["id"]

    # Convert filters to ORM query format
    query_filters = {}
    for f in filters:
        prop, expr = _parse_prop_eq_val(f, "--filter")
        prop = prop.strip()
        expr = expr.strip().strip('"').strip("'")

        if prop == "doc-ref":
            query_filters["doc_ref"] = expr
        elif prop == "file-ref":
            query_filters["file_ref"] = expr
        elif expr == "exists":
            query_filters["exists"] = prop
        else:
            # For simple equality filters, we can use the property directly
            # For complex filters like "observ*", we'll need to post-filter
            query_filters[prop] = expr

    # Use ORM to find documents
    docs = FSMarkdownDocument.where(**query_filters)

    # Post-filter for complex expressions that the ORM can't handle
    if filter_:
        filtered = []
        for doc in docs:
            passes = True
            for f in filters:
                prop, expr = _parse_prop_eq_val(f, "--filter")
                prop = prop.strip()
                expr = expr.strip().strip('"').strip("'")

                if prop == "doc-ref":
                    keys = {x.key for x in doc.doc_refs}
                    if expr not in keys:
                        passes = False
                        break
                elif prop == "file-ref":
                    keys = {x.key for x in doc.file_refs}
                    if expr not in keys:
                        passes = False
                        break
                else:
                    val = _get_dot(doc._data, prop)
                    if val is None and expr != "exists":
                        passes = False
                        break
                    if not match_filter(val, expr):
                        passes = False
                        break

            if passes:
                filtered.append(doc)
        docs = filtered

    # Output results
    if not docs:
        typer.echo("No documents found.")
        return

    # Convert to list of dictionaries for output
    result_docs = []
    for doc in docs:
        doc_dict = doc.to_dict()
        doc_dict["_doc_path"] = str(doc.doc_file)
        result_docs.append(doc_dict)

    # Output in requested format
    if len(cols) == 1 and cols[0] == "id":
        # Simple ID list
        for doc in docs:
            typer.echo(doc.id)
    else:
        # Detailed output
        for doc in result_docs:
            output = {}
            for col in cols:
                if col == "id":
                    output[col] = doc.get("id", "")
                elif col == "status":
                    output[col] = doc.get("status", "")
                elif col == "body":
                    output[col] = doc.get("body", "")[:100] + "..." if len(doc.get("body", "")) > 100 else doc.get("body", "")
                else:
                    output[col] = doc.get(col, "")

            if len(cols) == 1:
                typer.echo(output[cols[0]])
            else:
                typer.echo(json.dumps(output, ensure_ascii=False))

