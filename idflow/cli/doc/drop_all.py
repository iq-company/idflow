from __future__ import annotations
import typer
from idflow.core.fs_markdown import FSMarkdownDocument

def drop_all(
    status: str = typer.Argument(..., help="Status to filter by: inbox, active, done, archived, or all"),
    force: bool = typer.Option(False, "--force", help="delete without confirmation"),
):
    # Extract default values from typer.Option objects for direct function calls
    if hasattr(force, 'default'):
        force = force.default

    # Validate status parameter
    valid_statuses = {'inbox', 'active', 'done', 'archived', 'all'}
    if status not in valid_statuses:
        typer.echo(f"Error: Invalid status '{status}'. Must be one of: {', '.join(sorted(valid_statuses))}")
        raise typer.Exit(1)

    # Find documents using ORM with status filter
    if status == 'all':
        docs = FSMarkdownDocument.where()
    else:
        docs = FSMarkdownDocument.where(status=status)

    if not docs:
        typer.echo("nothing to delete")
        raise typer.Exit()

    if not force:
        typer.confirm(f"Really delete ALL ({len(docs)}) documents with status '{status}'?", abort=True)

    # Delete all documents using ORM
    for doc in docs:
        doc.destroy()

    typer.echo(f"deleted {len(docs)} docs")

