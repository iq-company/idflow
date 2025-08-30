from __future__ import annotations
import json, shutil, sys
from pathlib import Path
from typing import Optional, List, Any, Dict, Tuple
from uuid import uuid4

import typer
from idflow.core.fs_markdown import FSMarkdownDocument
from idflow.core.config import config

def _parse_prop_eq_val(arg: str, flag: str) -> tuple[str, str]:
    if "=" not in arg:
        raise typer.BadParameter(f"{flag} expects property=value, not: {arg}")
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
    body_arg: Optional[str] = typer.Argument(None, help="Body text (optional, otherwise stdin)"),
    status: str = typer.Option("inbox", "--status", help="inbox|active|done|blocked|archived"),
    set_: List[str] = typer.Option(None, "--set", help="property=value (dot paths allowed)"),
    list_add: List[str] = typer.Option(None, "--list-add", help="property=value to append to list"),
    json_kv: List[str] = typer.Option(None, "--json", help="property=<JSON> (dict/list/value)"),
    add_doc: List[str] = typer.Option(None, "--add-doc", help="keyname=<uuid>"),
    doc_data: List[str] = typer.Option(None, "--doc-data", help="JSON for last added _doc_ref"),
    add_file: List[str] = typer.Option(None, "--add-file", help="file_key=./path/to/file.ext"),
    file_data: List[str] = typer.Option(None, "--file-data", help="JSON for last added file"),
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

    # Create new document using ORM
    doc = FSMarkdownDocument(status=status)

    # Set body content
    body = _read_body_param_or_stdin(body_arg)
    doc.body = body

    # --set
    for item in set_ or []:
        prop, val = _parse_prop_eq_val(item, "--set")
        doc.set(prop, val)

    # --list-add
    for item in list_add or []:
        prop, val = _parse_prop_eq_val(item, "--list-add")
        # Parse the property path
        parts = prop.split(".")
        cur = doc._data

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
            raise typer.BadParameter(f"{prop} is not a list.")

        # Append the value
        cur[target_prop].append(val)

    # --json
    for item in json_kv or []:
        prop, js = _parse_prop_eq_val(item, "--json")
        try:
            value = json.loads(js)
        except json.JSONDecodeError as e:
            raise typer.BadParameter(f"--json: invalid JSON for {prop}: {e}")
        doc.set(prop, value)

    # _doc_refs
    if add_doc:
        for spec in add_doc:
            key, uuid = _parse_prop_eq_val(spec, "--add-doc")
            doc.add_doc_ref(key=key.strip(), uuid=uuid.strip())

        # Add data to the last added doc ref
        for js in doc_data or []:
            if not doc.doc_refs:
                raise typer.BadParameter("--doc-data without existing --add-doc")
            try:
                d = json.loads(js) if js else {}
            except json.JSONDecodeError as e:
                raise typer.BadParameter(f"--doc-data JSON invalid: {e}")
            doc.doc_refs[-1].data = d

    # _file_refs
    pending_files: List[tuple[Path, str]] = []
    for spec in add_file or []:
        key, path_str = _parse_prop_eq_val(spec, "--add-file")
        src = Path(path_str).expanduser()
        if not src.exists() or not src.is_file():
            raise typer.BadParameter(f"--add-file: file not found: {src}")
        pending_files.append((src, key.strip()))

    # Add file data to the last added file ref
    for js in file_data or []:
        if not pending_files:
            raise typer.BadParameter("--file-data without existing --add-file")
        try:
            d = json.loads(js) if js else {}
        except json.JSONDecodeError as e:
                            raise typer.BadParameter(f"--file-data JSON invalid: {e}")
        # Store the data to be applied when copying the file
        pending_files[-1] = (pending_files[-1][0], pending_files[-1][1], d)

    # Copy files and create file references
    for file_info in pending_files:
        if len(file_info) == 3:
            src, key, data = file_info
        else:
            src, key = file_info
            data = {}

        # Use the ORM method to copy file and create reference
        file_ref = doc.copy_file(src, key)
        file_ref.data = data

    # Create the document
    doc.create()

    # Output the document ID
    typer.echo(doc.id)

