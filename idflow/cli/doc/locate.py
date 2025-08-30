#!/usr/bin/env python3
"""
Locate command for finding document paths by UUID.
"""

import typer
from idflow.core.fs_markdown import FSMarkdownDocument

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

    # Find the document using ORM
    doc = FSMarkdownDocument.find(uuid)
    if not doc:
        raise typer.BadParameter(f"Document not found: {uuid}")

    typer.echo(str(doc.doc_file))
