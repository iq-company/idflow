from __future__ import annotations
import typer

app = typer.Typer(help="Manages stages for documents")

# Import stage commands
from .run import run
from .evaluate import evaluate

app.command("run")(run)
app.command("evaluate")(evaluate)
