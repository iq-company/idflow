from __future__ import annotations
import typer
from ..common import add_help_option

app = typer.Typer(help="Manages stages for documents")

@app.callback()
def stage_main(
    help: bool = add_help_option()
):
    """Manages stages for documents"""
    pass

# Import stage commands
from .run import run
from .evaluate import evaluate
from .list import list_stages

app.command("run")(run)
app.command("evaluate")(evaluate)
app.command("list")(list_stages)
app.command("ls")(list_stages)  # Alias für list
