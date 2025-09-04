from __future__ import annotations
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class WorkflowConfig(BaseModel):
    """Configuration for a workflow within a stage."""
    name: str
    version: Optional[int] = None
    when: Optional[str] = None
    correlation_id: Optional[str] = Field(None, alias="correlationId")
    inputs: Optional[Dict[str, Any]] = None


class FilePresenceRequirement(BaseModel):
    """File presence requirement configuration."""
    key: str
    count: int = 1
    count_operator: str = ">="


class StageRequirement(BaseModel):
    """Stage requirement configuration."""
    status: str


class Requirements(BaseModel):
    """Requirements configuration for a stage."""
    file_presence: Optional[FilePresenceRequirement] = None
    stages: Optional[Dict[str, StageRequirement]] = None


class StageDefinition(BaseModel):
    """A stage definition loaded from YAML."""
    name: str
    active: bool = True
    workflows: List[WorkflowConfig] = Field(default_factory=list)
    requirements: Optional[Requirements] = None
    multiple_callable: bool = False

    def check_requirements(self, doc) -> bool:
        """Check if the requirements for this stage are met for the given document."""
        if not self.requirements:
            return True

        # Check file presence requirements
        if self.requirements.file_presence:
            fp_req = self.requirements.file_presence
            matching_files = [f for f in doc.file_refs if f.key == fp_req.key]

            if fp_req.count_operator == ">=":
                if len(matching_files) < fp_req.count:
                    return False
            elif fp_req.count_operator == "==":
                if len(matching_files) != fp_req.count:
                    return False
            elif fp_req.count_operator == ">":
                if len(matching_files) <= fp_req.count:
                    return False
            elif fp_req.count_operator == "<=":
                if len(matching_files) > fp_req.count:
                    return False
            elif fp_req.count_operator == "<":
                if len(matching_files) >= fp_req.count:
                    return False
            elif fp_req.count_operator == "!=":
                if len(matching_files) == fp_req.count:
                    return False

        # Check stage requirements
        if self.requirements.stages:
            for stage_name, stage_req in self.requirements.stages.items():
                matching_stages = doc.get_stages(stage_name)
                if not matching_stages:
                    return False

                # Check if any stage with this name has the required status
                has_required_status = any(
                    stage.status == stage_req.status
                    for stage in matching_stages
                )
                if not has_required_status:
                    return False

        return True

    def trigger_workflows(self, doc, stage_counter: int = 1, conductor_client=None) -> List[str]:
        """Trigger the configured workflows for this stage."""
        if not conductor_client:
            from .conductor_client import get_conductor_client
            conductor_client = get_conductor_client()

        triggered_workflows = []

        for workflow_config in self.workflows:
            # Create unique correlation ID with stage counter
            correlation_id = f"{doc.id}-{self.name}-{stage_counter}"

            # Check if workflow is already running with this correlation ID
            try:
                existing_workflows = conductor_client.get_workflows_by_correlation_id(
                    correlation_id,
                    workflow_name=workflow_config.name
                )
                if existing_workflows:
                    continue
            except Exception:
                # If check fails, continue with starting the workflow
                pass

            # Start the trigger workflow with this stage's configuration
            trigger_input = {
                "docId": doc.id,
                "rule": workflow_config.when or "true",
                "inputTemplate": workflow_config.inputs or {},
                "correlationId": correlation_id
            }

            # Start the trigger workflow
            workflow_id = conductor_client.start_workflow(
                name= workflow_config.name,
                version=workflow_config.version or 1,
                input=trigger_input
            )
            triggered_workflows.append(workflow_id)

        return triggered_workflows


class StageDefinitions:
    """Manager for all stage definitions loaded from YAML files."""

    def __init__(self, stages_dir: Optional[Path] = None):
        self.stages_dir = stages_dir or Path("idflow/stages")
        self._definitions: Dict[str, StageDefinition] = {}
        self._load_definitions()

    def _load_definitions(self) -> None:
        """Load all stage definitions from YAML files."""
        if not self.stages_dir.exists():
            return

        for yaml_file in self.stages_dir.glob("*.yml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)

                if not data or not isinstance(data, dict):
                    continue

                # Create stage definition
                stage_def = StageDefinition(**data)

                # Only include active stages
                if stage_def.active:
                    self._definitions[stage_def.name] = stage_def

            except Exception as e:
                print(f"Warning: Failed to load stage definition from {yaml_file}: {e}")
                continue

    def get_definition(self, stage_name: str) -> Optional[StageDefinition]:
        """Get a stage definition by name."""
        return self._definitions.get(stage_name)

    def list_definitions(self) -> List[str]:
        """List all available stage definition names."""
        return list(self._definitions.keys())

    def reload(self) -> None:
        """Reload all stage definitions from files."""
        self._definitions.clear()
        self._load_definitions()


# Global instance
_stage_definitions: Optional[StageDefinitions] = None

def get_stage_definitions() -> StageDefinitions:
    """Get the global stage definitions instance."""
    global _stage_definitions
    if _stage_definitions is None:
        _stage_definitions = StageDefinitions()
    return _stage_definitions
