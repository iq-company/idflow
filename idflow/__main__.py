#!venv python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import typer

app = typer.Typer(add_completion=False)

# Import common help utilities
from idflow.cli.common import add_help_option

@app.callback()
def main(
    help: bool = add_help_option()
):
    """idflow CLI - Workflow management tool"""
    pass

# Import the CLI doc commands
from idflow.cli.doc import app as doc_app
app.add_typer(doc_app, name="doc")

# Import the CLI vendor commands
from idflow.cli.vendor import app as vendor_app
app.add_typer(vendor_app, name="vendor")

# Import the CLI stage commands
from idflow.cli.stage import app as stage_app
app.add_typer(stage_app, name="stage")

# Import the CLI worker commands
from idflow.cli.worker.worker import app as worker_app
app.add_typer(worker_app, name="worker")

# Import the CLI workflow commands
from idflow.cli.workflow import app as workflow_app
app.add_typer(workflow_app, name="workflow")

# Import the CLI tasks commands
from idflow.cli.tasks import app as tasks_app
app.add_typer(tasks_app, name="tasks")

# Import the CLI extras commands
from idflow.cli.extras import app as extras_app
app.add_typer(extras_app, name="extras")

# Import the CLI init command
from idflow.cli.init import init_project
app.command("init")(init_project)

if __name__ == "__main__":
    app()