from __future__ import annotations
import typer

app = typer.Typer(help="Manages local/remote workflows with versions")

# Import workflow commands
from .upload import upload_workflows
from .list import list_workflows
from .prune import prune_workflows

app.command("upload")(upload_workflows)
app.command("list")(list_workflows)
app.command("prune")(prune_workflows)
