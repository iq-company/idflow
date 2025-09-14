from __future__ import annotations
import typer
from ..common import add_help_option

app = typer.Typer(help="Manages local/remote workflows with versions")

@app.callback()
def workflow_main(
    help: bool = add_help_option()
):
    """Manages local/remote workflows with versions"""
    pass

# Import workflow commands
from .upload import upload_workflows
from .list import list_workflows
from .prune import prune_workflows

app.command("upload")(upload_workflows)
app.command("list")(list_workflows)
app.command("ls")(list_workflows)  # Alias für list
app.command("prune")(prune_workflows)
