from __future__ import annotations
from typing import Dict, Any, Optional, List
import os


class ConductorClient:
    """Basic conductor client for workflow management."""

    def __init__(self, server_url: Optional[str] = None, api_key: Optional[str] = None):
        from .config import config

        # Server URL only from config (no environment override)
        if server_url:
            self.server_url = server_url
        else:
            self.server_url = config.conductor_server_url

        # API key from environment variable (name configurable in config)
        if api_key:
            self.api_key = api_key
        else:
            api_key_env_var = config.conductor_api_key_env_var
            self.api_key = os.getenv(api_key_env_var)
        self._client = None

    def _get_client(self):
        """Lazy initialization of the actual conductor client."""
        if self._client is None:
            try:
                from conductor.client.workflow_client import WorkflowClient
                from conductor.client.configuration.configuration import Configuration

                config = Configuration()
                config.host = self.server_url
                if self.api_key:
                    config.api_key["X-Authorization"] = self.api_key

                self._client = WorkflowClient(configuration=config)
            except ImportError:
                raise ImportError("conductor-python package not installed")
        return self._client

    def start_workflow(self, name: str, version: int, input: Dict[str, Any]) -> str:
        """Start a workflow and return the workflow ID."""
        client = self._get_client()

        # Start the workflow
        workflow_id = client.start_workflow(
            name=name,
            version=version,
            input=input
        )

        return workflow_id

    def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow execution details."""
        client = self._get_client()

        execution = client.get_workflow(workflow_id)
        return execution

    def terminate_workflow(self, workflow_id: str, reason: str = "Terminated by user") -> None:
        """Terminate a workflow execution."""
        client = self._get_client()

        client.terminate_workflow(workflow_id, reason)

    def get_workflows_by_correlation_id(self, correlation_id: str, workflow_name: str = None) -> List[Dict[str, Any]]:
        """Get workflows by correlation ID."""
        client = self._get_client()

        # Use the correct conductor API method
        workflows = client.get_by_correlation_ids(
            workflow_name=workflow_name,
            correlation_ids=[correlation_id],
            include_completed=False,
            include_tasks=False
        )

        return workflows


# Global instance
_conductor_client: Optional[ConductorClient] = None

def get_conductor_client() -> ConductorClient:
    """Get the global conductor client instance."""
    global _conductor_client
    if _conductor_client is None:
        _conductor_client = ConductorClient()
    return _conductor_client
