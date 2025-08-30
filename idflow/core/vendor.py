# idflow/core/vendor.py
from __future__ import annotations
from pathlib import Path
from typing import Iterable, List, Tuple
import shutil
import typer
import importlib.resources as ir

# Was kopiert werden darf (relativ zum Vendor-Root):
COPYABLE_DIRS: List[str] = [
    "tasks",
    "workflows",
]

def get_vendor_root() -> Path:
    """
    Liefert den Ordner im installierten Paket, in dem die Vendor-Dateien liegen.
    Standard: idflow (das Paket selbst)
    """
    # nutzt importlib.resources, funktioniert auch im Zip/egg, solange als Paketdaten inkludiert
    return Path(ir.files("idflow"))

def list_copyable() -> List[Tuple[int, str, Path]]:
    root = get_vendor_root()
    items: List[Tuple[int, str, Path]] = []
    for i, rel in enumerate(COPYABLE_DIRS, start=1):
        p = root / rel
        items.append((i, rel, p))
    return items

def ensure_is_subpath(base: Path, target: Path) -> None:
    try:
        target.relative_to(base)
    except Exception:
        raise RuntimeError(f"Unsichere Pfadableitung: {target} nicht unter {base}")

def copy_tree_with_prompt(src: Path, dst: Path) -> None:
    """
    Kopiert Verzeichnis-Baum:
    - legt fehlende Ordner an
    - pro Datei prompt: Overwrite / Skip / Abort
    """
    if not src.exists() or not src.is_dir():
        raise typer.BadParameter(f"Quelle existiert nicht: {src}")

    for path in src.rglob("*"):
        rel = path.relative_to(src)
        out = dst / rel
        if path.is_dir():
            out.mkdir(parents=True, exist_ok=True)
            continue

        # Datei
        if out.exists():
            choice = _prompt_overwrite(rel)
            if choice == "a":
                raise typer.Abort()
            elif choice == "s":
                continue
            # "o" = overwrite
        else:
            out.parent.mkdir(parents=True, exist_ok=True)

        shutil.copyfile(path, out)

def _prompt_overwrite(relpath: Path) -> str:
    # einfaches Prompt mit validierten Optionen
    while True:
        ans = typer.prompt(
            f"Datei existiert bereits: {relpath} — (O)verwrite / (S)kip / (A)bort?",
            default="S"
        ).strip().lower()
        if ans in ("o", "s", "a"):
            return ans
        typer.echo("Bitte O, S oder A eingeben.")

