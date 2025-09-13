from __future__ import annotations
import typer

app = typer.Typer(help="Manages stages for documents")

# Import stage commands
from .run import run
from .evaluate import evaluate
from .list import list_stages

app.command("run")(run)
app.command("evaluate")(evaluate)
app.command("list")(list_stages)
