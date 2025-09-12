from __future__ import annotations
import typer
from typing import Optional, List, Dict, Any
from idflow.core.workflow_manager import get_workflow_manager
from idflow.core.conductor_client import _get_base_url, _get_headers
import requests


def _check_workflow_runs(workflow_name: str, version: Optional[int] = None) -> List[Dict[str, Any]]:
    """Check if there are running or pending workflow runs for a given workflow."""
    try:
        base_url = _get_base_url()
        headers = _get_headers()

        # Search for running workflows
        params = {
            'status': 'RUNNING,PENDING',
            'size': 1000  # Large number to get all results
        }

        if version:
            params['workflowType'] = workflow_name
            params['version'] = version
        else:
            params['workflowType'] = workflow_name

        response = requests.get(f"{base_url}/workflow/search", params=params, headers=headers)

        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])

            # Filter out completed workflows as the API might return them despite the status filter
            active_runs = []
            for run in results:
                status = run.get('status', '').upper()
                if status in ['RUNNING', 'PENDING', 'IN_PROGRESS', 'SCHEDULED']:
                    active_runs.append(run)

            return active_runs
        else:
            typer.echo(f"Warning: Could not check workflow runs for {workflow_name}: {response.status_code}")
            return []
    except Exception as e:
        typer.echo(f"Warning: Could not check workflow runs for {workflow_name}: {e}")
        return []


def _delete_workflow_version(workflow_name: str, version: int) -> bool:
    """Delete a specific workflow version from remote."""
    try:
        base_url = _get_base_url()
        headers = _get_headers()

        response = requests.delete(
            f"{base_url}/metadata/workflow/{workflow_name}/{version}",
            headers=headers
        )

        if response.status_code == 200:
            return True
        else:
            typer.echo(f"Failed to delete {workflow_name} v{version}: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        typer.echo(f"Failed to delete {workflow_name} v{version}: {e}")
        return False


def prune_workflows(
    workflow: Optional[str] = typer.Option(None, "--workflow", "-w", help="Specific workflow name to prune"),
    version: Optional[int] = typer.Option(None, "--version", "-v", help="Specific version to prune"),
    force: bool = typer.Option(False, "--force", help="Force deletion even if workflows are running"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be deleted without actually deleting")
):
    """Prune (delete) workflows and versions from remote that no longer exist locally."""
    workflow_manager = get_workflow_manager()

    if dry_run:
        typer.echo("DRY RUN MODE - No workflows will be deleted")
        typer.echo("=" * 50)

    # Get sync status to determine what to prune
    sync_status = workflow_manager.get_workflow_sync_status()
    remote_versions = sync_status['remote_versions']
    only_remote = sync_status['only_remote']

    workflows_to_check = []

    if workflow:
        # Specific workflow requested
        if workflow not in remote_versions:
            typer.echo(f"Workflow '{workflow}' not found remote")
            raise typer.Exit(1)

        if version:
            # Specific version requested
            if version not in remote_versions[workflow]:
                typer.echo(f"Version {version} of workflow '{workflow}' not found remote")
                raise typer.Exit(1)
            workflows_to_check = [(workflow, version)]
        else:
            # All versions of specific workflow
            workflows_to_check = [(workflow, v) for v in remote_versions[workflow]]
    else:
        # Default: Only workflows that exist remote but not locally
        for wf_name in only_remote:
            if wf_name in remote_versions:
                for v in remote_versions[wf_name]:
                    workflows_to_check.append((wf_name, v))

    if not workflows_to_check:
        typer.echo("No workflows to prune.")
        return

    typer.echo(f"Checking {len(workflows_to_check)} workflow versions for active runs...")
    typer.echo()

    workflows_to_delete = []
    workflows_with_runs = []

    for workflow_name, workflow_version in workflows_to_check:
        # Check for running workflows
        running_workflows = _check_workflow_runs(workflow_name, workflow_version)

        if running_workflows:
            workflows_with_runs.append((workflow_name, workflow_version, running_workflows))
            if force:
                typer.echo(f"⚠️  {workflow_name} v{workflow_version} has {len(running_workflows)} active runs - will delete anyway (--force)")
                workflows_to_delete.append((workflow_name, workflow_version))
            else:
                typer.echo(f"⚠️  {workflow_name} v{workflow_version} has {len(running_workflows)} active runs - skipping")
        else:
            workflows_to_delete.append((workflow_name, workflow_version))
            typer.echo(f"✓ {workflow_name} v{workflow_version} - safe to delete")

    typer.echo()

    if workflows_with_runs and not force:
        typer.echo("Some workflows have active runs and were skipped.")
        typer.echo("Use --force to delete them anyway, or wait for the runs to complete.")
        typer.echo()
        typer.echo("Workflows with active runs:")
        for workflow_name, workflow_version, runs in workflows_with_runs:
            typer.echo(f"  {workflow_name} v{workflow_version} ({len(runs)} runs)")
            for run in runs[:3]:  # Show first 3 runs
                run_id = run.get('workflowId', 'unknown')
                status = run.get('status', 'unknown')
                typer.echo(f"    - {run_id} ({status})")
            if len(runs) > 3:
                typer.echo(f"    ... and {len(runs) - 3} more")
        return

    if not workflows_to_delete:
        typer.echo("No workflows to delete.")
        return

    # Show what will be deleted
    typer.echo(f"Workflows to be deleted ({len(workflows_to_delete)}):")
    for workflow_name, workflow_version in workflows_to_delete:
        typer.echo(f"  {workflow_name} v{workflow_version}")

    if dry_run:
        typer.echo("\nDry run complete - no workflows were deleted.")
        return

    # Confirm deletion
    if not typer.confirm(f"\nDelete {len(workflows_to_delete)} workflow versions?"):
        typer.echo("Deletion cancelled.")
        return

    # Delete workflows
    typer.echo("\nDeleting workflows...")
    deleted_count = 0
    failed_count = 0

    for workflow_name, workflow_version in workflows_to_delete:
        if _delete_workflow_version(workflow_name, workflow_version):
            typer.echo(f"✓ Deleted {workflow_name} v{workflow_version}")
            deleted_count += 1
        else:
            typer.echo(f"✗ Failed to delete {workflow_name} v{workflow_version}")
            failed_count += 1

    typer.echo(f"\nSummary: {deleted_count} deleted, {failed_count} failed")
