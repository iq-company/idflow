from pathlib import Path
from typing import Tuple, Dict, Any
import yaml

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def to_frontmatter(data: Dict[str, Any], body: str) -> str:
    fm = yaml.safe_dump(data, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{fm}\n---\n{body}\n"

def read_frontmatter(path: Path) -> Tuple[dict, str]:
    txt = path.read_text(encoding="utf-8")
    if not txt.startswith("---"):
        return {}, txt
    parts = txt.split("\n---\n", 1)
    head = parts[0][4:] if parts[0].startswith("---\n") else parts[0].lstrip("-\n")
    body = parts[1] if len(parts) > 1 else ""
    data = yaml.safe_load(head) or {}
    return data, body

def write_frontmatter(path: Path, data: dict, body: str) -> None:
    path.write_text(to_frontmatter(data, body), encoding="utf-8")

