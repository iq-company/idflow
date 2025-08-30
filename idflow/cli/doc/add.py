from __future__ import annotations
import json, shutil, sys
from pathlib import Path
from typing import Optional, List, Any, Dict, Tuple
from uuid import uuid4

import typer
from idflow.core.models import VALID_STATUS, DocRef, FileRef
from idflow.core.repo import find_doc_dir
from idflow.core.io import ensure_dir, write_frontmatter
from idflow.core.props import set_in, parse_simple_value, _split_dot_path
from idflow.core.config import config

def _parse_prop_eq_val(arg: str, flag: str) -> tuple[str, str]:
    if "=" not in arg:
        raise typer.BadParameter(f"{flag} erwartet property=value, nicht: {arg}")
    return arg.split("=", 1)

def _read_body_param_or_stdin(arg_text: Optional[str]) -> str:
    if arg_text not in (None, ""):
        return arg_text
    if not sys.stdin.isatty():
        try:
            return sys.stdin.read()
        except OSError:
            # pytest capture mode - return empty string
            return ""
    return ""

def add(
    body_arg: Optional[str] = typer.Argument(None, help="Body-Text (optional, sonst stdin)"),
    status: str = typer.Option("inbox", "--status", help="inbox|active|done|blocked|archived"),
    set_: List[str] = typer.Option(None, "--set", help="property=value (Dot-Pfade erlaubt)"),
    list_add: List[str] = typer.Option(None, "--list-add", help="property=value an Liste anhängen"),
    json_kv: List[str] = typer.Option(None, "--json", help="property=<JSON> (dict/list/value)"),
    add_doc: List[str] = typer.Option(None, "--add-doc", help="keyname=<uuid>"),
    doc_data: List[str] = typer.Option(None, "--doc-data", help="JSON für zuletzt hinzugefügten _doc_ref"),
    add_file: List[str] = typer.Option(None, "--add-file", help="file_key=./path/to/file.ext"),
    file_data: List[str] = typer.Option(None, "--file-data", help="JSON für zuletzt hinzugefügte Datei"),
):
    # Extract default values from typer objects for direct function calls
    if hasattr(body_arg, 'default'):
        body_arg = body_arg.default
    if hasattr(status, 'default'):
        status = status.default
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

    if status not in VALID_STATUS:
        raise typer.BadParameter(f"--status muss eines von {sorted(VALID_STATUS)} sein.")

    doc_id = str(uuid4())
    fm: dict = {"id": doc_id, "status": status}

    # --set
    for item in set_ or []:
        prop, val = _parse_prop_eq_val(item, "--set")
        set_in(fm, prop, parse_simple_value(val))

    # --list-add
    for item in list_add or []:
        prop, val = _parse_prop_eq_val(item, "--list-add")
        # Parse the property path
        parts = prop.split(".")
        cur = fm

        # Navigate to the parent of the target property
        for p in parts[:-1]:
            if p not in cur:
                cur[p] = {}
            cur = cur[p]

        # Get the target property name
        target_prop = parts[-1]

        # Initialize the list if it doesn't exist
        if target_prop not in cur:
            cur[target_prop] = []
        elif not isinstance(cur[target_prop], list):
            raise typer.BadParameter(f"{prop} ist keine Liste.")

        # Append the value
        cur[target_prop].append(parse_simple_value(val))

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

    # Ziel anlegen
    out_dir = base_dir / status / doc_id
    ensure_dir(out_dir)
    out_file = out_dir / "doc.md"

    # Dateien kopieren (Name = UUID)
    if pending_files:
        fm["_file_refs"] = fm.get("_file_refs", [])
        for src, ref in pending_files:
            shutil.copyfile(src, out_dir / ref.uuid)
            fm["_file_refs"].append(ref.model_dump())

    # Body
    body = _read_body_param_or_stdin(body_arg)

    # Schreiben
    write_frontmatter(out_file, fm, body)
    typer.echo(doc_id)

