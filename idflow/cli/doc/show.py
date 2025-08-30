from __future__ import annotations
import typer
from idflow.core.fs_markdown import FSMarkdownDocument

def show(
    uuid: str = typer.Argument(...),
):
    # Extract default values from typer objects for direct function calls
    if hasattr(uuid, 'default'):
        uuid = uuid.default

    # Find the document using ORM
    doc = FSMarkdownDocument.find(uuid)
    if not doc:
        raise typer.BadParameter(f"Document not found: {uuid}")

    # Display the document content
    typer.echo(f"Document: {uuid}")
    typer.echo(f"Status: {doc.status}")
    typer.echo(f"File: {doc.doc_file}")
    typer.echo("-" * 50)

    # Show properties
    if doc._data:
        typer.echo("Properties:")
        for key, value in doc._data.items():
            if key not in ['id', 'status']:  # Skip internal fields
                typer.echo(f"  {key}: {value}")

    # Show document references
    if doc.doc_refs:
        typer.echo("\nDocument References:")
        for ref in doc.doc_refs:
            typer.echo(f"  {ref.key}: {ref.uuid}")
            if ref.data:
                typer.echo(f"    data: {ref.data}")

    # Show file references
    if doc.file_refs:
        typer.echo("\nFile References:")
        for ref in doc.file_refs:
            typer.echo(f"  {ref.key}: {ref.filename} ({ref.uuid})")
            if ref.data:
                typer.echo(f"    data: {ref.data}")

    # Show body content
    if doc.body:
        typer.echo(f"\nBody:")
        typer.echo("-" * 30)
        typer.echo(doc.body)
