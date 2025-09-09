from __future__ import annotations
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from .conductor_client import upload_workflow

# TODO: upload_tasks wird nicht mehr benötigt oder?
# TODO: check ob die workflow updates gut gemacht sind. Eigentlich sollen keine Löschungen (für ein replace) erfolgen (sondern erhöhte versionsnr); bzw. wenn dann, nur über eine force definition
# TODO: erstellung eigener task zum dedizierten workflow delete

class WorkflowManager:
    """Manages workflow and task definitions for Conductor."""

    def __init__(self, workflows_dir: Optional[Path] = None, tasks_dir: Optional[Path] = None):
        self.workflows_dir = workflows_dir or Path("idflow/workflows")
        self.tasks_dir = tasks_dir or Path("idflow/tasks")
        self._last_upload_results = None

    def discover_workflows(self) -> List[Path]:
        """Discover all workflow JSON files."""
        workflows = []
        for workflow_file in self.workflows_dir.rglob("*.json"):
            if workflow_file.name != "event_handlers.json":  # Skip event handlers
                workflows.append(workflow_file)
        return workflows

    def find_workflow_file(self, workflow_name: str) -> Optional[Path]:
        """Find workflow file by name."""
        for workflow_file in self.discover_workflows():
            workflow_def = self.load_workflow_definition(workflow_file)
            if workflow_def and workflow_def.get('name') == workflow_name:
                return workflow_file
        return None

    def discover_tasks(self) -> List[Path]:
        """Discover all task Python files."""
        tasks = []
        for task_file in self.tasks_dir.rglob("*.py"):
            if task_file.name != "__init__.py":
                tasks.append(task_file)
        return tasks

    def load_workflow_definition(self, workflow_file: Path) -> Optional[Dict[str, Any]]:
        """Load workflow definition from JSON file."""
        try:
            with open(workflow_file, 'r', encoding='utf-8') as f:
                workflow_def = json.load(f)

            # Add required fields if missing
            if "ownerEmail" not in workflow_def:
                workflow_def["ownerEmail"] = "idflow@example.com"

            return workflow_def
        except Exception as e:
            print(f"Failed to load workflow from {workflow_file}: {e}")
            return None

    def load_task_definition(self, task_file: Path) -> Optional[Dict[str, Any]]:
        """Extract task definition from Python file."""
        try:
            with open(task_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Look for @worker_task decorator
            if "@worker_task" not in content:
                return None

            # Extract task name from decorator
            import re
            match = re.search(r"@worker_task\(task_definition_name='([^']+)'\)", content)
            if not match:
                return None

            task_name = match.group(1)

            # Create basic task definition
            return {
                "name": task_name,
                "description": f"Task from {task_file.name}",
                "retryCount": 3,
                "timeoutSeconds": 600,  # Increased to be > responseTimeoutSeconds
                "timeoutPolicy": "TIME_OUT_WF",
                "retryLogic": "FIXED",
                "retryDelaySeconds": 60,
                "responseTimeoutSeconds": 300,  # Reduced to be < timeoutSeconds
                "concurrentExecLimit": 100,
                "rateLimitFrequencyInSeconds": 1,
                "rateLimitPerFrequency": 50,
                "ownerEmail": "idflow@example.com"  # Add required ownerEmail
            }
        except Exception as e:
            print(f"Failed to load task from {task_file}: {e}")
            return None


    def needs_upload(self, name: str, file_path: Path, is_workflow: bool = True) -> bool:
        """Check if workflow needs to be uploaded based on version comparison."""
        if not is_workflow:
            return True

        # For workflows, check if the exact version exists in Conductor
        return not self._workflow_exists_in_conductor(name, file_path)

    def _workflow_exists_in_conductor(self, name: str, file_path: Path) -> bool:
        """Check if workflow exists in Conductor with the correct version."""
        try:
            import requests
            from .conductor_client import _get_base_url, _get_headers

            # Load workflow definition to get version
            workflow_def = self.load_workflow_definition(file_path)
            if not workflow_def:
                return False

            expected_version = workflow_def.get('version', 1)

            # Check if workflow exists in Conductor metadata
            base_url = _get_base_url()
            headers = _get_headers()

            response = requests.get(
                f"{base_url}/metadata/workflow",
                headers=headers
            )

            if response.status_code == 200:
                existing_workflows = response.json()
                for workflow in existing_workflows:
                    if (workflow.get('name') == name and
                        workflow.get('version', 1) == expected_version):
                        return True

            return False
        except Exception as e:
            # If check fails, assume upload is needed
            print(f"Warning: Could not check workflow {name} in Conductor: {e}")
            return False

    def upload_workflows(self, force: bool = False) -> Dict[str, bool]:
        """Upload all workflows to Conductor."""
        results = {}
        uploaded_workflows = []
        skipped_workflows = []
        workflows = self.discover_workflows()

        print(f"Found {len(workflows)} workflow files")

        for workflow_file in workflows:
            workflow_def = self.load_workflow_definition(workflow_file)
            if not workflow_def:
                results[workflow_file.name] = False
                continue

            workflow_name = workflow_def.get('name')
            if not workflow_name:
                print(f"No name found in workflow {workflow_file}")
                results[workflow_file.name] = False
                continue

            # Check if upload is needed
            if not force and not self.needs_upload(workflow_name, workflow_file, is_workflow=True):
                print(f"Workflow {workflow_name} is up to date (already exists in Conductor)")
                results[workflow_name] = True
                skipped_workflows.append(workflow_name)
                continue

            # Upload workflow
            success = upload_workflow(workflow_def)
            results[workflow_name] = success

            if success:
                print(f"✓ Uploaded workflow: {workflow_name}")
                uploaded_workflows.append(workflow_name)
            else:
                print(f"✗ Failed to upload workflow: {workflow_name}")

        # Store results for summary
        self._last_upload_results = {
            'uploaded': uploaded_workflows,
            'skipped': skipped_workflows,
            'total': len(workflows)
        }

        return results

    def upload_single_workflow(self, workflow_name: str, force: bool = False) -> Dict[str, bool]:
        """Upload a single workflow by name."""
        results = {}
        uploaded_workflows = []
        skipped_workflows = []

        # Find the workflow file
        workflows = self.discover_workflows()
        workflow_file = None

        for wf_file in workflows:
            workflow_def = self.load_workflow_definition(wf_file)
            if workflow_def and workflow_def.get('name') == workflow_name:
                workflow_file = wf_file
                break

        if not workflow_file:
            print(f"Workflow '{workflow_name}' not found in local files")
            return {workflow_name: False}

        # Load workflow definition
        workflow_def = self.load_workflow_definition(workflow_file)
        if not workflow_def:
            print(f"Failed to load workflow definition from {workflow_file}")
            return {workflow_name: False}

        # Check if upload is needed
        if not force and not self.needs_upload(workflow_name, workflow_file, is_workflow=True):
            print(f"Workflow {workflow_name} is up to date (already exists in Conductor)")
            results[workflow_name] = True
            skipped_workflows.append(workflow_name)
        else:
            # Upload workflow
            from .conductor_client import upload_workflow
            success = upload_workflow(workflow_def)
            results[workflow_name] = success

            if success:
                print(f"✓ Uploaded workflow: {workflow_name}")
                uploaded_workflows.append(workflow_name)
            else:
                print(f"✗ Failed to upload workflow: {workflow_name}")

        # Store results for summary
        self._last_upload_results = {
            'uploaded': uploaded_workflows,
            'skipped': skipped_workflows,
            'total': 1
        }

        return results

    def upload_tasks(self, force: bool = False) -> Dict[str, bool]:
        """Upload all task definitions to Conductor."""
        results = {}
        tasks = self.discover_tasks()

        print(f"Found {len(tasks)} task files")

        for task_file in tasks:
            task_def = self.load_task_definition(task_file)
            if not task_def:
                results[task_file.name] = False
                continue

            task_name = task_def.get('name')
            if not task_name:
                print(f"No name found in task {task_file}")
                results[task_file.name] = False
                continue

            # Check if upload is needed
            if not force and not self.needs_upload(task_name, task_file, is_workflow=False):
                print(f"Task {task_name} is up to date")
                results[task_name] = True
                continue

            # Upload task
            success = self.conductor_client.upload_task_definition(task_def)
            results[task_name] = success

            if success:
                print(f"✓ Uploaded task: {task_name}")
            else:
                print(f"✗ Failed to upload task: {task_name}")

        return results

    def upload_all(self, force: bool = False) -> Dict[str, Dict[str, bool]]:
        """Upload all workflows and tasks."""
        print("Uploading workflows and tasks to Conductor...")

        workflow_results = self.upload_workflows(force)
        task_results = self.upload_tasks(force)

        return {
            "workflows": workflow_results,
            "tasks": task_results
        }

    def list_workflows(self) -> List[str]:
        """List all discovered workflow names."""
        workflows = self.discover_workflows()
        names = []

        for workflow_file in workflows:
            workflow_def = self.load_workflow_definition(workflow_file)
            if workflow_def and workflow_def.get('name'):
                names.append(workflow_def['name'])

        return names

    def list_tasks(self) -> List[str]:
        """List all discovered task names."""
        tasks = self.discover_tasks()
        names = []

        for task_file in tasks:
            task_def = self.load_task_definition(task_file)
            if task_def and task_def.get('name'):
                names.append(task_def['name'])

        return names


# Global instance
_workflow_manager: Optional[WorkflowManager] = None

def get_workflow_manager() -> WorkflowManager:
    """Get the global workflow manager instance."""
    global _workflow_manager
    if _workflow_manager is None:
        _workflow_manager = WorkflowManager()
    return _workflow_manager
