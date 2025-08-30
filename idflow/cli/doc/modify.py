from __future__ import annotations
import json, shutil, sys
from pathlib import Path
from typing import Optional, List, Any, Dict, Tuple
from uuid import uuid4

import typer
from idflow.core.models import DocRef, FileRef
from idflow.core.repo import find_doc_dir
from idflow.core.io import read_frontmatter, write_frontmatter
from idflow.core.props import set_in, parse_simple_value
from idflow.core.config import config

def _parse_prop_eq_val(arg: str, flag: str) -> tuple[str, str]:
    if "=" not in arg:
        raise typer.BadParameter(f"{flag} erwartet property=value, nicht: {arg}")
    return arg.split("=", 1)

def _read_body_arg_or_keep(body_arg: Optional[str], current_body: str) -> str:
    if body_arg is not None:
        # argument explizit übergeben → ggf. aus stdin lesen, sonst das arg
        if body_arg == "" and not sys.stdin.isatty():
            try:
                return sys.stdin.read()
            except OSError:
                # pytest capture mode - return empty string
                return ""
        return body_arg
    # body_arg nicht gesetzt → stdin? sonst unverändert lassen
    if not sys.stdin.isatty():
        try:
            return sys.stdin.read()
        except OSError:
            # pytest capture mode - return current body
            return current_body
    return current_body

def modify(
    uuid: str = typer.Argument(...),
    body_arg: Optional[str] = typer.Argument(None, help="Neuer Body (optional, sonst stdin oder unverändert)"),
    set_: List[str] = typer.Option(None, "--set", help="property=value"),
    list_add: List[str] = typer.Option(None, "--list-add", help="property=value an Liste anhängen"),
    json_kv: List[str] = typer.Option(None, "--json", help="property=<JSON>"),
    add_doc: List[str] = typer.Option(None, "--add-doc", help="keyname=<uuid>"),
    doc_data: List[str] = typer.Option(None, "--doc-data", help="JSON für zuletzt hinzugefügten _doc_ref"),
    add_file: List[str] = typer.Option(None, "--add-file", help="file_key=./path"),
    file_data: List[str] = typer.Option(None, "--file-data", help="JSON für zuletzt hinzugefügte Datei"),
):
    # Extract default values from typer objects for direct function calls
    if hasattr(uuid, 'default'):
        uuid = uuid.default
    if hasattr(body_arg, 'default'):
        body_arg = body_arg.default
    if hasattr(set_, 'default'):
        set_ = set_.default
    if hasattr(list_add, 'default'):
        list_add = list_add.default
    if hasattr(json_kv, 'default'):
        json_kv = json_kv.default
    if hasattr(add_doc, 'default'):
        add_doc = add_doc.default
    if hasattr(doc_data, 'default'):
        doc_data = doc_data.default
    if hasattr(add_file, 'default'):
        add_file = add_file.default
    if hasattr(file_data, 'default'):
        file_data = file_data.default

    # Use configuration for base_dir
    base_dir = config.base_dir

    cur_dir = find_doc_dir(base_dir, uuid)
    if not cur_dir:
        raise typer.BadParameter(f"Dokument nicht gefunden: {uuid}")
    doc_path = cur_dir / "doc.md"
    fm, body = read_frontmatter(doc_path)

    # --set
    for item in set_ or []:
        prop, val = _parse_prop_eq_val(item, "--set")
        set_in(fm, prop, parse_simple_value(val))

    # --list-add
    for item in list_add or []:
        prop, val = _parse_prop_eq_val(item, "--list-add")
        sentinel = "__APPEND_INIT__"
        set_in(fm, prop, sentinel)
        parts = prop.split(".")
        cur: Any = fm
        for i, p in enumerate(parts):
            last = i == len(parts) - 1
            if last:
                if cur.get(p) == sentinel:
                    cur[p] = []
                if not isinstance(cur[p], list):
                    raise typer.BadParameter(f"{prop} ist keine Liste.")
                cur[p].append(parse_simple_value(val))
            else:
                cur = cur[p]

    # --json
    for item in json_kv or []:
        prop, js = _parse_prop_eq_val(item, "--json")
        try:
            value = json.loads(js)
        except json.JSONDecodeError as e:
            raise typer.BadParameter(f"--json: ungültiges JSON für {prop}: {e}")
        set_in(fm, prop, value)

    # _doc_refs
    if add_doc:
        fm["_doc_refs"] = fm.get("_doc_refs", [])
        for spec in add_doc:
            key, uuid = _parse_prop_eq_val(spec, "--add-doc")
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
        key, path_str = _parse_prop_eq_val(spec, "--add-file")
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

    # Dateien kopieren (Name = UUID)
    if pending_files:
        fm["_file_refs"] = fm.get("_file_refs", [])
        for src, ref in pending_files:
            shutil.copyfile(src, cur_dir / ref.uuid)
            fm["_file_refs"].append(ref.model_dump())

    # Body
    body = _read_body_arg_or_keep(body_arg, body)

    # Schreiben
    write_frontmatter(doc_path, fm, body)
    typer.echo(str(doc_path))

