from __future__ import annotations
import yaml
from pathlib import Path
import importlib.resources as ir
from typing import Dict, List, Optional, Any, Union
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


class AttributeCheck(BaseModel):
    """
    Attribute check requirement configuration.

    Supports various operators for different types of comparisons:
    - Basic: EQ, NE, GT, LT, GTE, LTE, IS, IS_NOT
    - Pattern: CP (Contains Pattern/Glob), NP (Not Contains Pattern/Glob)
    - Regex: REGEX, NOT_REGEX

    Examples:
        - attribute: "filename", operator: "CP", value: "blog_*.md"
        - attribute: "url", operator: "REGEX", value: "^https://.*"
        - attribute: "priority", operator: "GT", value: 3
    """
    attribute: str
    operator: str  # EQ, NE, GT, LT, GTE, LTE, IS, IS_NOT, CP, NP, REGEX, NOT_REGEX
    value: Any
    case_sensitive: bool = True


class ListCheck(BaseModel):
    """List check requirement configuration."""
    attribute: str
    operator: str  # HAS, CONTAINS, INCLUDES, NOT_HAS, NOT_CONTAINS, NOT_INCLUDES
    value: Any
    case_sensitive: bool = True


class Requirements(BaseModel):
    """Requirements configuration for a stage."""
    file_presence: Optional[FilePresenceRequirement] = None
    stages: Optional[Dict[str, StageRequirement]] = None
    attribute_checks: Optional[List[AttributeCheck]] = None
    list_checks: Optional[List[ListCheck]] = None
    # New preferred key
    extras: Optional[List[str]] = None
    # optional list of additionally required task names for dynamic scheduling
    # Accept either plain strings or objects with a 'name' field for convenience
    tasks: Optional[List[Union[str, Dict[str, Any]]]] = None


class StageDefinition(BaseModel):
    """A stage definition loaded from YAML."""
    name: str
    active: bool = True
    workflows: List[WorkflowConfig] = Field(default_factory=list)
    requirements: Optional[Requirements] = None
    multiple_callable: bool = False
    # Do not evaluate/schedule this stage (design-only)
    no_eval: bool = False

    def check_requirements(self, doc) -> bool:
        """Check if the requirements for this stage are met for the given document."""
        if self.no_eval:
            return False
        if not self.requirements:
            return True

        # Check extras/feature requirements first (static, independent of document)
        feature_list = self.requirements.extras
        if feature_list:
            try:
                from .optional_deps import is_optional_dependency_installed
                for feature in feature_list:
                    if not is_optional_dependency_installed(feature):
                        return False
            except Exception:
                # If the feature check fails, consider requirements not met
                return False

        # Check file presence requirements
        if self.requirements.file_presence:
            if not self._check_file_presence_requirements(doc):
                return False

        # Check stage requirements
        if self.requirements.stages:
            if not self._check_stage_requirements(doc):
                return False

        # Check attribute requirements
        if self.requirements.attribute_checks:
            if not self._check_attribute_requirements(doc):
                return False

        # Check list requirements
        if self.requirements.list_checks:
            if not self._check_list_requirements(doc):
                return False

        return True

    def _check_file_presence_requirements(self, doc) -> bool:
        """Check file presence requirements."""
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

        return True

    def _check_stage_requirements(self, doc) -> bool:
        """Check stage requirements."""
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

    def _check_attribute_requirements(self, doc) -> bool:
        """Check attribute requirements."""
        for attr_check in self.requirements.attribute_checks:
            if not self._evaluate_attribute_check(doc, attr_check):
                return False
        return True

    def _check_list_requirements(self, doc) -> bool:
        """Check list requirements."""
        for list_check in self.requirements.list_checks:
            if not self._evaluate_list_check(doc, list_check):
                return False
        return True

    def _evaluate_attribute_check(self, doc, attr_check: AttributeCheck) -> bool:
        """Evaluate a single attribute check."""
        # Get attribute value from document
        attr_value = getattr(doc, attr_check.attribute, None)
        if attr_value is None:
            return False

        # Prepare values for comparison
        doc_value = attr_value
        check_value = attr_check.value

        # Handle case sensitivity for string comparisons
        if isinstance(doc_value, str) and isinstance(check_value, str) and not attr_check.case_sensitive:
            doc_value = doc_value.lower()
            check_value = check_value.lower()

        # Evaluate based on operator
        operator = attr_check.operator.upper()

        if operator == "EQ":
            return doc_value == check_value
        elif operator == "NE":
            return doc_value != check_value
        elif operator == "GT":
            return doc_value > check_value
        elif operator == "LT":
            return doc_value < check_value
        elif operator == "GTE":
            return doc_value >= check_value
        elif operator == "LTE":
            return doc_value <= check_value
        elif operator == "IS":
            return doc_value is check_value
        elif operator == "IS_NOT":
            return doc_value is not check_value
        elif operator == "CP":  # Contains Pattern (Glob)
            return self._glob_match(doc_value, check_value, attr_check.case_sensitive)
        elif operator == "NP":  # Not Contains Pattern (Glob)
            return not self._glob_match(doc_value, check_value, attr_check.case_sensitive)
        elif operator == "REGEX":
            return self._regex_match(doc_value, check_value, attr_check.case_sensitive)
        elif operator == "NOT_REGEX":
            return not self._regex_match(doc_value, check_value, attr_check.case_sensitive)
        else:
            raise ValueError(f"Unsupported attribute operator: {operator}")

    def _glob_match(self, text: str, pattern: str, case_sensitive: bool = True) -> bool:
        """Check if text matches glob pattern."""
        import fnmatch

        if not isinstance(text, str) or not isinstance(pattern, str):
            return False

        if not case_sensitive:
            text = text.lower()
            pattern = pattern.lower()

        return fnmatch.fnmatch(text, pattern)

    def _regex_match(self, text: str, pattern: str, case_sensitive: bool = True) -> bool:
        """Check if text matches regex pattern."""
        import re

        if not isinstance(text, str) or not isinstance(pattern, str):
            return False

        try:
            flags = 0 if case_sensitive else re.IGNORECASE
            return bool(re.search(pattern, text, flags))
        except re.error:
            # Invalid regex pattern
            return False

    def _evaluate_list_check(self, doc, list_check: ListCheck) -> bool:
        """Evaluate a single list check."""
        # Get attribute value from document
        attr_value = getattr(doc, list_check.attribute, None)
        if attr_value is None:
            return False

        # Ensure attribute value is a list
        if not isinstance(attr_value, list):
            return False

        # Prepare values for comparison
        doc_list = attr_value
        check_value = list_check.value

        # Handle case sensitivity for string comparisons
        if isinstance(check_value, str) and not list_check.case_sensitive:
            doc_list = [item.lower() if isinstance(item, str) else item for item in doc_list]
            check_value = check_value.lower()

        # Evaluate based on operator
        operator = list_check.operator.upper()

        if operator in ["HAS", "CONTAINS", "INCLUDES"]:
            return check_value in doc_list
        elif operator in ["NOT_HAS", "NOT_CONTAINS", "NOT_INCLUDES"]:
            return check_value not in doc_list
        else:
            raise ValueError(f"Unsupported list operator: {operator}")

    def trigger_workflows(self, doc, stage_counter: int = 1, conductor_client=None) -> List[str]:
        """Trigger the configured workflows for this stage."""
        from .conductor_client import start_workflow, search_workflows

        # Ensure workflows are uploaded before triggering
        self._ensure_workflows_uploaded()

        triggered_workflows = []

        # Create unique correlation ID with stage counter
        correlation_id = f"{doc.id}-{self.name}-{stage_counter}"

        # Check if stage workflow is already running with this correlation ID
        try:
            existing_workflows = search_workflows(size=100)
            running_workflows = [w for w in existing_workflows
                               if w.get('correlationId') == correlation_id
                               and w.get('workflowType') == 'stage_workflow']
            if running_workflows:
                return triggered_workflows
        except Exception:
            # If check fails, continue with starting the workflow
            pass

        # Get local workflow versions
        from .workflow_manager import get_workflow_manager
        workflow_manager = get_workflow_manager()

        workflows_with_versions = []
        for wf in self.workflows:
            # Get the local workflow version
            local_workflow_file = workflow_manager.find_workflow_file(wf.name)
            if local_workflow_file:
                local_workflow_def = workflow_manager.load_workflow_definition(local_workflow_file)
                if local_workflow_def:
                    local_version = local_workflow_def.get('version', 1)
                else:
                    local_version = 1
            else:
                local_version = 1

            workflows_with_versions.append({
                "name": wf.name,
                "version": local_version,
                "inputs": wf.inputs or {},
                "when": wf.when or "true"
            })

        # Start the stage workflow with all configured workflows
        stage_workflow_input = {
            "docId": doc.id,
            "stageName": self.name,
            "stageCounter": stage_counter,
            "workflows": workflows_with_versions,
            "correlationId": correlation_id
        }

        # Start the stage workflow
        workflow_id = start_workflow(
            workflow_name="stage_workflow",
            input_data=stage_workflow_input
        )
        triggered_workflows.append(workflow_id)

        return triggered_workflows

    def _ensure_workflows_uploaded(self) -> None:
        """Ensure all workflows for this stage are uploaded to Conductor."""
        # Check if workflows need to be uploaded (without actually uploading them)
        # This avoids race conditions during parallel stage evaluations
        from .conductor_client import get_workflow_definitions
        from .workflow_manager import get_workflow_manager

        try:
            # Get existing workflows from Conductor
            existing_workflows = get_workflow_definitions()
            existing_workflow_versions = {
                (w.get('name'), w.get('version', 1)): w
                for w in existing_workflows
            }

            # Check if any of our workflows are missing
            missing_workflows = []
            workflow_manager = get_workflow_manager()

            for wf in self.workflows:
                # Get the local workflow version
                local_workflow_file = workflow_manager.find_workflow_file(wf.name)
                if not local_workflow_file:
                    missing_workflows.append(f"{wf.name} (local file not found)")
                    continue

                local_workflow_def = workflow_manager.load_workflow_definition(local_workflow_file)
                if not local_workflow_def:
                    missing_workflows.append(f"{wf.name} (invalid local file)")
                    continue

                local_version = local_workflow_def.get('version', 1)

                # Check if this specific version exists in Conductor
                workflow_key = (wf.name, local_version)
                if workflow_key not in existing_workflow_versions:
                    missing_workflows.append(f"{wf.name} v{local_version}")

            if missing_workflows:
                print(f"Warning: Missing workflows: {', '.join(missing_workflows)}")
                print("Run 'idflow workflow upload' to upload missing workflows")
        except Exception as e:
            # If check fails, continue anyway - workflows might still work
            print(f"Warning: Could not check workflow status: {e}")

    def mark_stage_completed(self, doc, stage_id: str, conductor_client=None) -> None:
        """Mark a stage as completed and trigger events."""
        if not conductor_client:
            from .conductor_client import get_conductor_client
            conductor_client = get_conductor_client()

        # Update stage status in document
        stage = doc.get_stage_by_id(stage_id)
        if stage:
            stage.status = "done"
            doc.save()

            # Send stage completion event
            self._send_stage_completion_event(doc, stage, conductor_client)

    def _send_stage_completion_event(self, doc, stage, conductor_client) -> None:
        """Send stage completion event to conductor."""
        try:
            # In a real implementation, this would send an event to conductor
            # For now, we'll simulate the event sending
            event_data = {
                "event": "idflow:stage.completed",
                "docId": doc.id,
                "stage": {
                    "id": stage.id,
                    "name": stage.name,
                    "status": stage.status
                },
                "doc": {
                    "id": doc.id,
                    "status": doc.status,
                    "tags": doc.tags
                }
            }

            # This would be sent to conductor's event system
            # conductor_client.send_event(event_data)
            print(f"Stage completion event: {event_data}")

        except Exception as e:
            print(f"Failed to send stage completion event: {e}")


class StageDefinitions:
    """Manager for all stage definitions loaded from YAML files."""

    def __init__(self, stages_dir: Optional[Path] = None):
        # If stages_dir is provided, use only that directory; otherwise overlay package + project
        self.stages_dir = stages_dir
        self._definitions: Dict[str, StageDefinition] = {}
        self._load_definitions()

    def _load_definitions(self) -> None:
        """Load all stage definitions from YAML files with name-based deep merge (package -> project)."""
        self._definitions.clear()

        def _read_yaml(file_path: Path) -> Optional[Dict[str, Any]]:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                return data if isinstance(data, dict) else None
            except Exception as e:
                print(f"Warning: Failed to read YAML from {file_path}: {e}")
                return None

        def _merge_workflow_lists(base_list: List[Dict[str, Any]], overlay_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            # Merge by workflow name; items without name fall back to replacement
            try:
                base_map = {str(i.get('name')): i for i in base_list if isinstance(i, dict) and 'name' in i}
                result = [i for i in base_list if not (isinstance(i, dict) and 'name' in i)]
                for item in overlay_list:
                    if isinstance(item, dict) and 'name' in item:
                        name = str(item['name'])
                        if name in base_map:
                            base_item = base_map[name]
                            # deep merge dicts
                            result.append(_deep_merge_dicts(base_item, item))
                            del base_map[name]
                        else:
                            result.append(item)
                    else:
                        # Non-dict or missing name: append as-is
                        result.append(item)
                # Append remaining base named items not overridden
                for name, base_item in base_map.items():
                    result.append(base_item)
                return result
            except Exception:
                # Fallback: replace
                return overlay_list

        def _deep_merge_dicts(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
            merged: Dict[str, Any] = dict(base)
            for k, v in overlay.items():
                if k in merged:
                    bv = merged[k]
                    if isinstance(bv, dict) and isinstance(v, dict):
                        merged[k] = _deep_merge_dicts(bv, v)
                    elif k == 'workflows' and isinstance(bv, list) and isinstance(v, list):
                        merged[k] = _merge_workflow_lists(bv, v)
                    else:
                        merged[k] = v
                else:
                    merged[k] = v
            return merged

        # Expose helper inside method scope
        _deep_merge_dicts_ref = _deep_merge_dicts

        # Collect package then overlay project by stage name
        merged_by_name: Dict[str, Dict[str, Any]] = {}

        def _collect_from_dir(dir_path: Path, is_overlay: bool) -> None:
            if not dir_path.exists():
                return
            for yaml_file in dir_path.glob("*.yml"):
                data = _read_yaml(yaml_file)
                if not data:
                    continue
                stage_name = data.get('name')
                if not stage_name:
                    continue
                if stage_name in merged_by_name and is_overlay:
                    merged_by_name[stage_name] = _deep_merge_dicts_ref(merged_by_name[stage_name], data)
                elif stage_name in merged_by_name and not is_overlay:
                    # Multiple package files with same name: merge as well
                    merged_by_name[stage_name] = _deep_merge_dicts_ref(merged_by_name[stage_name], data)
                else:
                    merged_by_name[stage_name] = data

        # If explicit directory provided, load only there
        if self.stages_dir is not None:
            _collect_from_dir(self.stages_dir, is_overlay=False)
            # No project overlay when explicit dir is provided
            # Build definitions
            self._definitions.clear()
            for name, data in merged_by_name.items():
                try:
                    stage_def = StageDefinition(**data)
                    if stage_def.active:
                        self._definitions[stage_def.name] = stage_def
                except Exception as e:
                    print(f"Warning: Failed to load stage definition '{name}' from {self.stages_dir}: {e}")
            return

        # Multi-Base: lib -> vendors -> project
        from .resource_resolver import ResourceResolver
        rr = ResourceResolver()
        # definierte Reihenfolge: lib, vendors, project.
        bases: list[Path] = [b for _n, b in rr.bases()]

        for idx, base in enumerate(bases):
            is_overlay = (idx > 0)
            _collect_from_dir(base / "stages", is_overlay=is_overlay)

        # Build definitions from merged data
        self._definitions.clear()
        for name, data in merged_by_name.items():
            try:
                stage_def = StageDefinition(**data)
                if stage_def.active:
                    self._definitions[stage_def.name] = stage_def
            except Exception as e:
                print(f"Warning: Failed to load merged stage definition '{name}': {e}")

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
