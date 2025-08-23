from __future__ import annotations
import typer
from pathlib import Path
from idflow.core.vendor import list_copyable, get_vendor_root, copy_tree_with_prompt

@typer.command("copy")
def copy_vendor(
    all_: bool = typer.Option(False, "--all", help="Alle erlaubten Verzeichnisse kopieren"),
    dest: Path = typer.Option(Path("."), "--dest", help="Ziel-Projektverzeichnis (default: aktuelles Verzeichnis)"),
):
    dest = dest.resolve()
    items = list_copyable()

    if not items:
        typer.echo("Keine definierten Vendor-Verzeichnisse.")
        raise typer.Exit()

    if all_:
        for _, rel, src in items:
            _copy_one(src, dest, rel)
        typer.echo("Fertig.")
        return

    # Auswahl anzeigen
    typer.echo("Welche Quelle soll kopiert werden?")
    for i, rel, src in items:
        typer.echo(f"  [{i}] {rel}")

    idx_str = typer.prompt("Bitte Zahl eingeben")
    try:
        idx = int(idx_str)
    except ValueError:
        raise typer.BadParameter("Bitte eine gültige Zahl angeben.")

    match = [x for x in items if x[0] == idx]
    if not match:
        raise typer.BadParameter(f"Ungültige Auswahl: {idx}")

    _, rel, src = match[0]
    _copy_one(src, dest, rel)
    typer.echo("Fertig.")

def _copy_one(src: Path, dest: Path, rel: str) -> None:
    out_dir = (dest / rel).resolve()
    # Sicherheitsnetz: nicht außerhalb des dest schreiben
    # (hier lose, weil wir bewusst rel anhängen; alternativ weglassen)
    copy_tree_with_prompt(src, out_dir)

