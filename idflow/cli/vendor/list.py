from __future__ import annotations
import typer
from pathlib import Path
from idflow.core.resource_resolver import ResourceResolver


def list_vendor():
    # Use ResourceResolver to show overlay availability and origin classification
    rr = ResourceResolver()

    def _print_section(title: str, rows: list[tuple[str, str]]):
        typer.echo("\n" + title)
        if not rows:
            typer.echo("  (empty)")
            return
        name_w = max(len(r[0]) for r in rows)
        origin_w = max(len(r[1]) for r in rows)
        for name, origin in sorted(rows, key=lambda x: x[0]):
            typer.echo(f"  {name.ljust(name_w)}  {origin.ljust(origin_w)}")

    # tasks (directory-based)
    lib_t, vend_t, proj_t = rr.names_by_base("tasks", "*", name_extractor=None, item_type="dir")
    task_names = sorted(set().union(lib_t, vend_t, proj_t))
    task_rows: list[tuple[str, str]] = []
    for n in task_names:
        origin, tag = rr.classify_origin_from_sets(n, lib_t, vend_t, proj_t)
        task_rows.append((n, origin))
    _print_section("tasks", task_rows)

    # workflows (directory-based)
    lib_w, vend_w, proj_w = rr.names_by_base("workflows", "*", name_extractor=None, item_type="dir")
    wf_names = sorted(set().union(lib_w, vend_w, proj_w))
    wf_rows: list[tuple[str, str]] = []
    for n in wf_names:
        origin, tag = rr.classify_origin_from_sets(n, lib_w, vend_w, proj_w)
        wf_rows.append((n, origin))
    _print_section("workflows", wf_rows)

    # stages (file-based, name from YAML)
    stage_extractor = rr.name_from_yaml_key("name")
    lib_s, vend_s, proj_s = rr.names_by_base("stages", "*.yml", stage_extractor, item_type="file")
    stage_names = sorted(set().union(lib_s, vend_s, proj_s))
    stage_rows: list[tuple[str, str]] = []
    for n in stage_names:
        origin, tag = rr.classify_origin_from_sets(n, lib_s, vend_s, proj_s)
        stage_rows.append((n, origin))
    _print_section("stages", stage_rows)


