from __future__ import annotations

import typer
from pathlib import Path
from typing import Dict, Optional
from idflow.core.resource_resolver import ResourceResolver
import yaml


def _read_yaml(path: Path) -> Optional[Dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, dict) else None
    except Exception:
        return None

def list_stages():
    """List available stages with status and origin classification."""
    # Discover stages via ResourceResolver composite (overlay + classifier)
    rr = ResourceResolver()
    name_extractor = rr.name_from_yaml_key("name")
    flat_by_name, classify = rr.build_index_with_classifier(
        subdir="stages",
        pattern="*.yml",
        name_extractor=name_extractor,
        item_type="file"
    )

    if not flat_by_name:
        typer.echo("No stages found")
        return

    # Build rows: use effective file from overlay index to read 'active'
    rows = []
    for name in sorted(flat_by_name.keys()):
        yml_path = flat_by_name[name]
        data = _read_yaml(yml_path) or {}
        active = bool(data.get("active", True))
        status_label = "active" if active else "inactive"
        origin, origin_tag = classify(name)
        rows.append((name, status_label, origin, origin_tag))

    # Aligned table-like output
    name_w = max(len(r[0]) for r in rows)
    status_w = max(len(r[1]) for r in rows)
    origin_w = max(len(r[2]) for r in rows)

    for name, status_label, origin, _tag in rows:
        typer.echo(f"{name.ljust(name_w)}  {status_label.ljust(status_w)}  {origin.ljust(origin_w)}")

