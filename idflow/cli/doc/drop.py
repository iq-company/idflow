from __future__ import annotations
import typer
from idflow.core.fs_markdown import FSMarkdownDocument

def drop(
    uuid: str = typer.Argument(...),
):
    # Extract default values from typer objects for direct function calls
    if hasattr(uuid, 'default'):
        uuid = uuid.default

    # Find the document using ORM
    doc = FSMarkdownDocument.find(uuid)
    if not doc:
        raise typer.BadParameter(f"Document not found: {uuid}")

    # Destroy the document using ORM
    doc.destroy()
    typer.echo(f"deleted {uuid}")

