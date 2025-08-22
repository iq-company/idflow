import typer
from .add import add
from .list import list_docs
from .modify import modify
from .set_status import set_status
from .drop import drop
from .drop_all import drop_all

app = typer.Typer(add_completion=False)
app.command("add")(add)
app.command("list")(list_docs)
app.command("modify")(modify)
app.command("set-status")(set_status)
app.command("drop")(drop)
app.command("drop-all")(drop_all)

