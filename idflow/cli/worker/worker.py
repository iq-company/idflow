from __future__ import annotations
import typer
import sys
import signal
import time
from pathlib import Path
from typing import List, Optional
import importlib.util

from conductor.client.configuration.configuration import Configuration
from conductor.client.worker.worker import Worker
from conductor.client.automator.task_handler import TaskHandler

from ...core.workflow_manager import get_workflow_manager

app = typer.Typer(help="Manage Conductor task workers")


def discover_worker_files() -> List[Path]:
    """Discover all worker Python files."""
    tasks_dir = Path("idflow/tasks")
    worker_files = []

    for task_file in tasks_dir.rglob("*.py"):
        if task_file.name != "__init__.py":
            with open(task_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "@worker_task" in content:
                    worker_files.append(task_file)

    return worker_files


def extract_task_name_from_file(task_file: Path) -> Optional[str]:
    """Extract task name from worker file."""
    try:
        with open(task_file, 'r', encoding='utf-8') as f:
            content = f.read()

        import re
        match = re.search(r"@worker_task\(task_definition_name='([^']+)'\)", content)
        if match:
            return match.group(1)
    except Exception:
        pass

    return None


def load_task_function(task_file: Path, task_name: str):
    """Load the task function from a Python file."""
    spec = importlib.util.spec_from_file_location('task_module', str(task_file))
    task_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(task_module)

    # Get the task function - try common function names
    task_func = None
    for func_name in ['execute', task_name, 'main']:
        task_func = getattr(task_module, func_name, None)
        if task_func:
            break

    if not task_func:
        raise ValueError(f'No task function found in {task_file}. Available functions: {[name for name in dir(task_module) if not name.startswith("_")]}')

    return task_func


@app.command("list")
def list_workers():
    """List all available task workers."""
    worker_files = discover_worker_files()

    if not worker_files:
        typer.echo("No worker files found")
        return

    typer.echo(f"Found {len(worker_files)} worker files:")

    for task_file in worker_files:
        task_name = extract_task_name_from_file(task_file)
        if task_name:
            typer.echo(f"  - {task_name} ({task_file})")
        else:
            typer.echo(f"  - {task_file} (no task name found)")


@app.command("start")
def start_workers(
    workers: Optional[List[str]] = typer.Option(None, "--worker", "-w", help="Specific workers to start"),
    all: bool = typer.Option(False, "--all", "-a", help="Start all available workers")
):
    """Start task workers using Conductor SDK."""
    if not all and not workers:
        typer.echo("Please specify --all or --worker <name>")
        raise typer.Exit(1)

    worker_files = discover_worker_files()

    if not worker_files:
        typer.echo("No worker files found")
        return

    # Filter workers if specific ones requested
    selected_workers = []
    for task_file in worker_files:
        task_name = extract_task_name_from_file(task_file)
        if task_name:
            if all or (workers and task_name in workers):
                selected_workers.append((task_file, task_name))

    if not selected_workers:
        typer.echo("No workers selected")
        return

    typer.echo(f"Starting {len(selected_workers)} workers...")

    # Load all task functions
    workers_list = []
    for task_file, task_name in selected_workers:
        try:
            load_task_function(task_file, task_name)
            # The @worker_task decorator should handle the task definition
            typer.echo(f"✓ Loaded worker for {task_name}")
        except Exception as e:
            typer.echo(f"✗ Failed to load worker {task_name}: {e}")

    # Create configuration
    # TODO configuration needs to be created based on the config/idflow.yml settings.
    from ...core.config import get_config
    config = get_config() # TODO: generate global config utility

    config = Configuration()

    # Create task handler
    task_handler = TaskHandler(
        workers=[],
        scan_for_annotated_workers=True,
        configuration=config
    )

    def signal_handler(signum, frame):
        typer.echo("\nShutting down workers...")
        task_handler.stop_processes()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        typer.echo("Workers started. Press Ctrl+C to stop.")
        task_handler.start_processes()
        # task_handler.join_processes()
    except KeyboardInterrupt:
        typer.echo("\nShutting down workers...")
        task_handler.stop_processes()


@app.command("upload")
def upload_workflows(
    force: bool = typer.Option(False, "--force", help="Force upload even if up to date")
):
    """Upload all workflows to Conductor. Tasks are automatically registered via @worker_task decorators."""
    workflow_manager = get_workflow_manager()

    typer.echo("Uploading workflows to Conductor...")
    typer.echo("Note: Tasks are automatically registered via @worker_task decorators when workers start.")

    results = workflow_manager.upload_workflows(force=force)

    # Show results
    typer.echo("\nWorkflow upload results:")
    for name, success in results.items():
        status = "✓" if success else "✗"
        typer.echo(f"  {status} {name}")

    # Summary
    total_workflows = len(results)
    successful_workflows = sum(1 for success in results.values() if success)

    typer.echo(f"\nSummary: {successful_workflows}/{total_workflows} workflows uploaded successfully")
    typer.echo("Tasks will be automatically registered when workers start.")


if __name__ == "__main__":
    app()
