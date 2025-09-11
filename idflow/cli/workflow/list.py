from __future__ import annotations
import typer
from idflow.core.workflow_manager import get_workflow_manager


def list_workflows(
    local: bool = typer.Option(False, "--local", help="Show only local workflow files"),
    conductor: bool = typer.Option(False, "--conductor", help="Show only workflows in Conductor"),
    all: bool = typer.Option(False, "--all", help="Show both local and Conductor workflows")
):
    """List workflows (local files and/or Conductor)."""
    workflow_manager = get_workflow_manager()

    if not (local or conductor or all):
        # Default: show both
        local = True
        conductor = True

    if local or all:
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

        if conductor or all:
            typer.echo()

    if conductor or all:
        typer.echo("Workflows in Conductor:")
        remote_workflows = workflow_manager.list_workflows_remote()

        if not remote_workflows:
            typer.echo("  No workflows found in Conductor")
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
                versions = sorted(workflow_versions[name])
                version_str = ', '.join(f'v{v}' for v in versions)
                typer.echo(f"  {name} ({version_str})")
