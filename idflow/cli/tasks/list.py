from __future__ import annotations
import typer
from idflow.core.workflow_manager import get_workflow_manager

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
        tasks = workflow_manager.discover_tasks()

        if not tasks:
            typer.echo("  No task files found")
        else:
            for task_file in tasks:
                task_def = workflow_manager.load_task_definition(task_file)
                if task_def:
                    name = task_def.get('name', 'unknown')
                    typer.echo(f"  {name}")
                else:
                    typer.echo(f"  {task_file.name} (invalid)")

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
