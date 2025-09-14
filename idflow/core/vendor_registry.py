from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
import subprocess


def _find_project_root(start: Optional[Path] = None) -> Optional[Path]:
    """
    Finde Projekt-Root durch Suche nach config/idflow.yml in aktuellen und Eltern-Verzeichnissen.
    """
    current = (start or Path.cwd()).resolve()
    while True:
        cfg = current / "config" / "idflow.yml"
        if cfg.exists():
            return current
        if current == current.parent:
            return None
        current = current.parent


@dataclass
class VendorSpec:
    name: str
    type: str  # "git" | "path"
    enabled: bool = True
    priority: int = 100
    # git
    url: Optional[str] = None
    ref: Optional[str] = None  # tag | branch | commit
    subdir: Optional[str] = None
    # path
    path: Optional[Path] = None


def _parse_vendor_file(path: Path) -> Optional[VendorSpec]:
    """
    Parse eine einzelne TOML-Datei in config/vendors.d.
    Minimales Schema:
      name = "email_bot"               # optional, sonst Dateistamm
      enabled = true                    # optional, default true
      priority = 50                     # optional, default 100

      [source]
      type = "git" | "path"
      # git
      url = "https://...git"
      ref = "v1.2.3"                   # optional
      subdir = ""                      # optional
      # path
      path = "/abs/oder/relativ"
    """
    try:
        import tomllib
        with open(path, "rb") as f:
            data = tomllib.load(f) or {}
    except Exception:
        return None

    name = str(data.get("name") or path.stem)
    enabled = bool(data.get("enabled", True))
    priority = int(data.get("priority", 100))

    src = data.get("source") or {}
    t = str(src.get("type") or "").strip()
    if t not in ("git", "path"):
        return None

    if t == "git":
        url = src.get("url")
        if not url:
            return None
        ref = src.get("ref")
        subdir = src.get("subdir")
        return VendorSpec(name=name, type=t, enabled=enabled, priority=priority, url=str(url), ref=(str(ref) if ref else None), subdir=(str(subdir) if subdir else None))
    else:
        p = src.get("path")
        if not p:
            return None
        return VendorSpec(name=name, type=t, enabled=enabled, priority=priority, path=Path(str(p)))


def _load_vendor_specs_from_config(project_root: Path) -> List[VendorSpec]:
    specs: List[VendorSpec] = []
    vdir = project_root / "config" / "vendors.d"
    if not vdir.exists() or not vdir.is_dir():
        return specs
    for p in sorted(vdir.glob("*.toml")):
        spec = _parse_vendor_file(p)
        if spec is not None and spec.enabled:
            specs.append(spec)
    # sort by priority (ascending), then by name
    specs.sort(key=lambda s: (s.priority, s.name))
    return specs


class VendorWorkspace:
    """
    Verwaltet Arbeitsbereich fuer Vendor-Checkouts/Symlinks unter .idflow/vendors.
    - git: clone/fetch/checkout in <workspace>/<name>
    - path: symlink <workspace>/<name> -> externe Quelle
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()
        self.workspace_dir = (self.project_root / ".idflow" / "vendors").resolve()
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def _ensure_git_vendor(self, spec: VendorSpec) -> Optional[Path]:
        target = (self.workspace_dir / spec.name).resolve()
        if not target.exists():
            # clone
            try:
                subprocess.run(["git", "clone", "--depth", "1", spec.url, str(target)], check=True)
            except Exception:
                return None
        # ensure fetch + checkout ref if provided
        try:
            subprocess.run(["git", "-C", str(target), "fetch", "--all", "--tags", "--prune"], check=False)
            if spec.ref:
                # best-effort checkout exact ref
                subprocess.run(["git", "-C", str(target), "checkout", spec.ref], check=False)
                subprocess.run(["git", "-C", str(target), "reset", "--hard", spec.ref], check=False)
        except Exception:
            pass
        root = target / spec.subdir if spec.subdir else target
        return root if root.exists() else None

    def _ensure_path_vendor(self, spec: VendorSpec) -> Optional[Path]:
        src = spec.path
        if not src:
            return None
        # relative Pfade relativ zum Projekt-Root interpretieren
        if not src.is_absolute():
            src = (self.project_root / src).resolve()
        if not src.exists():
            return None
        link = (self.workspace_dir / spec.name).resolve()
        try:
            if link.exists() or link.is_symlink():
                # wenn falsches Ziel: neu setzen
                try:
                    current = link.resolve(strict=False)
                except Exception:
                    current = None
                if current is None or current != src:
                    if link.is_dir() and not link.is_symlink():
                        # Sicherungsstrategie: nicht automatisch löschen, abbrechen
                        return src
                    link.unlink(missing_ok=True)
                    link.symlink_to(src, target_is_directory=True)
            else:
                link.symlink_to(src, target_is_directory=True)
        except Exception:
            # Falls Symlink scheitert, nutze Quelle direkt
            return src
        return link

    def ensure_vendor_root(self, spec: VendorSpec) -> Optional[Path]:
        if spec.type == "git":
            return self._ensure_git_vendor(spec)
        return self._ensure_path_vendor(spec)


class VendorRegistry:
    """
    Laedt Vendor-Spezifikationen aus config/vendors.d und liefert geordnete Root-Pfade.
    Prezedenz (Overlay): library < vendors (priority aufsteigend) < project
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = (project_root or _find_project_root() or Path.cwd()).resolve()
        self._workspace = VendorWorkspace(self.project_root)
        self._specs: List[VendorSpec] = _load_vendor_specs_from_config(self.project_root)

    def vendor_specs(self) -> List[VendorSpec]:
        return list(self._specs)

    def vendor_roots(self) -> List[Tuple[str, Path]]:
        roots: List[Tuple[str, Path]] = []
        for spec in self._specs:
            root = self._workspace.ensure_vendor_root(spec)
            if root is not None and root.exists():
                roots.append((spec.name, root))
        return roots

    def fetch_all(self) -> None:
        """
        Best-effort Vorbereitung/Update fuer alle Vendors:
        - git: clone/fetch/checkout
        - path: Symlink im Workspace anlegen/aktualisieren
        """
        for spec in self._specs:
            try:
                self._workspace.ensure_vendor_root(spec)
            except Exception:
                # Non-fatal: continue with others
                continue


