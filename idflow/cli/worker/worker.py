from __future__ import annotations
import typer
import sys
import signal
import time
import os
import subprocess
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


@app.command("ps")
def list_running_workers(
    full_command: bool = typer.Option(False, "--full", "-f", help="Show full command path")
):
    """List running worker processes."""
    try:
        # Find Python processes that look like workers
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            check=True
        )

        lines = result.stdout.split('\n')
        worker_lines = []

        for line in lines:
            # Look for processes that contain idflow and worker-related terms
            # But exclude kernel workers, system processes, and CLI commands
            if (any(term in line.lower() for term in ['idflow', 'conductor']) or
                ('python' in line.lower() and any(term in line.lower() for term in ['worker', 'task', 'conductor']))):
                # Skip the header line, kernel workers, and CLI commands
                if (not line.startswith('USER') and
                    not line.startswith('root') and
                    'kworker' not in line and
                    'worker ps' not in line and
                    'worker killall' not in line and
                    'worker list' not in line and
                    'worker start' in line):  # Only show actual worker start processes
                    worker_lines.append(line)

        if worker_lines:
            typer.echo("Running worker processes:")
            if full_command:
                typer.echo("WORKER                    USER       PID  %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND")
            else:
                typer.echo("WORKER                    USER       PID  %CPU %MEM    VSZ   RSS TTY      STAT START   TIME")

            for line in worker_lines:
                # Extract worker name from command line
                worker_name = "unknown"
                if "--worker" in line:
                    # Extract worker name from --worker argument
                    import re
                    match = re.search(r'--worker\s+(\w+)', line)
                    if match:
                        worker_name = match.group(1)
                elif "--all" in line:
                    worker_name = "all"

                # Format worker name to fit in 25 characters
                worker_display = worker_name[:25].ljust(25)

                # Parse the ps output
                parts = line.split()
                if len(parts) >= 11:
                    if full_command:
                        # Show full command
                        command_start = 10  # Start of command in ps output
                        command = " ".join(parts[command_start:])
                        new_line = f"{worker_display} {parts[0]:<10} {parts[1]:<6} {parts[2]:<5} {parts[3]:<5} {parts[4]:<8} {parts[5]:<8} {parts[6]:<8} {parts[7]:<5} {parts[8]:<8} {parts[9]:<8} {command}"
                    else:
                        # Show only worker name, no command
                        new_line = f"{worker_display} {parts[0]:<10} {parts[1]:<6} {parts[2]:<5} {parts[3]:<5} {parts[4]:<8} {parts[5]:<8} {parts[6]:<8} {parts[7]:<5} {parts[8]:<8} {parts[9]:<8}"
                    typer.echo(new_line)
                else:
                    # Fallback to original line if parsing fails
                    if full_command:
                        typer.echo(f"{worker_display} {line}")
                    else:
                        typer.echo(f"{worker_display} {line}")
        else:
            typer.echo("No worker processes found")

    except subprocess.CalledProcessError as e:
        typer.echo(f"Error listing processes: {e}")
        sys.exit(1)
    except FileNotFoundError:
        typer.echo("Error: 'ps' command not found. This command requires Unix/Linux system.")
        sys.exit(1)


@app.command("killall")
def kill_workers(
    pattern: Optional[str] = typer.Argument(None, help="Worker name substring to match (optional, kills all if not provided)"),
    kill: bool = typer.Option(False, "--kill", "-k", help="Use SIGKILL instead of SIGTERM"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt")
):
    """Kill worker processes by worker name substring."""
    try:
        # First, list processes that match the pattern
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            check=True
        )

        lines = result.stdout.split('\n')
        matching_pids = []

        for line in lines:
            # Only match actual worker processes, not CLI commands
            if ('worker start' in line and
                'worker ps' not in line and
                'worker killall' not in line and
                'worker list' not in line and
                not line.startswith('USER')):

                # Extract worker name from command line
                worker_name = "unknown"
                if "--worker" in line:
                    import re
                    match = re.search(r'--worker\s+(\w+)', line)
                    if match:
                        worker_name = match.group(1)
                elif "--all" in line:
                    worker_name = "all"

                # If no pattern provided, match all workers
                # If pattern provided, check if it's contained in worker name
                if pattern is None or pattern.lower() in worker_name.lower():
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            pid = int(parts[1])
                            matching_pids.append((pid, line, worker_name))
                        except ValueError:
                            continue

        if not matching_pids:
            pattern_desc = "any pattern" if pattern is None else f"pattern '{pattern}'"
            typer.echo(f"No worker processes found matching {pattern_desc}")
            return

        pattern_desc = "all workers" if pattern is None else f"pattern '{pattern}'"
        typer.echo(f"Found {len(matching_pids)} worker processes matching {pattern_desc}:")
        typer.echo("WORKER                    USER       PID  %CPU %MEM    VSZ   RSS TTY      STAT START   TIME")

        for pid, line, worker_name in matching_pids:
            # Format worker name to fit in 25 characters
            worker_display = worker_name[:25].ljust(25)

            # Parse the ps output
            parts = line.split()
            if len(parts) >= 11:
                # Show only worker name, no command (like ps without --full)
                new_line = f"{worker_display} {parts[0]:<10} {parts[1]:<6} {parts[2]:<5} {parts[3]:<5} {parts[4]:<8} {parts[5]:<8} {parts[6]:<8} {parts[7]:<5} {parts[8]:<8} {parts[9]:<8}"
                typer.echo(new_line)
            else:
                # Fallback to original line if parsing fails
                typer.echo(f"{worker_display} {line}")

        if not yes:
            confirm = typer.confirm(f"Kill these {len(matching_pids)} processes?")
            if not confirm:
                typer.echo("Cancelled")
                return

        # Kill the processes
        killed_count = 0
        signal_name = "SIGKILL" if kill else "SIGTERM"
        for pid, line, worker_name in matching_pids:
            try:
                signal_to_use = signal.SIGKILL if kill else signal.SIGTERM
                os.kill(pid, signal_to_use)
                killed_count += 1
                typer.echo(f"Killed PID {pid} ({worker_name}) with {signal_name}")
            except ProcessLookupError:
                typer.echo(f"Process {pid} ({worker_name}) already terminated")
            except PermissionError:
                typer.echo(f"Permission denied to kill PID {pid} ({worker_name})")
            except Exception as e:
                typer.echo(f"Error killing PID {pid} ({worker_name}): {e}")

        typer.echo(f"Killed {killed_count} processes")

    except subprocess.CalledProcessError as e:
        typer.echo(f"Error listing processes: {e}")
        sys.exit(1)
    except FileNotFoundError:
        typer.echo("Error: 'ps' command not found. This command requires Unix/Linux system.")
        sys.exit(1)


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


if __name__ == "__main__":
    app()
