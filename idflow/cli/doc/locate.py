#!/usr/bin/env python3
"""
Locate command for finding document paths by UUID.
"""

from pathlib import Path
import typer
from idflow.core.repo import find_doc_dir
from idflow.core.config import config

def locate(
    uuid: str = typer.Argument(..., help="Document UUID to locate"),
):
    """
    Locate a document by its UUID and return its path.

    This is useful for finding where a document is stored after creation
    or for scripting purposes.
    """
    # Extract default values from typer objects for direct function calls
    if hasattr(uuid, 'default'):
        uuid = uuid.default

    # Use configuration for base_dir
    base_dir = config.base_dir

    doc_dir = find_doc_dir(base_dir, uuid)
    if not doc_dir:
        raise typer.BadParameter(f"Document not found: {uuid}")

    doc_path = doc_dir / "doc.md"
    if not doc_path.exists():
        raise typer.BadParameter(f"Document file not found: {doc_path}")

    typer.echo(str(doc_path))
