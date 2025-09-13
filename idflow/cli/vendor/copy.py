from __future__ import annotations
import typer
from pathlib import Path
from idflow.core.vendor import (
    list_copyable,
    list_sections,
    list_elements,
    normalize_element_name,
    is_extended,
    copy_tree_with_prompt,
    copy_element_with_target_prompt,
)

def copy_vendor(
    all_: bool = typer.Option(False, "--all", help="Copy all allowed directories"),
    dest: Path = typer.Option(Path("."), "--dest", help="Target project directory (default: current directory)"),
    section: str = typer.Option(None, "--section", help="Section (tasks|workflows|stages) directly select"),
    element: str = typer.Option(None, "--element", help="Element within the section directly select"),
):
    # Extract default values from typer.Option objects for direct function calls
    if hasattr(all_, 'default'):
        all_ = all_.default
    if hasattr(dest, 'default'):
        dest = dest.default
    dest = dest.resolve()
    items = list_copyable()

    if not items:
        typer.echo("No defined vendor directories.")
        raise typer.Exit()

    if all_:
        for _, rel, src in items:
            _copy_one(src, dest, rel)
        typer.echo("Done.")
        return

    # Section selection (prompt if not provided)
    available_sections = list_sections()

    selected_section: str
    if section:
        if section not in available_sections:
            raise typer.BadParameter(f"Unknown section: {section}")
        selected_section = section
    else:
        typer.echo("Select section:")
        for idx, sec in enumerate(available_sections, start=1):
            typer.echo(f"  [{idx}] {sec}")
        idx_str = typer.prompt("Please enter a number")
        try:
            idx = int(idx_str)
        except ValueError:
            raise typer.BadParameter("Please enter a valid number.")
        if idx < 1 or idx > len(available_sections):
            raise typer.BadParameter(f"Invalid selection: {idx}")
        selected_section = available_sections[idx - 1]

    # Element selection within section
    if element:
        normalized = normalize_element_name(selected_section, element)
        if normalized is None:
            raise typer.BadParameter(f"Element not found: {element} in {selected_section}")
        chosen_element = normalized
    else:
        elements = list_elements(selected_section)
        if not elements:
            typer.echo("No elements available in this section.")
            raise typer.Exit()
        typer.echo(f"{selected_section}")
        for i, name in enumerate(elements, start=1):
            extended = is_extended(selected_section, name, dest)
            suffix = " (extended)" if extended else ""
            typer.echo(f"  [{i}] {name}{suffix}")
        idx_str = typer.prompt("Please enter a number")
        try:
            idx = int(idx_str)
        except ValueError:
            raise typer.BadParameter("Please enter a valid number.")
        if idx < 1 or idx > len(elements):
            raise typer.BadParameter(f"Invalid selection: {idx}")
        chosen_element = elements[idx - 1]

    copy_element_with_target_prompt(selected_section, chosen_element, dest)
    typer.echo("Done.")

def _copy_one(src: Path, dest: Path, rel: str) -> None:
    out_dir = (dest / rel).resolve()
    # Safety net: don't write outside dest
    # (loose here because we intentionally append rel; alternatively omit)
    copy_tree_with_prompt(src, out_dir)

