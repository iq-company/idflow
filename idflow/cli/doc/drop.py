from __future__ import annotations
import shutil
from pathlib import Path
import typer
from idflow.core.repo import find_doc_dir

def drop(
    uuid: str = typer.Argument(...),
    base_dir: Path = typer.Option(Path("data"), "--base-dir"),
):
    # Extract default values from typer objects for direct function calls
    if hasattr(uuid, 'default'):
        uuid = uuid.default
    if hasattr(base_dir, 'default'):
        base_dir = base_dir.default
    dir_ = find_doc_dir(base_dir, uuid)
    if not dir_:
        raise typer.BadParameter(f"Dokument nicht gefunden: {uuid}")
    shutil.rmtree(dir_)
    typer.echo(f"deleted {uuid}")

