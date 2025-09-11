from __future__ import annotations
import typer
from idflow.core.workflow_manager import get_workflow_manager

def upload_tasks(
    task_name: str = typer.Argument(None, help="Specific task name to upload (optional)"),
    force: bool = typer.Option(False, "--force", help="Force upload even if task exists"),
    all: bool = typer.Option(False, "--all", help="Upload all tasks")
):
    """Upload tasks to Conductor."""
    workflow_manager = get_workflow_manager()

    if task_name:
        # Upload specific task
        typer.echo(f"Uploading task: {task_name}")
        success = workflow_manager.upload_task(task_name, force)
        if success:
            typer.echo(f"✓ Successfully uploaded task: {task_name}")
        else:
            typer.echo(f"✗ Failed to upload task: {task_name}")
            raise typer.Exit(1)
    elif all:
        # Upload all tasks
        typer.echo("Uploading all tasks...")
        results = workflow_manager.upload_tasks(force)

        successful = sum(1 for success in results.values() if success)
        total = len(results)

        typer.echo(f"\nUpload Summary: {successful}/{total} tasks uploaded successfully")

        if successful < total:
            failed_tasks = [name for name, success in results.items() if not success]
            typer.echo(f"Failed tasks: {', '.join(failed_tasks)}")
            raise typer.Exit(1)
    else:
        typer.echo("Please specify either a task name or use --all to upload all tasks")
        raise typer.Exit(1)
