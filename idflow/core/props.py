import re
from ast import literal_eval
from typing import Any, List, Optional, Tuple

_key_index_re = re.compile(r"(.*?)\[(\d+)\]$")

def parse_simple_value(txt: str) -> Any:
    try:
        return literal_eval(txt)
    except Exception:
        low = txt.lower()
        if low == "true": return True
        if low == "false": return False
        if low in ("null","none"): return None
        return txt

def _split_dot_path(path: str) -> List[Tuple[str, Optional[int]]]:
    parts = []
    for raw in path.split("."):
        m = _key_index_re.match(raw)
        parts.append((m.group(1), int(m.group(2))) if m else (raw, None))
    return parts

def set_in(container: dict, path: str, value: Any) -> None:
    parts = _split_dot_path(path)
    cur: Any = container
    for i, (key, idx) in enumerate(parts):
        last = i == len(parts) - 1
        if idx is None:
            if last:
                cur[key] = value
            else:
                next_is_list = parts[i+1][1] is not None
                if key not in cur or not isinstance(cur[key], (dict, list)):
                    cur[key] = [] if next_is_list else {}
                cur = cur[key]
        else:
            if key not in cur or not isinstance(cur[key], list):
                cur[key] = []
            lst = cur[key]
            while len(lst) <= idx:
                lst.append({})
            if last:
                lst[idx] = value
            else:
                if not isinstance(lst[idx], (dict, list)):
                    lst[idx] = {}
                cur = lst[idx]

