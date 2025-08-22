from pathlib import Path
from typing import List, Optional
from .models import VALID_STATUS

def doc_paths(base_dir: Path) -> List[Path]:
    paths: List[Path] = []
    for status in VALID_STATUS:
        root = base_dir / status
        if not root.exists(): continue
        for uuid_dir in root.iterdir():
            doc = uuid_dir / "doc.md"
            if doc.is_file():
                paths.append(doc)
    return paths

def find_doc_dir(base_dir: Path, uuid: str) -> Optional[Path]:
    for status in VALID_STATUS:
        p = base_dir / status / uuid
        if p.is_dir():
            return p
    return None

