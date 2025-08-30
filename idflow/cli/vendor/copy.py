from __future__ import annotations
import typer
from pathlib import Path
from idflow.core.vendor import list_copyable, get_vendor_root, copy_tree_with_prompt

def copy_vendor(
    all_: bool = typer.Option(False, "--all", help="Copy all allowed directories"),
    dest: Path = typer.Option(Path("."), "--dest", help="Target project directory (default: current directory)"),
):
    # Extract default values from typer.Option objects for direct function calls
    if hasattr(all_, 'default'):
        all_ = all_.default
    if hasattr(dest, 'default'):
        dest = dest.default
    dest = dest.resolve()
    items = list_copyable()

    if not items:
        typer.echo("No defined vendor directories.")
        raise typer.Exit()

    if all_:
        for _, rel, src in items:
            _copy_one(src, dest, rel)
        typer.echo("Done.")
        return

    # Show selection
    typer.echo("Which source should be copied?")
    for i, rel, src in items:
        typer.echo(f"  [{i}] {rel}")

    idx_str = typer.prompt("Please enter a number")
    try:
        idx = int(idx_str)
    except ValueError:
        raise typer.BadParameter("Please enter a valid number.")

    match = [x for x in items if x[0] == idx]
    if not match:
        raise typer.BadParameter(f"Invalid selection: {idx}")

    _, rel, src = match[0]
    _copy_one(src, dest, rel)
    typer.echo("Done.")

def _copy_one(src: Path, dest: Path, rel: str) -> None:
    out_dir = (dest / rel).resolve()
    # Safety net: don't write outside dest
    # (loose here because we intentionally append rel; alternatively omit)
    copy_tree_with_prompt(src, out_dir)

