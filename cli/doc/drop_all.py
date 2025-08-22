from __future__ import annotations
import shutil
from pathlib import Path
import typer
from idflow.core.models import VALID_STATUS

@typer.command("drop-all")
def drop_all(
    force: bool = typer.Option(False, "--force", help="ohne Nachfrage löschen"),
    base_dir: Path = typer.Option(Path("data"), "--base-dir"),
):
    all_dirs = []
    for status in VALID_STATUS:
        root = base_dir / status
        if not root.exists():
            continue
        all_dirs += [p for p in root.iterdir() if p.is_dir()]

    if not all_dirs:
        typer.echo("nichts zu löschen")
        raise typer.Exit()

    if not force:
        typer.confirm(f"Wirklich ALLE ({len(all_dirs)}) Dokumente löschen?", abort=True)

    for d in all_dirs:
        shutil.rmtree(d)
    typer.echo(f"deleted {len(all_dirs)} docs")

