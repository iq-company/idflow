#!venv python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import typer

app = typer.Typer(add_completion=False)

# Import the CLI doc commands
from idflow.cli.doc import app as doc_app
app.add_typer(doc_app, name="doc")

# Import the CLI vendor commands
from idflow.cli.vendor import app as vendor_app
app.add_typer(vendor_app, name="vendor")

if __name__ == "__main__":
    app()