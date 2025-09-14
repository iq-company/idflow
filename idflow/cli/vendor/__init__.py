import typer
from .copy import copy_vendor
from .list import list_vendor

from pathlib import Path
from idflow.core.vendor_registry import VendorRegistry, _find_project_root

app = typer.Typer(add_completion=False, help="Copy vendor delivered stages, workflows, tasks into project for custom extension.")
app.command("copy")(copy_vendor)
app.command("list")(list_vendor)


@app.command("fetch")
def fetch_all():
    """Fetch/Update all configured git vendors into .idflow/vendors."""
    root = _find_project_root() or Path.cwd()
    vr = VendorRegistry(root)
    vr.fetch_all()
    # Show summary
    roots = vr.vendor_roots()
    if not roots:
        typer.echo("No vendors prepared.")
    else:
        typer.echo("Prepared vendors:")
        for name, path in roots:
            typer.echo(f"  - {name}: {path}")


@app.command("specs")
def list_specs():
    """List configured vendor specs with resolved roots."""
    root = _find_project_root() or Path.cwd()
    vr = VendorRegistry(root)
    specs = vr.vendor_specs()
    roots = vr.vendor_roots()
    name_to_root = {n: p for n, p in roots}
    if not specs:
        typer.echo("No vendor specs found.")
        return
    for s in specs:
        r = name_to_root.get(s.name)
        typer.echo(f"- {s.name} [{s.type}] prio={s.priority} enabled={s.enabled} root={r if r else 'unresolved'}")


@app.command("enable")
def enable_vendor(name: str):
    """Enable a vendor by toggling its config file (sets enabled=true)."""
    _toggle_vendor_enabled(name, True)


@app.command("disable")
def disable_vendor(name: str):
    """Disable a vendor by toggling its config file (sets enabled=false)."""
    _toggle_vendor_enabled(name, False)


def _toggle_vendor_enabled(name: str, enabled: bool) -> None:
    root = _find_project_root() or Path.cwd()
    vdir = (root / "config" / "vendors.d")
    if not vdir.exists():
        typer.echo("No config/vendors.d found")
        raise typer.Exit(1)
    import tomllib
    import re
    for p in sorted(vdir.glob("*.toml")):
        try:
            with open(p, "rb") as f:
                data = tomllib.load(f) or {}
        except Exception:
            continue
        n = str(data.get("name") or p.stem)
        if n != name:
            continue
        # Text-basiertes Umschalten ohne Zusatz-Abhängigkeiten
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            typer.echo(f"Could not read {p}")
            return
        new_line = f"enabled = {'true' if enabled else 'false'}"
        pattern = r"(?m)^(?!\\s*#)\\s*enabled\\s*=\\s*(true|false)\\s*$"
        if re.search(pattern, text):
            new_text = re.sub(pattern, new_line, text, count=1)
        else:
            # Falls kein aktiver enabled-Eintrag existiert: am Ende ergänzen
            if not text.endswith("\n"):
                text += "\n"
            new_text = text + new_line + "\n"
        try:
            p.write_text(new_text, encoding="utf-8")
            typer.echo(f"Set {name} enabled={enabled} in {p}")
        except Exception:
            typer.echo(f"Could not write {p}")
        return
    typer.echo(f"Vendor spec '{name}' not found in {vdir}")

# Usage:
# ===
# # 1) interactive selection of a source
# idflow vendor copy
#
# # 2) copy all allowed directories to the current project
# idflow vendor copy --all
#
# # 3) to another target directory
# idflow vendor copy --dest ./my-project
# When copying, you will be asked for each existing file:
# O → overwrite
# S → skip
# A → abort entire operation

# Story Desc
# create another cli folder for something like sync/vendor/copy (or better suggestion?) to copy files from the pip folder to the directory where `idflow` is called (to make project-specific changes).
#
# E.g. pipelines, tasks, prompts are delivered with the pip folder.
#
# These are then used by the configuration in the project directory.
#
# If individual files are to be added for the project, these should be able to be overridden by FS structure equality in the project.
#
# In the cli command, a constant should be defined in which the directories are listed that can be copied to the local project.
#
# Z.B.
# tasks/
# templates/researcher
# templates/enricher
# templates/generator
#
# Through this definition I want to prevent that simply "all" templates have to be taken (like with tasks), but go into a possible finer-grained structure.
#
# The new CLI command should either have "--all" as a parameter (then all directories are copied), or not, then the possible directories should be displayed numbered, so that the user can specify the number for a folder via prompt to copy the desired folder to the project directory.
#
# If files already exist, each file should be asked whether to overwrite or abort.

