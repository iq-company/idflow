from __future__ import annotations
import shutil
from pathlib import Path
import typer
from idflow.core.repo import find_doc_dir
from idflow.core.config import config

def drop(
    uuid: str = typer.Argument(...),
):
    # Extract default values from typer objects for direct function calls
    if hasattr(uuid, 'default'):
        uuid = uuid.default

    # Use configuration for base_dir
    base_dir = config.base_dir

    cur_dir = find_doc_dir(base_dir, uuid)
    if not cur_dir:
        raise typer.BadParameter(f"Dokument nicht gefunden: {uuid}")

    shutil.rmtree(cur_dir)
    typer.echo(f"deleted {uuid}")

