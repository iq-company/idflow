from __future__ import annotations
import typer
from typing import List

from idflow.core.optional_deps import (
    get_available_features,
    get_installed_optional_dependencies,
    get_feature_origin_map,
)
from idflow.core.stage_definitions import get_stage_definitions


app = typer.Typer(help="Manage extras (optional dependencies)")


def _gather_required_features_with_stages() -> dict[str, list[str]]:
    """Return mapping feature -> list of stage names that require it (only active stages)."""
    stage_defs = get_stage_definitions()
    mapping: dict[str, set[str]] = {}
    for stage_name in stage_defs.list_definitions():
        sd = stage_defs.get_definition(stage_name)
        if not sd or not sd.active or not sd.requirements:
            continue
        feats = (sd.requirements.extras) or []
        for feature in feats:
            mapping.setdefault(feature, set()).add(stage_name)
    return {k: sorted(list(v)) for k, v in mapping.items()}


def list_extras():
    """List extras: available, installed, required (by active stages), missing, extraneous."""
    available_map = get_available_features()
    available = sorted(available_map.keys())
    installed = get_installed_optional_dependencies()
    required_map = _gather_required_features_with_stages()
    required = sorted(required_map.keys())

    installed_set = set(installed)
    required_set = set(required)

    missing = sorted(list(required_set - installed_set))
    extraneous = sorted(list(installed_set - required_set))

    typer.echo("Available extras:")
    if available:
        origin_map = get_feature_origin_map()
        rows = [(f, origin_map.get(f, 'custom')) for f in available]
        name_w = max(len(r[0]) for r in rows)
        origin_w = max(len(r[1]) for r in rows)
        for name, origin in rows:
            typer.echo(f"  {name.ljust(name_w)}  {origin.ljust(origin_w)}")
    else:
        typer.echo("  (none)")

    typer.echo("\nInstalled extras:")
    if installed:
        for f in installed:
            typer.echo(f"  {f}")
    else:
        typer.echo("  (none)")

    typer.echo("\nRequired by active stages:")
    if required:
        for f in required:
            stages = required_map.get(f, [])
            suffix = f" ({', '.join(stages)})" if stages else ""
            typer.echo(f"  {f}{suffix}")
    else:
        typer.echo("  (none)")

    typer.echo("\nMissing extras:")
    if missing:
        for f in missing:
            typer.echo(f"  {f}")
    else:
        typer.echo("  (none)")

    typer.echo("\nExtraneous extras (installed but not required):")
    if extraneous:
        for f in extraneous:
            typer.echo(f"  {f}")
    else:
        typer.echo("  (none)")


app.command("list")(list_extras)


@app.command("install")
def install_extras(
    features: List[str] = typer.Argument(None, help="Extras to install; if omitted installs missing"),
):
    """Install missing extras via pip. Package extras via idflow[...], project-defined extras as package lists."""
    import subprocess, sys
    available_map = get_available_features()
    installed = set(get_installed_optional_dependencies())
    origin_map = get_feature_origin_map()
    if not features:
        # Default: install only missing required extras (from active stages)
        required = set(_gather_required_features_with_stages().keys())
        features = sorted(list(required - installed))
    to_install = [f for f in features if f in available_map and f not in installed]
    if not to_install:
        typer.echo("Nothing to install")
        return

    extras = [f for f in to_install if origin_map.get(f) == 'extra']
    project_feats = [f for f in to_install if origin_map.get(f) != 'extra']

    # 1) Install package extras in one pip command via idflow[...]
    if extras:
        cmd = [sys.executable, "-m", "pip", "install", f"idflow[{','.join(extras)}]"]
        typer.echo("Running: " + " ".join(cmd))
        subprocess.run(cmd, check=False)

    # 2) Install project-defined extras directly (flattened packages)
    if project_feats:
        pkgs: list[str] = []
        for f in project_feats:
            pkgs.extend(available_map.get(f, []))
        if pkgs:
            cmd = [sys.executable, "-m", "pip", "install", *pkgs]
            typer.echo("Running: " + " ".join(cmd))
            subprocess.run(cmd, check=False)


@app.command("purge")
def purge_extras():
    """Show uninstall suggestions for extraneous extras (manual confirmation)."""
    import subprocess, sys
    import importlib.metadata
    import re
    available_map = get_available_features()
    installed = set(get_installed_optional_dependencies())
    required = set(_gather_required_features_with_stages().keys())
    extraneous = sorted(list(installed - required))
    if not extraneous:
        typer.echo("No extraneous extras installed")
        return
    # Helper to extract base distribution name from requirement spec
    def _extract_name(req: str) -> str:
        name = req.split(";", 1)[0].split("[", 1)[0]
        for sep in ["==", ">=", "<=", "~=", ">", "<", "!=", "==="]:
            if sep in name:
                name = name.split(sep, 1)[0]
        return name.strip()

    # Collect distributions that must be kept because they are required by active extras
    protected_dists = set()
    for f in required:
        for req in available_map.get(f, []):
            protected_dists.add(_extract_name(req))

    # Also protect base (non-extra) runtime dependencies of idflow itself
    try:
        dist = importlib.metadata.distribution("idflow")
        lines = dist.metadata.as_string().splitlines()
        req_re = re.compile(r"^Requires-Dist:\s*([^;\s]+)(?:;\s*(.*))?$")
        for line in lines:
            if not line.startswith("Requires-Dist:"):
                continue
            m = req_re.match(line)
            if not m:
                continue
            requirement = m.group(1)
            marker = m.group(2) or ""
            # Skip entries that are only for extras (we only want base deps)
            if "extra ==" in marker:
                continue
            protected_dists.add(_extract_name(requirement))
    except Exception:
        # Best-effort; if metadata isn't available, we just skip base protection
        pass

    # We cannot reliably uninstall extras as a group; suggest uninstalling their dists,
    # but exclude any distribution that is still required by protected sets.
    # However, if a package is ONLY used by extraneous extras, it should be uninstallable.

    # Find packages that are only used by extraneous extras
    extraneous_packages = set()
    required_packages = set()

    # Collect packages from extraneous extras
    for f in extraneous:
        for req in available_map.get(f, []):
            extraneous_packages.add(_extract_name(req))

    # Collect packages from required extras
    for f in required:
        for req in available_map.get(f, []):
            required_packages.add(_extract_name(req))

    dists = set()
    for f in extraneous:
        for req in available_map.get(f, []):
            name = _extract_name(req)
            # Allow uninstall if package is only used by extraneous extras
            if name not in required_packages and name not in protected_dists:
                dists.add(name)
            elif name in extraneous_packages and name not in required_packages:
                # Package is only in extraneous extras, allow uninstall even if "protected"
                dists.add(name)

    if not dists:
        typer.echo("No uninstallable distributions found for extraneous extras")
        return
    cmd = [sys.executable, "-m", "pip", "uninstall", "-y", *sorted(dists)]
    typer.echo("Running: " + " ".join(cmd))
    subprocess.run(cmd, check=False)


@app.command("sync")
def sync_extras(
    purge: bool = typer.Option(False, "--purge", help="Also uninstall extraneous extras"),
):
    """Install missing extras (and optionally purge extraneous)."""
    # install missing
    install_extras(features=None)
    if purge:
        purge_extras()


