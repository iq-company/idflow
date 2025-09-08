from __future__ import annotations
from typing import Dict, Any, Optional, List
import requests
import os


def _get_conductor_config():
    """Get Conductor configuration from config module."""
    from .config import config

    return {
        'host': config.conductor_server_url,
        'base_path': '/api',
        'api_key': os.getenv(config.conductor_api_key_env_var) if hasattr(config, 'conductor_api_key_env_var') else None
    }


def _get_base_url():
    """Get the base URL for Conductor API calls."""
    config = _get_conductor_config()
    return f"{config['host']}{config['base_path']}"


def _get_headers():
    """Get headers for Conductor API calls."""
    config = _get_conductor_config()
    headers = {"Content-Type": "application/json"}

    if config['api_key']:
        headers["Authorization"] = f"Bearer {config['api_key']}"

    return headers


def start_workflow(workflow_name: str, input_data: Dict[str, Any]) -> str:
    """Start a workflow and return the workflow ID."""
    try:
        base_url = _get_base_url()
        headers = _get_headers()

        response = requests.post(
            f"{base_url}/workflow/{workflow_name}",
            json=input_data,
            headers=headers
        )

        if response.status_code == 200:
            return response.text.strip('"')
        else:
            raise Exception(f"Failed to start workflow: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Failed to start workflow {workflow_name}: {e}")
        raise


def get_workflow_status(workflow_id: str) -> Dict[str, Any]:
    """Get workflow execution status."""
    try:
        base_url = _get_base_url()
        headers = _get_headers()

        response = requests.get(f"{base_url}/workflow/{workflow_id}", headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Failed to get workflow status {workflow_id}: {e}")
        return None


def upload_workflow(workflow_definition: Dict[str, Any]) -> bool:
    """Upload a workflow definition to Conductor."""
    try:
        base_url = _get_base_url()
        headers = _get_headers()

        workflow_name = workflow_definition.get('name', 'unknown')
        workflow_version = workflow_definition.get('version', 1)

        # First try to delete existing workflow
        try:
            requests.delete(
                f"{base_url}/metadata/workflow/{workflow_name}/{workflow_version}",
                headers=headers
            )
            # Ignore delete errors - workflow might not exist
        except:
            pass

        # Upload new workflow
        response = requests.post(
            f"{base_url}/metadata/workflow",
            json=workflow_definition,
            headers=headers
        )

        if response.status_code != 200:
            print(f"Workflow upload failed for {workflow_name}: {response.status_code} - {response.text}")
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Failed to upload workflow {workflow_definition.get('name', 'unknown')}: {e}")
        return False


def search_workflows(size: int = 10) -> List[Dict[str, Any]]:
    """Search for workflows."""
    try:
        base_url = _get_base_url()
        headers = _get_headers()

        response = requests.get(f"{base_url}/workflow/search?size={size}", headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get('results', [])
    except Exception as e:
        print(f"Failed to search workflows: {e}")
        return []
