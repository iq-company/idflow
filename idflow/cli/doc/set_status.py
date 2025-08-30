from __future__ import annotations
import typer
from idflow.core.fs_markdown import FSMarkdownDocument
from idflow.core.models import VALID_STATUS

def set_status(
    uuid: str = typer.Argument(...),
    status: str = typer.Argument(...),
):
    # Extract default values from typer objects for direct function calls
    if hasattr(uuid, 'default'):
        uuid = uuid.default
    if hasattr(status, 'default'):
        status = status.default

    if status not in VALID_STATUS:
        raise typer.BadParameter(f"status must be one of {sorted(VALID_STATUS)}.")

    # Find the document using ORM
    doc = FSMarkdownDocument.find(uuid)
    if not doc:
        raise typer.BadParameter(f"Document not found: {uuid}")

    # Get the old status for the message
    old_status = doc.status

    # Update status and save
    doc.status = status
    doc.save()

    # Show a better message
    typer.echo(f"switched state of {uuid} from {old_status} to {status}")

