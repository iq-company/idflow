"""
Utilities to manage and check optional feature dependencies.

Supports two sources of feature definitions:
- Package extras (from the installed idflow distribution metadata)
- Project-defined features from config/features.toml (or features.toml)

A feature is considered installed if all of its required distributions are importable
(importlib.metadata.distribution succeeds), ignoring version constraints for the check.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Set
from pathlib import Path
import importlib.metadata


def _parse_requires_dist_for_extra(dist: importlib.metadata.Distribution) -> Dict[str, List[str]]:
    """
    Parse METADATA to map extras to their Requires-Dist requirement specifiers.

    Returns: { extra_name: ["packageA>=1", "packageB"], ... }
    """
    extras: Dict[str, List[str]] = {}
    try:
        lines = dist.metadata.as_string().splitlines()
    except Exception:
        return extras

    current_requires: List[Tuple[str, Optional[str]]] = []
    # We will scan Requires-Dist lines with markers like: extra == 'research'
    import re
    req_re = re.compile(r"^Requires-Dist:\s*([^;]+?)(?:;\s*(.*))?$")

    for line in lines:
        if not line.startswith("Requires-Dist:"):
            continue
        m = req_re.match(line)
        if not m:
            continue
        requirement = m.group(1)  # package and version specifier
        marker = m.group(2) or ""
        # Extract extra name from marker if present
        extra_name = None
        # Support single or double quotes and case-insensitive 'extra =='
        em = re.search(r"extra\s*==\s*['\"]([^'\"]+)['\"]", marker or "", flags=re.IGNORECASE)
        if em:
            extra_name = em.group(1)
        if extra_name:
            extras.setdefault(extra_name, []).append(requirement)

    return extras


def _project_features_sources() -> List[Path]:
    """Return project feature file candidates in load order (earlier overridden by later)."""
    paths: List[Path] = []
    # base files
    if (Path("config") / "features.toml").exists():
        paths.append(Path("config") / "features.toml")
    if Path("features.toml").exists():
        paths.append(Path("features.toml"))
    # modular directory
    ddir = Path("config") / "features.d"
    if ddir.exists() and ddir.is_dir():
        for p in sorted(ddir.glob("*.toml")):
            paths.append(p)
    return paths


def _parse_project_features_file(path: Path) -> Dict[str, Dict[str, List[str]]]:
    """
    Parse a single TOML file.
    Supports two styles:
    - [features] simple mapping: name = [reqs]
    - [features.name] with keys: packages=[...], extends=[...]
    Returns: { name: {"packages": [...], "extends": [...] } }
    """
    import tomllib
    out: Dict[str, Dict[str, List[str]]] = {}
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f) or {}
    except Exception:
        return out

    features = data.get("features", {})

    # If table of tables style
    if isinstance(features, dict) and any(isinstance(v, dict) for v in features.values()):
        for name, spec in features.items():
            packages: List[str] = []
            extends: List[str] = []
            if isinstance(spec, dict):
                pk = spec.get("packages")
                if isinstance(pk, list):
                    packages = [str(x) for x in pk]
                elif isinstance(pk, str):
                    packages = [pk]
                ex = spec.get("extends")
                if isinstance(ex, list):
                    extends = [str(x) for x in ex]
                elif isinstance(ex, str):
                    extends = [ex]
            out[name] = {"packages": packages, "extends": extends}
    else:
        # simple mapping style
        for name, v in features.items():
            packages: List[str] = []
            if isinstance(v, list):
                packages = [str(x) for x in v]
            elif isinstance(v, str):
                packages = [v]
            out[name] = {"packages": packages, "extends": []}

    return out


def _merge_project_features() -> Dict[str, Dict[str, List[str]]]:
    """Merge project feature sources; later files override earlier definitions entirely for the same name."""
    merged: Dict[str, Dict[str, List[str]]] = {}
    for path in _project_features_sources():
        parsed = _parse_project_features_file(path)
        for name, spec in parsed.items():
            merged[name] = spec
    return merged


def _resolve_features_with_extends(base: Dict[str, List[str]], project: Dict[str, Dict[str, List[str]]]) -> Dict[str, List[str]]:
    """
    Resolve final feature->packages with extends. 'base' are package extras; 'project' are project specs.
    Project entries override base packages for the same feature name unless they explicitly extend.
    """
    # Start from combined view for resolution
    combined_base: Dict[str, List[str]] = dict(base)

    # Helper to get raw spec for a feature (packages + extends)
    def get_spec(name: str) -> Tuple[List[str], List[str], bool]:
        if name in project:
            spec = project[name]
            return spec.get("packages", []), spec.get("extends", []), True
        # fall back to base extras (no extends there)
        if name in combined_base:
            return combined_base[name], [], False
        return [], [], False

    resolved: Dict[str, List[str]] = {}
    resolving: Set[str] = set()

    def resolve(name: str) -> List[str]:
        if name in resolved:
            return resolved[name]
        if name in resolving:
            # cycle guard
            return []
        resolving.add(name)

        pkgs, exts, is_project = get_spec(name)
        final: List[str] = []

        # include extends first
        for parent in exts:
            final.extend(resolve(parent))

        # then own packages; if project overrides an existing base feature without extends,
        # we still just take the project's packages (as defined)
        final.extend(pkgs)

        # deduplicate while preserving order
        seen: Set[str] = set()
        deduped: List[str] = []
        for p in final:
            if p not in seen:
                seen.add(p)
                deduped.append(p)

        resolved[name] = deduped
        resolving.remove(name)
        return resolved[name]

    # resolve all names known from either source
    all_names: Set[str] = set(base.keys()) | set(project.keys())
    for n in all_names:
        resolve(n)

    return resolved


def _package_extras() -> Dict[str, List[str]]:
    """Get extras from installed idflow distribution and/or local pyproject fallback."""
    extras: Dict[str, List[str]] = {}
    try:
        dist = importlib.metadata.distribution("idflow")
        # Parse extras from METADATA
        parsed = _parse_requires_dist_for_extra(dist)
        extras.update(parsed)
        # Ensure names from Provides-Extra are present even if no explicit Requires-Dist lines
        try:
            provided = dist.metadata.get_all("Provides-Extra") or []
            for name in provided:
                extras.setdefault(name, [])
        except Exception:
            pass
    except importlib.metadata.PackageNotFoundError:
        dist = None

    # Fallback: read optional-dependencies from local pyproject.toml (dev environment)
    def _fallback_from_pyproject() -> Dict[str, List[str]]:
        try:
            import tomllib, importlib.util
            candidates: List[Path] = []
            # 1) Current working directory pyproject (demo project won't have idflow extras; still include for completeness)
            cwd_py = Path("pyproject.toml")
            if cwd_py.exists():
                candidates.append(cwd_py)
            # 2) Seek the pyproject.toml near installed idflow package location (editable installs/dev)
            try:
                spec = importlib.util.find_spec("idflow")
                if spec and spec.origin:
                    pkg_dir = Path(spec.origin).resolve().parent
                    for parent in [pkg_dir] + list(pkg_dir.parents):
                        py = parent / "pyproject.toml"
                        if py.exists():
                            candidates.append(py)
                            break
            except Exception:
                pass
            out: Dict[str, List[str]] = {}
            for py in candidates:
                try:
                    with open(py, "rb") as f:
                        data = tomllib.load(f) or {}
                    opt = data.get("project", {}).get("optional-dependencies", {})
                    for name, pkgs in opt.items():
                        if isinstance(pkgs, list):
                            out[name] = [str(x) for x in pkgs]
                except Exception:
                    continue
            return out
        except Exception:
            return {}

    extras.update(_fallback_from_pyproject())
    return extras


def _extract_distribution_name(requirement_spec: str) -> str:
    """Extract the distribution name from a requirement specifier (drop version and extras)."""
    # Examples:
    #  - package
    #  - package>=1.2
    #  - package[extra]>=1.0
    #  - package!=2.0
    name_part = requirement_spec.split(";")[0].strip()
    # split off version constraints
    for sep in ["==", ">=", "<=", "~=", ">", "<", "!=", "==="]:
        if sep in name_part:
            name_part = name_part.split(sep, 1)[0].strip()
    # remove extras in brackets
    if "[" in name_part:
        name_part = name_part.split("[", 1)[0]
    return name_part


def _is_all_requirements_installed(requirements: List[str]) -> bool:
    for req in requirements:
        dist_name = _extract_distribution_name(req)
        try:
            importlib.metadata.distribution(dist_name)
        except importlib.metadata.PackageNotFoundError:
            return False
        except Exception:
            return False
    return True


def get_available_features() -> Dict[str, List[str]]:
    """Resolve available features from package extras + project features (config/features.toml, features.d/*.toml)."""
    base = _package_extras()
    project = _merge_project_features()
    return _resolve_features_with_extends(base, project)


def get_feature_origin_map() -> Dict[str, str]:
    """
    Return a map of feature name -> origin category: 'extra' or 'project'.
    If a feature exists as package extra, it's categorized as 'extra' (even if also defined in project via extends/override),
    otherwise as 'project'.
    """
    base = _package_extras()
    project = _merge_project_features()
    names: Set[str] = set(base.keys()) | set(project.keys())
    origin: Dict[str, str] = {}
    for n in names:
        origin[n] = 'extra' if n in base else 'project'
    return origin


def get_installed_optional_dependencies() -> List[str]:
    """Return names of features whose requirements are installed."""
    available = get_available_features()
    installed: List[str] = []
    for name, reqs in available.items():
        if _is_all_requirements_installed(reqs):
            installed.append(name)
    return installed


def is_optional_dependency_installed(extra_name: str) -> bool:
    """Check if a specific feature's requirements are installed."""
    available = get_available_features()
    reqs = available.get(extra_name, [])
    if not reqs:
        # Unknown feature => consider not installed
        return False
    return _is_all_requirements_installed(reqs)


def get_optional_dependencies_info() -> Dict[str, object]:
    """Return detailed information about optional dependencies/features."""
    available_map = get_available_features()
    installed = get_installed_optional_dependencies()
    return {
        "available": sorted(list(available_map.keys())),
        "installed": sorted(installed),
        "all_installed": set(installed) == set(available_map.keys()),
        "definitions": available_map,
    }


def require_optional_dependency(extra_name: str, feature_description: str | None = None) -> None:
    """
    Raise ImportError if the named feature is not installed.
    """
    if not is_optional_dependency_installed(extra_name):
        feature_desc = f" for {feature_description}" if feature_description else ""
        raise ImportError(
            f"Optional dependency '{extra_name}' is not installed{feature_desc}. "
            f"Install it with: pip install idflow[{extra_name}] or define in config/features.toml"
        )


if __name__ == "__main__":
    info = get_optional_dependencies_info()
    print("Available:", info["available"])  # pragma: no cover
    print("Installed:", info["installed"])   # pragma: no cover
