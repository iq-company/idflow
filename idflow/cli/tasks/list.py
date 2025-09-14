from __future__ import annotations
import typer
from idflow.core.workflow_manager import get_workflow_manager
from idflow.core.resource_resolver import ResourceResolver

def list_tasks(
    local: bool = typer.Option(False, "--local", help="Show only local task files"),
    remote: bool = typer.Option(False, "--remote", help="Show only tasks in Conductor"),
    all: bool = typer.Option(False, "--all", help="Show both local and remote tasks"),
    sync: bool = typer.Option(False, "--sync", help="Show synchronization status")
):
    """List tasks (local files and/or Conductor)."""
    workflow_manager = get_workflow_manager()

    if sync:
        # Show synchronization status
        status = workflow_manager.get_task_sync_status()

        typer.echo("Task Synchronization Status:")
        typer.echo(f"  Local tasks: {len(status['local'])}")
        typer.echo(f"  Remote tasks: {len(status['remote'])}")
        typer.echo(f"  Common: {len(status['common'])}")
        typer.echo(f"  Only local: {len(status['only_local'])}")
        typer.echo(f"  Only remote: {len(status['only_remote'])}")

        if status['only_local']:
            typer.echo("\nTasks only available locally:")
            for task in sorted(status['only_local']):
                typer.echo(f"  {task}")

        if status['only_remote']:
            typer.echo("\nTasks only available remotely:")
            for task in sorted(status['only_remote']):
                typer.echo(f"  {task}")

        if status['common']:
            typer.echo("\nTasks available both locally and remotely:")
            for task in sorted(status['common']):
                typer.echo(f"  {task}")

        return

    if not (local or remote or all):
        # Default: show both
        local = True
        remote = True

    if local or all:
        typer.echo("Local task files:")

        # Use ResourceResolver for consistent task discovery and classification
        resolver = ResourceResolver()
        required = set(workflow_manager.required_task_names())

        # Get task names and origins using same logic as vendor list
        lib_t, vend_t, proj_t = resolver.names_by_base("tasks", "*", name_extractor=None, item_type="dir")
        task_names = sorted(set().union(lib_t, vend_t, proj_t))

        if not task_names:
            typer.echo("  No task files found")
        else:
            # Build rows for tabular display
            rows = []
            for name in task_names:
                origin, short = resolver.classify_origin_from_sets(name, lib_t, vend_t, proj_t)
                status = "active" if name in required else "inactive"
                rows.append((name, status, origin))

            # Calculate column widths
            name_w = max(len(r[0]) for r in rows)
            status_w = max(len(r[1]) for r in rows)
            origin_w = max(len(r[2]) for r in rows)

            for name, status, origin in rows:
                status_color = "green" if status == "active" else "red"
                # Apply color but keep original length for padding
                styled_status = typer.style(status, fg=status_color)
                typer.echo(f"  {name.ljust(name_w)}  {styled_status}{' ' * (status_w - len(status))}  {origin.ljust(origin_w)}")

        if remote or all:
            typer.echo()

    if remote or all:
        typer.echo("Tasks in Conductor:")
        remote_tasks = workflow_manager.list_tasks_remote()

        if not remote_tasks:
            typer.echo("  No tasks found in Conductor")
        else:
            for task in remote_tasks:
                name = task.get('name')
                if name:
                    typer.echo(f"  {name}")
