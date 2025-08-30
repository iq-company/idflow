from __future__ import annotations
import shutil
from pathlib import Path
import typer
from idflow.core.models import VALID_STATUS
from idflow.core.repo import find_doc_dir
from idflow.core.io import read_frontmatter, write_frontmatter
from idflow.core.config import config

def set_status(
    uuid: str = typer.Argument(...),
    status: str = typer.Argument(...),
):
    # Extract default values from typer objects for direct function calls
    if hasattr(uuid, 'default'):
        uuid = uuid.default
    if hasattr(status, 'default'):
        status = status.default

    # Use configuration for base_dir
    base_dir = config.base_dir

    if status not in VALID_STATUS:
        raise typer.BadParameter(f"status muss eines von {sorted(VALID_STATUS)} sein.")
    cur_dir = find_doc_dir(base_dir, uuid)
    if not cur_dir:
        raise typer.BadParameter(f"Dokument nicht gefunden: {uuid}")
    doc_path = cur_dir / "doc.md"
    fm, body = read_frontmatter(doc_path)
    fm["status"] = status

    new_dir = base_dir / status / uuid
    if cur_dir != new_dir:
        new_dir.parent.mkdir(parents=True, exist_ok=True)
        if new_dir.exists():
            shutil.rmtree(new_dir)
        shutil.move(str(cur_dir), str(new_dir))
        doc_path = new_dir / "doc.md"

    write_frontmatter(doc_path, fm, body)
    typer.echo(str(doc_path))

