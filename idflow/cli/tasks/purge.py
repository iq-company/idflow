from __future__ import annotations
import typer
from idflow.core.workflow_manager import get_workflow_manager

def purge_tasks(
    task_name: str = typer.Argument(None, help="Specific task name to purge (optional)"),
    force: bool = typer.Option(False, "--force", help="Force purge even if task is in use"),
    orphaned: bool = typer.Option(False, "--orphaned", help="Purge tasks that are no longer available locally"),
    confirm: bool = typer.Option(False, "-y", help="Skip confirmation prompt")
):
    """Purge tasks from Conductor."""
    workflow_manager = get_workflow_manager()

    if task_name:
        # Purge specific task
        if not confirm:
            if not typer.confirm(f"Are you sure you want to purge task '{task_name}'?"):
                typer.echo("Purge cancelled")
                return

        typer.echo(f"Purging task: {task_name}")
        success = workflow_manager.purge_task(task_name, force)
        if success:
            typer.echo(f"✓ Successfully purged task: {task_name}")
        else:
            typer.echo(f"✗ Failed to purge task: {task_name}")
            raise typer.Exit(1)
    elif orphaned:
        # Purge orphaned tasks (only remote, not local)
        sync_status = workflow_manager.get_task_sync_status()
        orphaned_tasks = sync_status['only_remote']

        if not orphaned_tasks:
            typer.echo("No orphaned tasks found (all remote tasks are also available locally)")
            return

        # Show tasks that will be purged
        typer.echo("The following tasks will be purged (not available locally):")
        for task in sorted(orphaned_tasks):
            typer.echo(f"  - {task}")

        if not confirm:
            if not typer.confirm(f"\nAre you sure you want to purge these {len(orphaned_tasks)} orphaned tasks?"):
                typer.echo("Purge cancelled")
                return

        typer.echo(f"\nPurging {len(orphaned_tasks)} orphaned tasks...")
        successful = 0
        failed = 0

        for task_name in orphaned_tasks:
            typer.echo(f"Purging task: {task_name}")
            success = workflow_manager.purge_task(task_name, force)
            if success:
                successful += 1
            else:
                failed += 1

        typer.echo(f"\nPurge Summary: {successful} tasks purged successfully, {failed} failed")

        if failed > 0:
            raise typer.Exit(1)
    else:
        typer.echo("Please specify either a task name or use --orphaned to purge orphaned tasks")
        raise typer.Exit(1)
