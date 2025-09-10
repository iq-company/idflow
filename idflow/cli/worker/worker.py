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


def is_child_process(pid: int, parent_pid: int) -> bool:
    """Check if a process is a child of the parent process."""
    try:
        # Get the parent process ID of the given process
        result = subprocess.run(
            ["ps", "-o", "ppid=", "-p", str(pid)],
            capture_output=True,
            text=True,
            check=True
        )
        ppid = int(result.stdout.strip())
        return ppid == parent_pid
    except (ValueError, subprocess.CalledProcessError, FileNotFoundError):
        return False


def determine_process_type(current_pid: int, ppid: int, memory_usage: float) -> str:
    """Determine process type based on hierarchy and characteristics."""
    if ppid is None:
        return "unknown"

    # Check if parent is a CLI process
    try:
        parent_result = subprocess.run(
            ["ps", "-p", str(ppid), "-o", "command="],
            capture_output=True,
            text=True,
            check=True
        )
        if "idflow worker start" in parent_result.stdout:
            # This is a child of CLI, determine if task-mgr or worker
            # Task-manager typically has lower memory usage and is usually the first child
            # We can also check the process start time to determine order
            try:
                # Get process start time to determine order
                start_time_result = subprocess.run(
                    ["ps", "-o", "lstart=", "-p", str(current_pid)],
                    capture_output=True,
                    text=True,
                    check=True
                )
                start_time = start_time_result.stdout.strip()

                # Get all children of the parent to determine order
                children_result = subprocess.run(
                    ["ps", "--ppid", str(ppid), "-o", "pid,lstart="],
                    capture_output=True,
                    text=True,
                    check=True
                )
                children_lines = children_result.stdout.strip().split('\n')
                children_pids = []
                for line in children_lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            children_pids.append(int(parts[0]))

                # Sort by PID to get creation order
                children_pids.sort()

                # The first child is typically the task-manager
                if current_pid == children_pids[0]:
                    return "task-mgr"
                else:
                    return "worker"
            except (subprocess.CalledProcessError, ValueError, IndexError):
                # Fallback to memory usage
                if memory_usage < 1.0:  # Less than 1% memory
                    return "task-mgr"
                else:
                    return "worker"
        else:
            return "unknown"
    except (subprocess.CalledProcessError, ValueError):
        return "unknown"

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
                # Extract worker name and process type from command line
                worker_name = "unknown"
                process_type = "unknown"

                if "--worker" in line or " -w " in line:
                    # Extract worker name from --worker or -w argument
                    import re
                    match = re.search(r'(?:--worker|-w)\s+(\w+)', line)
                    if match:
                        worker_name = match.group(1)
                elif "--all" in line or " -a " in line or line.strip().endswith(" -a"):
                    worker_name = "all"

                # Determine process type based on process hierarchy and command line
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        current_pid = int(parts[1])

                        # Get parent process ID
                        try:
                            ppid_result = subprocess.run(
                                ["ps", "-o", "ppid=", "-p", str(current_pid)],
                                capture_output=True,
                                text=True,
                                check=True
                            )
                            ppid = int(ppid_result.stdout.strip())
                        except (ValueError, subprocess.CalledProcessError):
                            ppid = None

                        # Determine process type based on hierarchy and command line
                        if full_command:
                            # For full command output, we can see the actual command
                            if "conductor.client.automator.task_handler" in line or "TaskHandler" in line:
                                process_type = "task-mgr"
                            elif "conductor.client.automator.task_runner" in line or "TaskRunner" in line:
                                process_type = "worker"
                            elif "idflow worker start" in line:
                                process_type = "cli"
                            else:
                                process_type = "unknown"
                        else:
                            # For non-full output, use hierarchy-based detection
                            # CLI is typically the root process (no other idflow worker start as parent)
                            # Task-manager is a child of CLI
                            # Worker is a child of task-manager or CLI

                            # Check if this process has other idflow worker start processes as children
                            has_worker_children = False
                            try:
                                children_result = subprocess.run(
                                    ["ps", "--ppid", str(current_pid), "-o", "pid="],
                                    capture_output=True,
                                    text=True,
                                    check=True
                                )
                                child_pids = children_result.stdout.strip().split('\n')
                                child_pids = [pid.strip() for pid in child_pids if pid.strip()]

                                # Check if any children are idflow worker processes
                                for child_pid in child_pids:
                                    if child_pid:
                                        child_result = subprocess.run(
                                            ["ps", "-p", child_pid, "-o", "command="],
                                            capture_output=True,
                                            text=True,
                                            check=True
                                        )
                                        if "idflow worker start" in child_result.stdout:
                                            has_worker_children = True
                                            break
                            except (subprocess.CalledProcessError, ValueError):
                                pass

                            if has_worker_children:
                                process_type = "cli"
                            else:
                                # Use the helper function to determine process type
                                try:
                                    memory_usage = float(parts[3])
                                    process_type = determine_process_type(current_pid, ppid, memory_usage)
                                except (ValueError, IndexError):
                                    process_type = "unknown"
                    except (ValueError, IndexError):
                        process_type = "unknown"
                else:
                    process_type = "unknown"

                # Format worker name and process type
                worker_display = f"{worker_name} ({process_type})"[:25].ljust(25)

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

                # Extract worker name and process type from command line
                worker_name = "unknown"
                process_type = "unknown"

                if "--worker" in line or " -w " in line:
                    import re
                    match = re.search(r'(?:--worker|-w)\s+(\w+)', line)
                    if match:
                        worker_name = match.group(1)
                elif "--all" in line or " -a " in line or line.strip().endswith(" -a"):
                    worker_name = "all"

                # Determine process type based on process hierarchy and command line
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        current_pid = int(parts[1])

                        # Get parent process ID
                        try:
                            ppid_result = subprocess.run(
                                ["ps", "-o", "ppid=", "-p", str(current_pid)],
                                capture_output=True,
                                text=True,
                                check=True
                            )
                            ppid = int(ppid_result.stdout.strip())
                        except (ValueError, subprocess.CalledProcessError):
                            ppid = None

                        # Check if this process has other idflow worker start processes as children
                        has_worker_children = False
                        try:
                            children_result = subprocess.run(
                                ["ps", "--ppid", str(current_pid), "-o", "pid="],
                                capture_output=True,
                                text=True,
                                check=True
                            )
                            child_pids = children_result.stdout.strip().split('\n')
                            child_pids = [pid.strip() for pid in child_pids if pid.strip()]

                            # Check if any children are idflow worker processes
                            for child_pid in child_pids:
                                if child_pid:
                                    child_result = subprocess.run(
                                        ["ps", "-p", child_pid, "-o", "command="],
                                        capture_output=True,
                                        text=True,
                                        check=True
                                    )
                                    if "idflow worker start" in child_result.stdout:
                                        has_worker_children = True
                                        break
                        except (subprocess.CalledProcessError, ValueError):
                            pass

                        if has_worker_children:
                            process_type = "cli"
                        else:
                            # Use the helper function to determine process type
                            try:
                                memory_usage = float(parts[3])
                                process_type = determine_process_type(current_pid, ppid, memory_usage)
                            except (ValueError, IndexError):
                                process_type = "unknown"
                    except (ValueError, IndexError):
                        process_type = "unknown"
                else:
                    process_type = "unknown"

                # If no pattern provided, match all workers
                # If pattern provided, check if it's contained in worker name
                if pattern is None or pattern.lower() in worker_name.lower():
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            pid = int(parts[1])
                            matching_pids.append((pid, line, worker_name, process_type))
                        except ValueError:
                            continue

        if not matching_pids:
            pattern_desc = "any pattern" if pattern is None else f"pattern '{pattern}'"
            typer.echo(f"No worker processes found matching {pattern_desc}")
            return

        pattern_desc = "all workers" if pattern is None else f"pattern '{pattern}'"
        typer.echo(f"Found {len(matching_pids)} worker processes matching {pattern_desc}:")
        typer.echo("WORKER                    USER       PID  %CPU %MEM    VSZ   RSS TTY      STAT START   TIME")

        for pid, line, worker_name, process_type in matching_pids:
            # Format worker name and process type to fit in 25 characters
            worker_display = f"{worker_name} ({process_type})"[:25].ljust(25)

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
        for pid, line, worker_name, process_type in matching_pids:
            try:
                signal_to_use = signal.SIGKILL if kill else signal.SIGTERM
                os.kill(pid, signal_to_use)
                killed_count += 1
                typer.echo(f"Killed PID {pid} ({worker_name} - {process_type}) with {signal_name}")
            except ProcessLookupError:
                typer.echo(f"Process {pid} ({worker_name} - {process_type}) already terminated")
            except PermissionError:
                typer.echo(f"Permission denied to kill PID {pid} ({worker_name} - {process_type})")
            except Exception as e:
                typer.echo(f"Error killing PID {pid} ({worker_name} - {process_type}): {e}")

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

    # Global variable to track if shutdown is in progress
    shutdown_in_progress = False
    worker_pids = []
    current_pid = os.getpid()

    def signal_handler(signum, frame):
        nonlocal shutdown_in_progress
        if shutdown_in_progress:
            # Force exit if already shutting down
            print("\nForce shutdown...")
            sys.exit(1)

        shutdown_in_progress = True
        print("\nShutting down workers...")

        try:
            # Try to stop processes gracefully
            task_handler.stop_processes()
        except Exception as e:
            print(f"Error during graceful shutdown: {e}")

        # Also kill any remaining worker processes directly
        # Only kill processes that are children of the current process
        try:
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True,
                check=True
            )

            lines = result.stdout.split('\n')
            killed_count = 0
            for line in lines:
                if ('worker start' in line and
                    'worker ps' not in line and
                    'worker killall' not in line and
                    'worker list' not in line and
                    not line.startswith('USER')):
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            pid = int(parts[1])
                            # Check if this process is a child of the current process
                            # by checking if it's in our worker_pids list or if it's a direct child
                            if pid in worker_pids or is_child_process(pid, current_pid):
                                os.kill(pid, signal.SIGTERM)
                                killed_count += 1
                        except (ValueError, ProcessLookupError, PermissionError):
                            pass

            if killed_count > 0:
                print(f"Killed {killed_count} worker processes")
        except Exception as e:
            print(f"Error killing remaining processes: {e}")

        print("Workers stopped.")
        sys.exit(0)

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        typer.echo("Workers started. Press Ctrl+C to stop.")
        task_handler.start_processes()

        # Track worker PIDs after starting
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            check=True
        )

        lines = result.stdout.split('\n')
        for line in lines:
            if ('worker start' in line and
                'worker ps' not in line and
                'worker killall' not in line and
                'worker list' not in line and
                not line.startswith('USER')):
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        pid = int(parts[1])
                        # Only add if it's a child of current process
                        if is_child_process(pid, current_pid):
                            worker_pids.append(pid)
                    except (ValueError, ProcessLookupError):
                        pass

        # Keep the main thread alive and wait for workers
        # Use a more robust approach to handle interrupts
        while not shutdown_in_progress:
            time.sleep(0.1)

    except Exception as e:
        if not shutdown_in_progress:
            typer.echo(f"Error starting workers: {e}")
            try:
                task_handler.stop_processes()
            except Exception as stop_error:
                typer.echo(f"Error during cleanup: {stop_error}")
            sys.exit(1)
    finally:
        # Ensure cleanup happens even if something goes wrong
        if not shutdown_in_progress:
            try:
                task_handler.stop_processes()
            except Exception:
                pass


if __name__ == "__main__":
    app()
