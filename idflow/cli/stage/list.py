from __future__ import annotations

import typer
import yaml
from pathlib import Path
import importlib.resources as ir
from typing import Dict, Optional


def _safe_pkg_root() -> Optional[Path]:
    try:
        return Path(ir.files("idflow"))
    except Exception:
        return None


def _read_yaml(path: Path) -> Optional[Dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, dict) else None
    except Exception:
        return None


def _collect_stage_map(dir_path: Optional[Path]) -> Dict[str, Dict]:
    result: Dict[str, Dict] = {}
    if not dir_path or not dir_path.exists():
        return result
    for yml in dir_path.glob("*.yml"):
        data = _read_yaml(yml)
        if not data:
            continue
        name = data.get("name")
        if not isinstance(name, str) or not name:
            continue
        result[name] = data
    return result


def list_stages(
    prefix: bool = typer.Option(False, "--prefix", help="Use compact prefix style (std|ext|cus)")
):
    """List available stages with status and origin classification."""
    # Discover package and project stage definitions
    pkg_root = _safe_pkg_root()
    pkg_stages_dir = pkg_root.joinpath("stages") if pkg_root else None
    proj_stages_dir = Path("stages")

    pkg_map = _collect_stage_map(pkg_stages_dir)
    proj_map = _collect_stage_map(proj_stages_dir)

    all_names = sorted(set(pkg_map.keys()) | set(proj_map.keys()))

    if not all_names:
        typer.echo("No stages found")
        return

    # Build rows first
    rows = []
    for name in all_names:
        in_pkg = name in pkg_map
        in_proj = name in proj_map

        # Determine effective 'active' flag (project overrides package)
        active = True
        if in_pkg:
            active = bool(pkg_map[name].get("active", True))
        if in_proj and "active" in proj_map[name]:
            active = bool(proj_map[name]["active"])  # explicit override

        status_label = "active" if active else "inactive"

        if in_pkg and in_proj:
            origin = "extended"
            origin_tag = "ext"
        elif in_pkg:
            origin = "standard"
            origin_tag = "std"
        else:
            origin = "custom"
            origin_tag = "cus"

        rows.append((name, status_label, origin, origin_tag))

    if prefix:
        for name, status_label, _origin, origin_tag in rows:
            typer.echo(f"({origin_tag}) {name} [{status_label}]")
        return

    # Aligned table-like output
    name_w = max(len(r[0]) for r in rows)
    status_w = max(len(r[1]) for r in rows)
    origin_w = max(len(r[2]) for r in rows)

    for name, status_label, origin, _tag in rows:
        typer.echo(f"{name.ljust(name_w)}  {status_label.ljust(status_w)}  {origin.ljust(origin_w)}")


