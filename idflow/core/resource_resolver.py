from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple, Callable, Optional, Set
import importlib.resources as ir

from .vendor_registry import VendorRegistry


def _package_root() -> Path:
    try:
        return Path(ir.files("idflow"))
    except Exception:
        return Path("idflow").resolve()


class ResourceResolver:
    """
    Ermittelt Ressourcen über mehrere Basen in definierter Reihenfolge:
    1) lib (Paketressourcen)
    2) vendors (konfiguriert, sortiert nach priority)
    3) project (aktuelles Arbeitsverzeichnis)

    Bietet Overlay-Auflösung nach Schlüssel:
    - tasks:   tasks/<name>/
    - workflows: workflows/<name>/
    - stages:  stages/*.yml  (Schlüssel = Dateiname)
    """

    def __init__(self, project_root: Path | None = None):
        self.project_root = (project_root or Path.cwd()).resolve()
        self.pkg_root = _package_root()
        self.vendor_registry = VendorRegistry(self.project_root)

    def bases(self) -> List[Tuple[str, Path]]:
        bases: List[Tuple[str, Path]] = [("lib", self.pkg_root)]
        bases.extend(self.vendor_registry.vendor_roots())
        bases.append(("project", self.project_root))
        return bases

    # --- Generic collectors ---
    def _collect_dir_items(self, base: Path, subdir: str) -> Dict[str, Path]:
        result: Dict[str, Path] = {}
        root = base / subdir
        if not root.exists():
            return result
        for entry in root.iterdir():
            if entry.is_dir():
                result[entry.name] = entry
        return result

    def _collect_file_items(self, base: Path, subdir: str, pattern: str) -> Dict[str, Path]:
        result: Dict[str, Path] = {}
        root = base / subdir
        if not root.exists():
            return result
        for p in root.glob(pattern):
            if p.is_file():
                result[p.name] = p
        return result

    def overlay_workflow_dirs(self) -> Dict[str, Path]:
        # Overlay in Reihenfolge lib -> vendors (n) -> project, wobei spaetere Eintraege ueberlagern
        merged: Dict[str, Path] = {}
        for _name, base in self.bases():
            items = self._collect_dir_items(base, "workflows")
            merged.update(items)
        return merged

    def overlay_task_dirs(self) -> Dict[str, Path]:
        merged: Dict[str, Path] = {}
        for _name, base in self.bases():
            items = self._collect_dir_items(base, "tasks")
            merged.update(items)
        return merged

    def overlay_stage_files(self) -> Dict[str, Path]:
        merged: Dict[str, Path] = {}
        for _name, base in self.bases():
            items = self._collect_file_items(base, "stages", "*.yml")
            merged.update(items)
        return merged

    # --- Generic high-level helpers for CLIs ---
    def base_dir_maps(self, subdir: str) -> List[Tuple[str, Dict[str, Path]]]:
        """Return per-base directory maps for a subdir: [(base_name, {name->Path}), ...]."""
        out: List[Tuple[str, Dict[str, Path]]] = []
        for name, base in self.bases():
            out.append((name, self._collect_dir_items(base, subdir)))
        return out

    def target_dirs(self, subdir: str) -> Dict[str, Path]:
        """Overlay directories for a subdir across bases (lib -> vendors -> project)."""
        merged: Dict[str, Path] = {}
        for _name, base in self.bases():
            merged.update(self._collect_dir_items(base, subdir))
        return merged

    def origin_maps_for(self, subdir: str) -> Tuple[Dict[str, Path], Dict[str, Path], Dict[str, Path]]:
        """
        Return (lib_map, vendors_map_merged, project_map) for subdir.
        Vendors are merged into a single map for presence checks.
        """
        bases = self.bases()
        lib_map: Dict[str, Path] = {}
        vendors_map: Dict[str, Path] = {}
        project_map: Dict[str, Path] = {}

        if not bases:
            return lib_map, vendors_map, project_map

        # lib is first, project is last, everything between are vendors
        lib_base_name, lib_base = bases[0]
        lib_map = self._collect_dir_items(lib_base, subdir)

        if len(bases) > 1:
            project_base_name, project_base = bases[-1]
            project_map = self._collect_dir_items(project_base, subdir)

        # vendors are bases[1:-1]
        for name, base in bases[1:-1]:
            vendors_map.update(self._collect_dir_items(base, subdir))

        return lib_map, vendors_map, project_map

    # --- Domain-specific helpers ---
    def workflow_json_files(self) -> List[Path]:
        """Return flattened workflow JSON files using directory overlay semantics."""
        return self.collect_flattened_files("workflows", "*.json", exclude_filenames={"event_handlers.json"})

    def task_python_files(self) -> List[Path]:
        """Return flattened task Python files using directory overlay semantics."""
        return self.collect_flattened_files("tasks", "*.py", exclude_filenames={"__init__.py"})

    # --- Generic collectors ---
    def collect_flattened_files(self, subdir: str, file_glob: str, exclude_filenames: Optional[Set[str]] = None) -> List[Path]:
        """
        Flatten files from overlayed directories under subdir matching file_glob.
        exclude_filenames: optional set of exact file names to skip (e.g., event_handlers.json).
        """
        files: List[Path] = []
        exclude_filenames = exclude_filenames or set()
        # Overlay by dir, then rglob pattern within each dir
        for dir_path in self.target_dirs(subdir).values():
            for f in dir_path.rglob(file_glob):
                if f.name in exclude_filenames:
                    continue
                if f.is_file():
                    files.append(f)
        return files

    def _collect_files_in_dirs(self, dirs_map: Dict[str, Path], file_glob: str, exclude_filenames: Optional[Set[str]] = None) -> List[Path]:
        files: List[Path] = []
        exclude_filenames = exclude_filenames or set()
        for d in dirs_map.values():
            for f in d.rglob(file_glob):
                if f.name in exclude_filenames or not f.is_file():
                    continue
                files.append(f)
        return files

    def collect_files_by_base(self, subdir: str, file_glob: str, exclude_filenames: Optional[Set[str]] = None) -> Tuple[List[Path], List[Path], List[Path]]:
        """
        Collect files per base (lib_files, vendor_files, project_files) without re-scanning later.
        """
        lib_map, vendor_map, proj_map = self.origin_maps_for(subdir)
        lib_files = self._collect_files_in_dirs(lib_map, file_glob, exclude_filenames)
        vendor_files = self._collect_files_in_dirs(vendor_map, file_glob, exclude_filenames)
        proj_files = self._collect_files_in_dirs(proj_map, file_glob, exclude_filenames)
        return lib_files, vendor_files, proj_files

    def _collect_files_by_base_direct(self, subdir: str, file_glob: str, exclude_filenames: Optional[Set[str]] = None) -> Tuple[List[Path], List[Path], List[Path]]:
        """Collect files per base directly from bases (for file-based overlays like stages)."""
        exclude_filenames = exclude_filenames or set()
        bases = [b for _n, b in self.bases()]
        lib_files: List[Path] = []
        vendor_files: List[Path] = []
        proj_files: List[Path] = []
        if not bases:
            return lib_files, vendor_files, proj_files
        lib_base = bases[0]
        for f in (lib_base / subdir).glob(file_glob):
            if f.is_file() and f.name not in exclude_filenames:
                lib_files.append(f)
        if len(bases) > 1:
            project_base = bases[-1]
            for f in (project_base / subdir).glob(file_glob):
                if f.is_file() and f.name not in exclude_filenames:
                    proj_files.append(f)
        for base in bases[1:-1]:
            root = base / subdir
            if not root.exists():
                continue
            for f in root.glob(file_glob):
                if f.is_file() and f.name not in exclude_filenames:
                    vendor_files.append(f)
        return lib_files, vendor_files, proj_files

    # Name extractors
    @staticmethod
    def name_from_json_key(key: str) -> Callable[[Path], Optional[str]]:
        def _extract(path: Path) -> Optional[str]:
            try:
                import json
                data = json.loads(path.read_text(encoding="utf-8"))
                val = data.get(key)
                return str(val) if val is not None else None
            except Exception:
                return None
        return _extract

    @staticmethod
    def name_from_yaml_key(key: str) -> Callable[[Path], Optional[str]]:
        def _extract(path: Path) -> Optional[str]:
            try:
                import yaml
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    val = data.get(key)
                    return str(val) if val is not None else None
                return None
            except Exception:
                return None
        return _extract

    @staticmethod
    def name_from_stem() -> Callable[[Path], Optional[str]]:
        def _extract(path: Path) -> Optional[str]:
            try:
                return path.stem
            except Exception:
                return None
        return _extract

    @staticmethod
    def name_from_regex(pattern: str, group: int = 1) -> Callable[[Path], Optional[str]]:
        """Create extractor that reads text and returns first regex group match."""
        import re
        regex = re.compile(pattern)

        def _extract(path: Path) -> Optional[str]:
            try:
                text = path.read_text(encoding="utf-8")
                m = regex.search(text)
                if not m:
                    return None
                val = m.group(group)
                return str(val) if val is not None else None
            except Exception:
                return None
        return _extract

    def _names_in_dirs(self, dirs_map: Dict[str, Path], pattern: str, name_extractor: Callable[[Path], Optional[str]], exclude_filenames: Optional[Set[str]] = None) -> Set[str]:
        names: Set[str] = set()
        exclude_filenames = exclude_filenames or set()
        for d in dirs_map.values():
            for f in d.rglob(pattern):
                if f.name in exclude_filenames or not f.is_file():
                    continue
                n = name_extractor(f)
                if n:
                    names.add(n)
        return names

    def names_by_base(self, subdir: str, pattern: str, name_extractor: Callable[[Path], Optional[str]] | None, exclude_filenames: Optional[Set[str]] = None, item_type: str = "file") -> Tuple[Set[str], Set[str], Set[str]]:
        """
        Return name sets (lib_names, vendor_names, project_names) for given subdir and file pattern using a name extractor.
        """
        if item_type == "dir":
            lib_map, vendor_map, proj_map = self.origin_maps_for(subdir)
            return set(lib_map.keys()), set(vendor_map.keys()), set(proj_map.keys())
        # file-based: collect files per base directly, then map to names
        nx = name_extractor or (lambda p: p.stem)
        lib_files, vendor_files, proj_files = self._collect_files_by_base_direct(
            subdir=subdir, file_glob=pattern, exclude_filenames=exclude_filenames or set()
        )
        lib_names = self.names_from_files(lib_files, nx)
        vendor_names = self.names_from_files(vendor_files, nx)
        proj_names = self.names_from_files(proj_files, nx)
        return lib_names, vendor_names, proj_names

    @staticmethod
    def names_from_files(files: List[Path], name_extractor: Callable[[Path], Optional[str]]) -> Set[str]:
        names: Set[str] = set()
        for f in files:
            n = name_extractor(f)
            if n:
                names.add(n)
        return names

    # Composite builder for CLIs
    def build_index_with_classifier(
        self,
        subdir: str,
        pattern: str,
        name_extractor: Callable[[Path], Optional[str]],
        exclude_filenames: Optional[Set[str]] = None,
        item_type: str = "dir",
    ) -> Tuple[Dict[str, Path], Callable[[str], Tuple[str, str]]]:
        """
        Build a flattened index (name -> file Path) with overlay precedence
        and return a classifier function that maps a name to (origin, tag).
        """
        exclude_filenames = exclude_filenames or set()
        # Collect once per base
        if item_type == "file":
            lib_files, vendor_files, proj_files = self._collect_files_by_base_direct(
                subdir=subdir, file_glob=pattern, exclude_filenames=exclude_filenames
            )
        else:
            lib_files, vendor_files, proj_files = self.collect_files_by_base(
                subdir=subdir, file_glob=pattern, exclude_filenames=exclude_filenames
            )

        # Precompute name sets
        lib_names = self.names_from_files(lib_files, name_extractor)
        vendor_names = self.names_from_files(vendor_files, name_extractor)
        proj_names = self.names_from_files(proj_files, name_extractor)

        # Overlay index: lib -> vendors -> project
        flat_by_name: Dict[str, Path] = {}

        def _index(files: List[Path]) -> None:
            for f in files:
                n = name_extractor(f)
                if n:
                    flat_by_name[n] = f

        _index(lib_files)
        _index(vendor_files)
        _index(proj_files)

        def _classify(name: str) -> Tuple[str, str]:
            return self.classify_origin_from_sets(name, lib_names, vendor_names, proj_names)

        return flat_by_name, _classify

    def classify_origin_generic(self, item_name: str, subdir: str, pattern: str, name_extractor: Callable[[Path], Optional[str]], exclude_filenames: Optional[Set[str]] = None) -> Tuple[str, str]:
        """
        Generic origin classifier for any item type.
        Returns (origin, tag) with origin in {extended, standard, vendor, custom}.
        """
        lib_names, vendor_names, proj_names = self.names_by_base(subdir, pattern, name_extractor, exclude_filenames)
        in_lib = item_name in lib_names
        in_vendor = item_name in vendor_names
        in_proj = item_name in proj_names
        if in_proj and (in_lib or in_vendor):
            return ("extended", "ext")
        if in_vendor:
            return ("vendor", "vnd")
        if in_lib:
            return ("standard", "std")
        return ("custom", "cus")

    @staticmethod
    def classify_origin_from_sets(item_name: str, lib_names: Set[str], vendor_names: Set[str], proj_names: Set[str]) -> Tuple[str, str]:
        """
        Classify using precomputed name sets to avoid re-scanning per item.
        """
        in_lib = item_name in lib_names
        in_vendor = item_name in vendor_names
        in_proj = item_name in proj_names
        if in_proj and (in_lib or in_vendor):
            return ("extended", "ext")
        if in_vendor:
            return ("vendor", "vnd")
        if in_lib:
            return ("standard", "std")
        return ("custom", "cus")

    def classify_workflow_origin(self, workflow_name: str) -> Tuple[str, str]:
        # Convenience wrapper for workflows (JSON key 'name', exclude event_handlers.json)
        return self.classify_origin_generic(
            item_name=workflow_name,
            subdir="workflows",
            pattern="*.json",
            name_extractor=self.name_from_json_key("name"),
            exclude_filenames={"event_handlers.json"},
        )


