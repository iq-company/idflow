#!venv python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import json, sys, shutil, re, fnmatch
from pathlib import Path
from uuid import uuid4
from typing import Any, Dict, List, Optional, Tuple
from ast import literal_eval

import typer
import yaml
from pydantic import BaseModel, Field

app = typer.Typer(add_completion=False)
doc_app = typer.Typer(add_completion=False)
app.add_typer(doc_app, name="doc")

VALID_STATUS = {"inbox","active","done","blocked","archived"}

class DocRef(BaseModel):
    key: str
    uuid: str
    data: Dict[str, Any] = Field(default_factory=dict)

class FileRef(BaseModel):
    key: str
    filename: str
    uuid: str
    data: Dict[str, Any] = Field(default_factory=dict)

# ---------- helpers ----------
def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def parse_simple_value(txt: str) -> Any:
    try:
        return literal_eval(txt)
    except Exception:
        low = txt.lower()
        if low == "true": return True
        if low == "false": return False
        if low in ("null","none"): return None
        return txt

_key_index_re = re.compile(r"(.*?)\[(\d+)\]$")

def _split_dot_path(path: str):
    parts: List[Tuple[str, Optional[int]]] = []
    for raw in path.split("."):
        m = _key_index_re.match(raw)
        if m: parts.append((m.group(1), int(m.group(2))))
        else: parts.append((raw, None))
    return parts

def set_in(container: Dict[str, Any], path: str, value: Any) -> None:
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

def to_frontmatter(data: Dict[str, Any], body: str) -> str:
    fm = yaml.safe_dump(data, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{fm}\n---\n{body}\n"

def read_body_param_or_stdin(arg_text: Optional[str]) -> str:
    if arg_text not in (None, ""):
        return arg_text
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return ""

def parse_prop_eq_val(arg: str, flag: str) -> tuple[str, str]:
    if "=" not in arg:
        raise typer.BadParameter(f"{flag} erwartet property=value, nicht: {arg}")
    return arg.split("=", 1)

def find_doc_dir(base_dir: Path, uuid: str) -> Optional[Path]:
    for status in VALID_STATUS:
        p = base_dir / status / uuid
        if p.is_dir():
            return p
    return None

def read_frontmatter(path: Path) -> tuple[Dict[str, Any], str]:
    txt = path.read_text(encoding="utf-8")
    if not txt.startswith("---"):
        return {}, txt
    parts = txt.split("\n---\n", 1)
    head = parts[0][4:] if parts[0].startswith("---\n") else parts[0].lstrip("-\n")
    body = parts[1] if len(parts) > 1 else ""
    data = yaml.safe_load(head) or {}
    return data, body

def write_frontmatter(path: Path, data: Dict[str, Any], body: str) -> None:
    content = to_frontmatter(data, body)
    path.write_text(content, encoding="utf-8")

def doc_paths(base_dir: Path) -> List[Path]:
    # data/<status>/<uuid>/doc.md
    paths: List[Path] = []
    for status in VALID_STATUS:
        root = base_dir / status
        if not root.exists(): continue
        for uuid_dir in root.iterdir():
            doc = uuid_dir / "doc.md"
            if doc.is_file():
                paths.append(doc)
    return paths

# ---------- add ----------
@doc_app.command("add")
def add(
    body_arg: Optional[str] = typer.Argument(None, help="Body-Text (optional, sonst stdin)"),
    status: str = typer.Option("inbox", help="inbox|active|done|blocked|archived"),
    set_: List[str] = typer.Option(None, "--set", help="property=value (Dot-Pfade erlaubt)"),
    list_add: List[str] = typer.Option(None, "--list-add", help="property=value an Liste anhängen"),
    json_kv: List[str] = typer.Option(None, "--json", help="property=<JSON> (dict/list/value)"),
    add_doc: List[str] = typer.Option(None, "--add-doc", help="keyname=<uuid>"),
    doc_data: List[str] = typer.Option(None, "--doc-data", help="JSON für zuletzt hinzugefügten _doc_ref"),
    add_file: List[str] = typer.Option(None, "--add-file", help="file_key=./path/to/file.ext"),
    file_data: List[str] = typer.Option(None, "--file-data", help="JSON für zuletzt hinzugefügte Datei"),
    base_dir: Path = typer.Option(Path("data"), "--base-dir", help="Basisverzeichnis"),
):
    if status not in VALID_STATUS:
        raise typer.BadParameter(f"--status muss eines von {sorted(VALID_STATUS)} sein.")

    doc_id = str(uuid4())
    fm: Dict[str, Any] = {"id": doc_id, "status": status}

    # --set
    for item in set_ or []:
        prop, val = parse_prop_eq_val(item, "--set")
        set_in(fm, prop, parse_simple_value(val))

    # --list-add
    for item in list_add or []:
        prop, val = parse_prop_eq_val(item, "--list-add")
        sentinel = "__APPEND_INIT__"
        set_in(fm, prop, sentinel)
        parts = _split_dot_path(prop)
        cur = fm
        for i, (k, idx) in enumerate(parts):
            last = i == len(parts)-1
            if idx is None:
                if last:
                    if cur.get(k) == sentinel:
                        cur[k] = []
                    if not isinstance(cur[k], list):
                        raise typer.BadParameter(f"{prop} ist keine Liste.")
                    cur[k].append(parse_simple_value(val))
                else:
                    cur = cur[k]
            else:
                lst = cur[k]
                if not isinstance(lst, list):
                    raise typer.BadParameter(f"{prop} ist keine Liste.")
                if last:
                    if lst[idx] == sentinel:
                        lst[idx] = []
                    if not isinstance(lst[idx], list):
                        raise typer.BadParameter(f"{prop} ist keine Liste.")
                    lst[idx].append(parse_simple_value(val))
                else:
                    cur = lst[idx]

    # --json
    for item in json_kv or []:
        prop, js = parse_prop_eq_val(item, "--json")
        try:
            value = json.loads(js)
        except json.JSONDecodeError as e:
            raise typer.BadParameter(f"--json: ungültiges JSON für {prop}: {e}")
        set_in(fm, prop, value)

    # _doc_refs
    if add_doc:
        fm["_doc_refs"] = fm.get("_doc_refs", [])
        for spec in add_doc:
            key, uuid = parse_prop_eq_val(spec, "--add-doc")
            fm["_doc_refs"].append(DocRef(key=key.strip(), uuid=uuid.strip()).model_dump())
        for js in doc_data or []:
            if not fm["_doc_refs"]:
                raise typer.BadParameter("--doc-data ohne vorhandenes --add-doc")
            try:
                d = json.loads(js) if js else {}
            except json.JSONDecodeError as e:
                raise typer.BadParameter(f"--doc-data JSON ungültig: {e}")
            fm["_doc_refs"][-1]["data"] = d

    # _file_refs
    pending_files: List[tuple[Path, FileRef]] = []
    for spec in add_file or []:
        key, path_str = parse_prop_eq_val(spec, "--add-file")
        src = Path(path_str).expanduser()
        if not src.exists() or not src.is_file():
            raise typer.BadParameter(f"--add-file: Datei nicht gefunden: {src}")
        fid = str(uuid4())
        pending_files.append((src, FileRef(key=key.strip(), filename=src.name, uuid=fid)))

    for js in file_data or []:
        if not pending_files:
            raise typer.BadParameter("--file-data ohne vorhandenes --add-file")
        try:
            d = json.loads(js) if js else {}
        except json.JSONDecodeError as e:
            raise typer.BadParameter(f"--file-data JSON ungültig: {e}")
        pending_files[-1][1].data = d

    # Zielpfade
    out_dir = base_dir / status / doc_id
    ensure_dir(out_dir)
    out_file = out_dir / "doc.md"

    # Files kopieren (Name = UUID)
    if pending_files:
        fm["_file_refs"] = fm.get("_file_refs", [])
        for src, ref in pending_files:
            shutil.copyfile(src, out_dir / ref.uuid)
            fm["_file_refs"].append(ref.model_dump())

    # Body
    body = read_body_param_or_stdin(body_arg)

    # Schreiben
    write_frontmatter(out_file, fm, body)
    typer.echo(str(out_file))

# ---------- list ----------
_cmp_re = re.compile(r'^\s*(==|!=|>=|<=|>|<)\s*(.+)\s*$')

def match_filter(prop_value: Any, expr: str) -> bool:
    # numeric comparisons?
    m = _cmp_re.match(expr)
    if m:
        op, rhs = m.groups()
        try:
            pv = float(prop_value)
            rv = float(rhs)
        except Exception:
            return False
        return {
            "==": pv == rv, "!=": pv != rv, ">": pv > rv,
            "<": pv < rv, ">=": pv >= rv, "<=": pv <= rv
        }[op]
    # existence
    if expr.strip().lower() == "exists":
        return bool(prop_value)
    # glob (stringify)
    return fnmatch.fnmatch(str(prop_value), expr)

@doc_app.command("list")
def list_docs(
    base_dir: Path = typer.Option(Path("data"), "--base-dir"),
    filter_: List[str] = typer.Option(None, "--filter", help='property=EXPR (z.B. title="observ*" | priority=">0.5" | meta.owner="exists" | doc-ref="key")'),
    col: List[str] = typer.Option(None, "--col", help="Ausgabespalten (default: uuid)"),
):
    docs = []
    for doc_path in doc_paths(base_dir):
        fm, _ = read_frontmatter(doc_path)
        if not fm: continue
        fm["_doc_path"] = doc_path
        docs.append(fm)

    def passes(fm: Dict[str, Any]) -> bool:
        for f in filter_ or []:
            prop, expr = parse_prop_eq_val(f, "--filter")
            prop = prop.strip()
            expr = expr.strip().strip('"').strip("'")
            if prop == "doc-ref":
                keys = {x.get("key") for x in fm.get("_doc_refs", []) if isinstance(x, dict)}
                if expr not in keys: return False
            elif prop == "file-ref":
                keys = {x.get("key") for x in fm.get("_file_refs", []) if isinstance(x, dict)}
                if expr not in keys: return False
            else:
                # dot-path get (simple)
                parts = prop.split(".")
                cur: Any = fm
                ok = True
                for p in parts:
                    if isinstance(cur, dict) and p in cur:
                        cur = cur[p]
                    else:
                        cur = None
                        ok = False
                        break
                if not ok:
                    return False if expr != "exists" else False
                if not match_filter(cur, expr):
                    return False
        return True

    filtered = [fm for fm in docs if passes(fm)]

    # Ausgabe
    cols = col or ["id"]  # uuid/id
    for fm in filtered:
        row = []
        for c in cols:
            if c == "id" or c == "uuid":
                row.append(fm.get("id",""))
            elif c == "status":
                row.append(fm.get("status",""))
            elif c in ("_doc_refs","doc-keys","doc_keys","doc-ref"):
                keys = sorted({x.get("key") for x in fm.get("_doc_refs", []) if isinstance(x, dict) and "key" in x})
                row.append(",".join(keys))
            elif c in ("_file_refs","file-keys","file_keys","file-ref"):
                keys = sorted({x.get("key") for x in fm.get("_file_refs", []) if isinstance(x, dict) and "key" in x})
                row.append(",".join(keys))
            else:
                # einfacher dot-get
                cur: Any = fm
                for p in c.split("."):
                    if isinstance(cur, dict) and p in cur:
                        cur = cur[p]
                    else:
                        cur = ""
                        break
                # List/Dict kurz und knackig stringifizieren
                if isinstance(cur, (list, dict)):
                    row.append(json.dumps(cur, ensure_ascii=False))
                else:
                    row.append("" if cur is None else str(cur))
        typer.echo(" | ".join(row))

# ---------- set-status ----------
@doc_app.command("set-status")
def set_status(
    uuid: str = typer.Argument(...),
    status: str = typer.Argument(...),
    base_dir: Path = typer.Option(Path("data"), "--base-dir"),
):
    if status not in VALID_STATUS:
        raise typer.BadParameter(f"status muss eines von {sorted(VALID_STATUS)} sein.")
    cur_dir = find_doc_dir(base_dir, uuid)
    if not cur_dir:
        raise typer.BadParameter(f"Dokument nicht gefunden: {uuid}")
    doc_path = cur_dir / "doc.md"
    fm, body = read_frontmatter(doc_path)
    fm["status"] = status
    # Zielverzeichnis
    new_dir = base_dir / status / uuid
    if cur_dir != new_dir:
        ensure_dir(new_dir.parent)
        if new_dir.exists():
            shutil.rmtree(new_dir)
        shutil.move(str(cur_dir), str(new_dir))
        doc_path = new_dir / "doc.md"
    write_frontmatter(doc_path, fm, body)
    typer.echo(str(doc_path))

# ---------- modify ----------
@doc_app.command("modify")
def modify(
    uuid: str = typer.Argument(...),
    body_arg: Optional[str] = typer.Argument(None, help="Neuer Body (optional, sonst stdin unverändert)"),
    set_: List[str] = typer.Option(None, "--set", help="property=value"),
    list_add: List[str] = typer.Option(None, "--list-add", help="property=value an Liste anhängen"),
    json_kv: List[str] = typer.Option(None, "--json", help="property=<JSON>"),
    add_doc: List[str] = typer.Option(None, "--add-doc", help="keyname=<uuid>"),
    doc_data: List[str] = typer.Option(None, "--doc-data", help="JSON für zuletzt hinzugefügten _doc_ref"),
    add_file: List[str] = typer.Option(None, "--add-file", help="file_key=./path"),
    file_data: List[str] = typer.Option(None, "--file-data", help="JSON für zuletzt hinzugefügte Datei"),
    base_dir: Path = typer.Option(Path("data"), "--base-dir"),
):
    cur_dir = find_doc_dir(base_dir, uuid)
    if not cur_dir:
        raise typer.BadParameter(f"Dokument nicht gefunden: {uuid}")
    doc_path = cur_dir / "doc.md"
    fm, body = read_frontmatter(doc_path)

    # set
    for item in set_ or []:
        prop, val = parse_prop_eq_val(item, "--set")
        set_in(fm, prop, parse_simple_value(val))

    # list-add
    for item in list_add or []:
        prop, val = parse_prop_eq_val(item, "--list-add")
        sentinel = "__APPEND_INIT__"
        set_in(fm, prop, sentinel)
        parts = _split_dot_path(prop)
        cur = fm
        for i, (k, idx) in enumerate(parts):
            last = i == len(parts)-1
            if idx is None:
                if last:
                    if cur.get(k) == sentinel:
                        cur[k] = []
                    if not isinstance(cur[k], list):
                        raise typer.BadParameter(f"{prop} ist keine Liste.")
                    cur[k].append(parse_simple_value(val))
                else:
                    cur = cur[k]
            else:
                lst = cur[k]
                if not isinstance(lst, list):
                    raise typer.BadParameter(f"{prop} ist keine Liste.")
                if last:
                    if lst[idx] == sentinel:
                        lst[idx] = []
                    if not isinstance(lst[idx], list):
                        raise typer.BadParameter(f"{prop} ist keine Liste.")
                    lst[idx].append(parse_simple_value(val))
                else:
                    cur = lst[idx]

    # json
    for item in json_kv or []:
        prop, js = parse_prop_eq_val(item, "--json")
        try:
            value = json.loads(js)
        except json.JSONDecodeError as e:
            raise typer.BadParameter(f"--json: ungültiges JSON für {prop}: {e}")
        set_in(fm, prop, value)

    # doc refs
    if add_doc:
        fm["_doc_refs"] = fm.get("_doc_refs", [])
        for spec in add_doc:
            key, uuid2 = parse_prop_eq_val(spec, "--add-doc")
            fm["_doc_refs"].append(DocRef(key=key.strip(), uuid=uuid2.strip()).model_dump())
        for js in doc_data or []:
            if not fm["_doc_refs"]:
                raise typer.BadParameter("--doc-data ohne vorhandenes --add-doc")
            d = json.loads(js) if js else {}
            fm["_doc_refs"][-1]["data"] = d

    # file refs (kopieren)
    pending_files: List[tuple[Path, FileRef]] = []
    for spec in add_file or []:
        key, path_str = parse_prop_eq_val(spec, "--add-file")
        src = Path(path_str).expanduser()
        if not src.exists() or not src.is_file():
            raise typer.BadParameter(f"--add-file: Datei nicht gefunden: {src}")
        fid = str(uuid4())
        pending_files.append((src, FileRef(key=key.strip(), filename=src.name, uuid=fid)))

    for js in file_data or []:
        if not pending_files:
            raise typer.BadParameter("--file-data ohne vorhandenes --add-file")
        d = json.loads(js) if js else {}
        pending_files[-1][1].data = d

    if pending_files:
        fm["_file_refs"] = fm.get("_file_refs", [])
        for src, ref in pending_files:
            shutil.copyfile(src, cur_dir / ref.uuid)
            fm["_file_refs"].append(ref.model_dump())

    # body
    new_body = read_body_param_or_stdin(body_arg) if (body_arg is not None or not sys.stdin.isatty()) else body
    write_frontmatter(doc_path, fm, new_body)
    typer.echo(str(doc_path))

# ---------- drop ----------
@doc_app.command("drop")
def drop(
    uuid: str = typer.Argument(...),
    base_dir: Path = typer.Option(Path("data"), "--base-dir"),
):
    dir_ = find_doc_dir(base_dir, uuid)
    if not dir_:
        raise typer.BadParameter(f"Dokument nicht gefunden: {uuid}")
    shutil.rmtree(dir_)
    typer.echo(f"deleted {uuid}")

# ---------- drop-all ----------
@doc_app.command("drop-all")
def drop_all(
    force: bool = typer.Option(False, "--force", help="ohne Nachfrage löschen"),
    base_dir: Path = typer.Option(Path("data"), "--base-dir"),
):
    all_dirs = []
    for status in VALID_STATUS:
        root = base_dir / status
        if not root.exists(): continue
        all_dirs += [p for p in root.iterdir() if p.is_dir()]
    if not all_dirs:
        typer.echo("nichts zu löschen")
        raise typer.Exit()

    if not force:
        typer.confirm(f"Wirklich ALLE ({len(all_dirs)}) Dokumente löschen?", abort=True)

    for d in all_dirs:
        shutil.rmtree(d)
    typer.echo(f"deleted {len(all_dirs)} docs")

if __name__ == "__main__":
    app()



# erweitere das cli `idflow doc` um folgende Befehle:

# - list
# hierbei sollten filter gesetzt werden können, wie z.b. `--filter title="observ*" --filter priority=">0.5"`
# In der Ausgabe wird per default nur die uuid je zeile ausgegeben. Die einzelnen Properties sollen aber definierbar sein (z.B. --col title).
# Für die Spezialfelder refs und docs zählt nur, ob es zum übermittelten filter key eine oder mehrere Einträge gibt. In der Ausgabe sollen alle keys "," separiert dargestellt werden

# - set-status Statusänderung

# - modify
# hierbei sollen weitere werte gesetzt werden können (via set, list-add, ...).

# - drop
# übergabe einer einzelnen uuid zum Löschen

# - drop-all
# mit extra prompt (oder opt. --force)