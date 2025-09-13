from __future__ import annotations
import typer
from .list import list_tasks
from .upload import upload_tasks
from .purge import purge_tasks

app = typer.Typer(help="List tasks and handle remote registrations/deletions")
app.command("list")(list_tasks)
app.command("upload")(upload_tasks)
app.command("purge")(purge_tasks)

if __name__ == "__main__":
    app()
