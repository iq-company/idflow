# idflow/core/vendor.py
from __future__ import annotations
from pathlib import Path
from typing import Iterable, List, Tuple, Dict, Optional
import shutil
import typer
import importlib.resources as ir

# Was kopiert werden darf (relativ zum Vendor-Root):
COPYABLE_DIRS: List[str] = [
    "tasks",
    "workflows",
    "stages",
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

def list_sections() -> List[str]:
    """Return available vendor sections (e.g., tasks, workflows, stages)."""
    return list(COPYABLE_DIRS)

def list_elements(section: str) -> List[str]:
    """List element names for a given section.

    - tasks/workflows: subdirectory names
    - stages: yaml filenames
    """
    root = get_vendor_root() / section
    if not root.exists():
        return []
    if section == "stages":
        return [p.name for p in sorted(root.glob("*.yml")) if p.is_file()]
    else:
        return [p.name for p in sorted(root.iterdir()) if p.is_dir()]

def normalize_element_name(section: str, element: str) -> Optional[str]:
    """Normalize element for matching, esp. stages (with/without .yml)."""
    available = set(list_elements(section))
    if section == "stages":
        if element in available:
            return element
        # allow passing stem without extension
        with_yml = f"{element}.yml"
        if with_yml in available:
            return with_yml
        return None
    else:
        return element if element in available else None

def is_extended(section: str, element: str, dest: Path) -> bool:
    """Return True if the element already exists in the destination project.

    stages: interpret by stage name (from YAML), not by filename. This aligns with
    runtime behavior where stage identity is the 'name' field.
    """
    dest = dest.resolve()
    if section == "stages":
        # Look for any YAML in project stages whose 'name' equals element (stem allowed)
        target_name = element[:-4] if element.endswith('.yml') else element
        proj_dir = dest / section
        if not proj_dir.exists():
            return False
        for yml in proj_dir.glob("*.yml"):
            try:
                import yaml
                data = yaml.safe_load(yml.read_text(encoding='utf-8'))
                if isinstance(data, dict) and data.get('name') == target_name:
                    return True
            except Exception:
                continue
        return False
    else:
        return (dest / section / element).exists()

def overview(dest: Path) -> Dict[str, List[Tuple[str, bool]]]:
    """Build overview mapping: section -> list of (element, is_extended)."""
    dest = dest.resolve()
    data: Dict[str, List[Tuple[str, bool]]] = {}
    for section in COPYABLE_DIRS:
        items = []
        for el in list_elements(section):
            items.append((el, is_extended(section, el, dest)))
        data[section] = items
    return data

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

def copy_element_with_target_prompt(section: str, element: str, dest: Path) -> None:
    """Copy a single element from a section into dest.

    - stages: copy file level
    - others: copy directory level (with per-file overwrite prompts)
    """
    section = section.strip()
    dest = dest.resolve()
    vendor_root = get_vendor_root() / section
    if not vendor_root.exists():
        raise typer.BadParameter(f"Unbekannte Sektion: {section}")

    normalized = normalize_element_name(section, element)
    if normalized is None:
        raise typer.BadParameter(f"Element nicht gefunden: {element} in {section}")

    if section == "stages":
        src = vendor_root / normalized
        if not src.exists() or not src.is_file():
            raise typer.BadParameter(f"Quelle existiert nicht: {src}")
        dst = dest / section / src.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            typer.echo(f"Target already exists in: {dst}")
            if not typer.confirm("Do you want to replace it?"):
                typer.echo("Abgebrochen (kein Ersatz).")
                return
        shutil.copyfile(src, dst)
    else:
        src = vendor_root / normalized
        if not src.exists() or not src.is_dir():
            raise typer.BadParameter(f"Quelle existiert nicht: {src}")
        dst = dest / section / normalized
        if dst.exists():
            typer.echo(f"Target already exists in: {dst}")
            if not typer.confirm("Do you want to replace it?"):
                typer.echo("Abgebrochen (kein Ersatz).")
                return
        copy_tree_with_prompt(src, dst)

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

