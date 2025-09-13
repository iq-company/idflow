from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List
import importlib.resources as ir


def _package_root() -> Path:
    try:
        return Path(ir.files("idflow"))
    except Exception:
        return Path("idflow")


class OverlayDiscovery:
    """
    Allgemeine Overlay-Discovery.

    - mode='dir': vergleicht nach Verzeichnisnamen unter {subdir}
    - mode='file': vergleicht nach Dateinamen unter {subdir} mit file_glob
    Projekt-Elemente überschreiben Paket-Elemente mit gleichem Schlüssel.
    """

    def __init__(self, subdir: str, mode: str, file_glob: str | None = None):
        self.subdir = subdir
        self.mode = mode
        self.file_glob = file_glob

    def _collect_dir_items(self, base: Path) -> Dict[str, Path]:
        result: Dict[str, Path] = {}
        root = base / self.subdir
        if not root.exists():
            return result
        for entry in root.iterdir():
            if entry.is_dir():
                result[entry.name] = entry
        return result

    def _collect_file_items(self, base: Path) -> Dict[str, Path]:
        result: Dict[str, Path] = {}
        root = base / self.subdir
        if not root.exists():
            return result
        pattern = self.file_glob or "*"
        for p in root.glob(pattern):
            if p.is_file():
                result[p.name] = p
        return result

    def package_items(self) -> Dict[str, Path]:
        base = _package_root()
        if self.mode == 'dir':
            return self._collect_dir_items(base)
        return self._collect_file_items(base)

    def project_items(self) -> Dict[str, Path]:
        base = Path('.')
        if self.mode == 'dir':
            return self._collect_dir_items(base)
        return self._collect_file_items(base)

    def overlay(self) -> Dict[str, Path]:
        items = self.package_items()
        items.update(self.project_items())
        return items


def overlay_workflow_dirs() -> Dict[str, Path]:
    """Workflows nach Verzeichnisnamen überlagern (workflows/<name>/...)."""
    return OverlayDiscovery("workflows", mode="dir").overlay()


def overlay_task_dirs() -> Dict[str, Path]:
    """Tasks/Worker nach Verzeichnisnamen überlagern (tasks/<name>/...)."""
    return OverlayDiscovery("tasks", mode="dir").overlay()

def required_workflow_names_static() -> List[str]:
    """Bestimme benötigte Workflows anhand aktiver Stages und erfüllter Features."""
    from .stage_definitions import get_stage_definitions
    from .optional_deps import is_optional_dependency_installed

    stage_defs = get_stage_definitions()
    required: set[str] = set()
    for stage_name in stage_defs.list_definitions():
        sd = stage_defs.get_definition(stage_name)
        if not sd or not sd.active:
            continue
        feats = (sd.requirements.extras if sd.requirements else None) or []
        if any(not is_optional_dependency_installed(f) for f in feats):
            continue
        for wf in sd.workflows:
            required.add(wf.name)
    return sorted(required)


def required_task_names_static() -> List[str]:
    """Benötigte Task-Namen aus Workflows (statisch) + Stage requirements.tasks."""
    from .stage_definitions import get_stage_definitions

    required_wfs = set(required_workflow_names_static())
    required_tasks: set[str] = set()

    # Workflows parsen: gewählte Verzeichnisse, alle json-Dateien darin
    wf_dirs = overlay_workflow_dirs()
    for wf_name, wf_dir in wf_dirs.items():
        if wf_name not in required_wfs:
            continue
        for json_file in wf_dir.rglob("*.json"):
            if json_file.name == "event_handlers.json":
                continue
            try:
                data = json.loads(json_file.read_text(encoding='utf-8'))
                for task in data.get('tasks', []):
                    tn = task.get('name') or task.get('taskReferenceName')
                    if tn:
                        required_tasks.add(tn)
            except Exception:
                continue

    # Zusätzliche Stage-deklarierte Tasks (string oder {name: ...})
    stage_defs = get_stage_definitions()
    for stage_name in stage_defs.list_definitions():
        sd = stage_defs.get_definition(stage_name)
        if not sd or not sd.active or not sd.requirements:
            continue
        extra = getattr(sd.requirements, 'tasks', None) or []
        for t in extra:
            if isinstance(t, str):
                required_tasks.add(t)
            elif isinstance(t, dict) and 'name' in t:
                required_tasks.add(str(t['name']))

    return sorted(required_tasks)


