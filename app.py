import importlib.metadata as md
import typer
from idflow.cli.doc import app as doc_app

# further groups
# from idflow.cli.othercmd import app as other_app

app = typer.Typer(add_completion=False)
app.add_typer(doc_app, name="doc")

for ep in md.entry_points(group="idflow.commands"):
    subapp = ep.load()
    app.add_typer(subapp, name=ep.name)

def run():
    app()

