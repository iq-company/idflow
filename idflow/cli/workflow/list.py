from __future__ import annotations
import typer
from idflow.core.workflow_manager import get_workflow_manager


def list_workflows(
    local: bool = typer.Option(False, "--local", help="Show only local workflow files (Default)"),
    all: bool = typer.Option(False, "--all", help="Show both local and remote workflows"),
    remote: bool = typer.Option(False, "--remote", help="Show only workflows that exist remote but not locally"),
    versions: bool = typer.Option(True, "--versions/--no-versions", help="Show version information for workflows")
):
    """List workflows (local files and/or remote)."""
    workflow_manager = get_workflow_manager()

    # Handle remote-only mode
    if remote:
        _show_remote_only(workflow_manager, versions)
        return

    # Determine what to show
    if local:
        show_local = True
        show_remote = False
    elif all:
        show_local = True
        show_remote = True
    elif remote:
        show_local = False
        show_remote = True
    else:
        # Default: show local only
        show_local = True
        show_remote = False

    if show_local:
        typer.echo("Local workflow files:")
        workflows = workflow_manager.discover_workflows()

        if not workflows:
            typer.echo("  No workflow files found")
        else:
            for workflow_file in workflows:
                workflow_def = workflow_manager.load_workflow_definition(workflow_file)
                if workflow_def:
                    name = workflow_def.get('name', 'unknown')
                    version = workflow_def.get('version', 1)
                    typer.echo(f"  {name} v{version}")
                else:
                    typer.echo(f"  {workflow_file.name} (invalid)")

        if show_remote:
            typer.echo()

    if show_remote:
        typer.echo("Remote workflows:")
        remote_workflows = workflow_manager.list_workflows_remote()

        if not remote_workflows:
            typer.echo("  No remote workflows found ")
        else:
            # Group by name and show versions
            workflow_versions = {}
            for wf in remote_workflows:
                name = wf.get('name')
                version = wf.get('version', 1)
                if name:
                    if name not in workflow_versions:
                        workflow_versions[name] = []
                    workflow_versions[name].append(version)

            for name in sorted(workflow_versions.keys()):
                versions_list = sorted(workflow_versions[name])
                version_str = ', '.join(f'v{v}' for v in versions_list)
                typer.echo(f"  {name} ({version_str})")


def _show_remote_only(workflow_manager, show_versions: bool):
    """Show only workflows that exist remote but not locally."""
    sync_status = workflow_manager.get_workflow_sync_status()
    only_remote = sync_status['only_remote']
    remote_versions = sync_status['remote_versions']

    if only_remote:
        typer.echo("Remote workflows:")
        for workflow_name in sorted(only_remote):
            if show_versions and workflow_name in remote_versions:
                versions = sorted(remote_versions[workflow_name])
                version_str = ', '.join(f'v{v}' for v in versions)
                typer.echo(f"  {workflow_name} ({version_str})")
            else:
                typer.echo(f"  {workflow_name}")
    else:
        typer.echo("All remote workflows are also available locally.")
