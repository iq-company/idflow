from __future__ import annotations
import typer
from .list import list_tasks
from .upload import upload_tasks
from .purge import purge_tasks
from ..common import add_help_option

app = typer.Typer(help="List tasks and handle remote registrations/deletions")

@app.callback()
def tasks_main(
    help: bool = add_help_option()
):
    """List tasks and handle remote registrations/deletions"""
    pass
app.command("list")(list_tasks)
app.command("ls")(list_tasks)  # Alias für list
app.command("upload")(upload_tasks)
app.command("purge")(purge_tasks)

if __name__ == "__main__":
    app()
