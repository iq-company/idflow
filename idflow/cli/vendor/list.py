from __future__ import annotations
import typer
from pathlib import Path
from idflow.core.vendor import overview


def list_vendor(
    dest: Path = typer.Option(Path("."), "--dest", help="Project directory (default: current directory)"),
):
    # Extract default values from typer.Option for direct function calls
    if hasattr(dest, 'default'):
        dest = dest.default
    dest = dest.resolve()

    data = overview(dest)
    if not data:
        typer.echo("No vendor sections available.")
        raise typer.Exit()

    for section, entries in data.items():
        typer.echo(section)
        if not entries:
            typer.echo("  (empty)")
            continue
        for name, extended in entries:
            suffix = " (extended)" if extended else ""
            typer.echo(f"  - {name}{suffix}")


