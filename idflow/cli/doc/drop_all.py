from __future__ import annotations
import typer
from idflow.core.fs_markdown import FSMarkdownDocument

def drop_all(
    force: bool = typer.Option(False, "--force", help="delete without confirmation"),
):
    # Extract default values from typer.Option objects for direct function calls
    if hasattr(force, 'default'):
        force = force.default

    # Find all documents using ORM
    all_docs = FSMarkdownDocument.where()

    if not all_docs:
        typer.echo("nothing to delete")
        raise typer.Exit()

    if not force:
        typer.confirm(f"Really delete ALL ({len(all_docs)}) documents?", abort=True)

    # Delete all documents using ORM
    for doc in all_docs:
        doc.destroy()

    typer.echo(f"deleted {len(all_docs)} docs")

