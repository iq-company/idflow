from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, TYPE_CHECKING
from uuid import uuid4

from .models import DocRef, FileRef, VALID_STATUS, VALID_STAGE_STATUS

if TYPE_CHECKING:
    from .stage import Stage

T = TypeVar('T', bound='Document')

class Document(ABC):
    """
    Base Document ORM class that provides lifecycle hooks, relations, and query methods.

    This abstract class defines the interface for document operations and can be
    subclassed to implement specific persistence strategies (e.g., filesystem, database).
    """

    def __init__(self, **kwargs):
        """Initialize a new document with the given attributes."""
        self.id = kwargs.get('id', str(uuid4()))
        self.status = kwargs.get('status', 'inbox')
        self._data = kwargs.copy()
        self._data['id'] = self.id
        self._data['status'] = self.status
        self._stages: Optional[List['Stage']] = None
        self._doc_refs: Optional[List[DocRef]] = None
        self._file_refs: Optional[List[FileRef]] = None
        self._body: str = kwargs.get('body', '')
        self._dirty: bool = False  # Track if document has unsaved changes

        # Validate status - will be overridden in subclasses
        self._validate_status()

    def _validate_status(self) -> None:
        """Validate the document status. Override in subclasses for custom validation."""
        if self.status not in VALID_STATUS:
            raise ValueError(f"Invalid status: {self.status}. Must be one of {VALID_STATUS}")

    def __getattr__(self, name: str) -> Any:
        """Allow accessing document attributes as object properties."""
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        """Allow setting document attributes as object properties."""
        if name in ['id', 'status', '_data', '_stages', '_doc_refs', '_file_refs', '_body', '_dirty']:
            super().__setattr__(name, value)
        elif name == 'body':
            # Handle body separately to avoid duplication
            super().__setattr__('_body', value)
            self._dirty = True
        else:
            self._data[name] = value
            self._dirty = True

    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access to document attributes."""
        return self._data.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Allow dictionary-style setting of document attributes."""
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a document attribute with a default value."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a document attribute."""
        self._data[key] = value

    @property
    def body(self) -> str:
        """Get the document body content."""
        return self._body

    @body.setter
    def body(self, value: str) -> None:
        """Set the document body content."""
        self._body = value

    @property
    def doc_refs(self) -> List[DocRef]:
        """Get document references."""
        if self._doc_refs is None:
            self._doc_refs = []
            for ref_data in self._data.get('_doc_refs', []):
                if isinstance(ref_data, dict):
                    self._doc_refs.append(DocRef(**ref_data))
                elif isinstance(ref_data, DocRef):
                    self._doc_refs.append(ref_data)
        return self._doc_refs

    @property
    def file_refs(self) -> List[FileRef]:
        """Get file references."""
        if self._file_refs is None:
            self._file_refs = []
            for ref_data in self._data.get('_file_refs', []):
                if isinstance(ref_data, dict):
                    self._file_refs.append(FileRef(**ref_data))
                elif isinstance(ref_data, FileRef):
                    self._file_refs.append(ref_data)
        return self._file_refs

    @property
    def stages(self) -> List['Stage']:
        """Get document stages."""
        if self._stages is None:
            self._stages = self._load_stages()
        return self._stages

    def add_doc_ref(self, key: str, uuid: str, data: Optional[Dict[str, Any]] = None) -> DocRef:
        """Add a document reference."""
        ref = DocRef(key=key, uuid=uuid, data=data or {})
        self.doc_refs.append(ref)
        self._data['_doc_refs'] = [ref.model_dump() for ref in self.doc_refs]
        return ref

    def add_file_ref(self, key: str, filename: str, uuid: str, data: Optional[Dict[str, Any]] = None) -> FileRef:
        """Add a file reference."""
        ref = FileRef(key=key, filename=filename, uuid=uuid, data=data or {})
        self.file_refs.append(ref)
        self._data['_file_refs'] = [ref.model_dump() for ref in self.file_refs]
        return ref

    def add_stage(self, name: str, **kwargs) -> 'Stage':
        """Add a new stage to this document."""
        # Count existing stages with this name to determine counter
        existing_stages = [s for s in self.stages if s.name == name]
        counter = len(existing_stages) + 1

        # Import Stage class to avoid circular import
        from .stage import Stage

        # Create stage first
        stage = Stage(name=name, parent=self, counter=counter, **kwargs)

        # Check requirements if no explicit status provided
        if 'status' not in kwargs:
            from .stage_definitions import get_stage_definitions
            stage_definitions = get_stage_definitions()
            stage_def = stage_definitions.get_definition(name)

            if stage_def and stage_def.check_requirements(self):
                stage.status = 'active'
            else:
                stage.status = 'scheduled'

        self.stages.append(stage)
        self._dirty = True

        # Save the stage immediately
        stage.save()

        # Update document status to "active" if it was "inbox" and has stages
        if self.status == "inbox" and len(self.stages) > 0:
            self.status = "active"

        return stage

    def get_stages(self, name: str) -> List['Stage']:
        """Get all stages with the given name."""
        return [s for s in self.stages if s.name == name]

    def get_stage(self, name: str, counter: int = 1) -> Optional['Stage']:
        """Get a specific stage by name and counter."""
        for stage in self.stages:
            if stage.name == name and stage.counter == counter:
                return stage
        return None

    def get_stage_by_id(self, stage_id: str) -> Optional['Stage']:
        """Get a specific stage by its ID."""
        for stage in self.stages:
            if stage.id == stage_id:
                return stage
        return None

    def mark_stage_dirty(self, stage: 'Stage') -> None:
        """Mark a stage as dirty, which marks the parent document as dirty."""
        self._dirty = True

    def _load_stages(self) -> List['Stage']:
        """Load stages from storage. Override in subclasses."""
        return []

    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary representation."""
        result = self._data.copy()

        # Remove internal ORM attributes that shouldn't be serialized
        internal_attrs = ['_doc_dir', '_doc_file', '_data_dir', '_stages', '_doc_refs', '_file_refs']
        for attr in internal_attrs:
            if attr in result:
                del result[attr]

        # Add the serialized references
        result['_doc_refs'] = [ref.model_dump() for ref in self.doc_refs]
        result['_file_refs'] = [ref.model_dump() for ref in self.file_refs]

        return result

    # Lifecycle hooks
    def before_save(self) -> None:
        """Called before saving the document. Override in subclasses."""
        # Only trigger stage evaluation for updates (not for new documents)
        if hasattr(self, '_persisted') and self._persisted:
            self._trigger_stage_evaluation()

    def after_save(self) -> None:
        """Called after saving the document. Override in subclasses."""
        # Trigger stage evaluation and check if status changed
        result = self._trigger_stage_evaluation()

        # If status changed during stage evaluation, save again
        if result and result.get('status_changed'):
            self._save()
            self._dirty = False

        self._handle_stage_lifecycle()

    def before_create(self) -> None:
        """Called before creating the document. Override in subclasses."""
        pass

    def after_create(self) -> None:
        """Called after creating the document. Override in subclasses."""
        # Trigger stage evaluation and check if status changed
        result = self._trigger_stage_evaluation()

        # If status changed during stage evaluation, save again
        if result and result.get('status_changed'):
            self._save()
            self._dirty = False

    def before_destroy(self) -> None:
        """Called before destroying the document. Override in subclasses."""
        self._cancel_all_stages()

    def after_destroy(self) -> None:
        """Called after destroying the document. Override in subclasses."""
        pass

    # CRUD operations
    def save(self) -> None:
        """Save the document and all dirty stages. Automatically detects if it's a new document."""
        # Check if this is a new document (hasn't been persisted yet)
        if not hasattr(self, '_persisted') or not self._persisted:
            # This is a new document, call create
            self.create()
        else:
            # This is an existing document, call update
            self.before_save()

            # Save all dirty stages first
            if self._stages:
                for stage in self._stages:
                    if hasattr(stage, '_dirty') and stage._dirty:
                        stage._save()
                        stage._dirty = False

            self._save()
            self._dirty = False
            self.after_save()

    def create(self) -> None:
        """Create a new document."""
        self.before_create()
        self._create()
        self._persisted = True  # Mark as persisted
        self.after_create()

    def destroy(self) -> None:
        """Destroy the document."""
        self.before_destroy()
        self._destroy()
        self.after_destroy()

    @abstractmethod
    def _save(self) -> None:
        """Internal save implementation. Override in subclasses."""
        pass

    @abstractmethod
    def _create(self) -> None:
        """Internal create implementation. Override in subclasses."""
        pass

    @abstractmethod
    def _destroy(self) -> None:
        """Internal destroy implementation. Override in subclasses."""
        pass

    # Query methods
    @classmethod
    def find(cls: Type[T], uuid: str) -> Optional[T]:
        """Find a document by UUID."""
        return cls._find(uuid)

    @classmethod
    def where(cls: Type[T], **filters) -> List[T]:
        """Find documents matching the given filters."""
        return cls._where(**filters)

    @classmethod
    @abstractmethod
    def _find(cls: Type[T], uuid: str) -> Optional[T]:
        """Internal find implementation. Override in subclasses."""
        pass

    @classmethod
    @abstractmethod
    def _where(cls: Type[T], **filters) -> List[T]:
        """Internal where implementation. Override in subclasses."""
        pass

    def _handle_stage_lifecycle(self) -> None:
        """Handle stage lifecycle based on document status changes."""
        # Get all stages in scheduled or active status
        active_stages = [s for s in self.stages if s.status in {"scheduled", "active"}]

        if not active_stages:
            return

        # Handle different document statuses
        if self.status == "inbox":
            # Nothing to do for inbox status
            return

        elif self.status in {"done", "blocked", "archived"}:
            # Document is in final state - cancel or complete stages
            for stage in active_stages:
                if stage.status == "scheduled":
                    stage.status = "cancelled"
                elif stage.status == "active":
                    # Map document status to stage status
                    if self.status == "done":
                        stage.status = "done"
                    elif self.status == "blocked":
                        stage.status = "blocked"
                    else:  # archived
                        stage.status = "cancelled"

        elif self.status == "active":
            # Document is active - check requirements for stages
            for stage in active_stages:
                if stage.status == "scheduled":
                    # Check if requirements are met to activate
                    if stage.check_requirements():
                        stage.status = "active"
                        stage.trigger_workflows()
                elif stage.status == "active":
                    # Check if requirements are still met
                    if not stage.check_requirements():
                        stage.status = "cancelled"

    def _cancel_all_stages(self) -> None:
        """Cancel all scheduled and active stages before document destruction."""
        active_stages = [s for s in self.stages if s.status in {"scheduled", "active"}]
        for stage in active_stages:
            stage.status = "cancelled"

    def _trigger_stage_evaluation(self) -> Optional[Dict[str, Any]]:
        """Trigger stage evaluation for documents with status 'inbox' or 'active'."""
        # Only trigger stage evaluation for documents in active states
        if self.status not in {"inbox", "active"}:
            return None

        try:
            return self.evaluate_stages()
        except Exception as e:
            # Don't fail document save if stage evaluation fails
            print(f"Warning: Failed to evaluate stages for document {self.id}: {e}")
            return None

    def evaluate_stages(self, stage_name: Optional[str] = None, allow_rerun: bool = False) -> Dict[str, Any]:
        """
        Evaluate stage requirements for this document and automatically start stages where requirements are met.

        Args:
            stage_name: Specific stage name to evaluate (None for all stages)
            allow_rerun: Allow rerunning completed stages with multiple_callable: true

        Returns:
            Dictionary with evaluation results
        """
        from .stage_definitions import get_stage_definitions

        # Get stage definitions
        stage_definitions = get_stage_definitions()
        available_stages = stage_definitions.list_definitions()

        if not available_stages:
            return {
                "success": False,
                "error": "No stage definitions found",
                "stages_evaluated": 0,
                "stages_started": 0,
                "stages_skipped": 0
            }

        # Filter stages if specific stage requested
        stages_to_evaluate = available_stages
        if stage_name:
            if stage_name not in available_stages:
                return {
                    "success": False,
                    "error": f"Stage '{stage_name}' not found",
                    "available_stages": available_stages,
                    "stages_evaluated": 0,
                    "stages_started": 0,
                    "stages_skipped": 0
                }
            stages_to_evaluate = [stage_name]

        # Track results
        total_evaluated = 0
        stages_started = 0
        stages_skipped = 0
        started_stages = []
        skipped_stages = []

        # Track if document has any stages (existing or newly created)
        has_stages = len(self.stages) > 0
        original_status = self.status

        for stage_name in stages_to_evaluate:
            stage_def = stage_definitions.get_definition(stage_name)
            if not stage_def:
                continue

            # Check if stage already exists for this document
            existing_stages = self.get_stages(stage_name)

            # Determine if we can create/rerun this stage
            can_create = True
            skip_reason = None

            if existing_stages:
                # Check if any stage is still active (scheduled or active)
                active_stages = [s for s in existing_stages if s.status in {"scheduled", "active"}]
                if active_stages:
                    can_create = False
                    skip_reason = f"already has active stage (status: {active_stages[0].status})"
                elif not allow_rerun:
                    can_create = False
                    skip_reason = "already exists (use allow_rerun to rerun completed stages)"
                elif not stage_def.multiple_callable:
                    can_create = False
                    skip_reason = "not marked as multiple_callable in stage definition"

            if not can_create:
                skipped_stages.append({
                    "name": stage_name,
                    "reason": skip_reason
                })
                stages_skipped += 1
                continue

            # Check requirements
            requirements_met = stage_def.check_requirements(self)
            total_evaluated += 1

            if requirements_met:
                # Create stage in active status (requirements are met)
                new_stage = self.add_stage(stage_name, status="active")
                has_stages = True  # Mark that document now has stages

                # Trigger workflows for this stage
                triggered_workflows = []
                try:
                    triggered_workflows = stage_def.trigger_workflows(self)
                except Exception as e:
                    # Log error but don't fail the stage creation
                    print(f"Warning: Failed to trigger workflows for stage {stage_name}: {e}")

                started_stages.append({
                    "name": stage_name,
                    "id": new_stage.id,
                    "counter": new_stage.counter,
                    "workflows_triggered": len(triggered_workflows)
                })
                stages_started += 1
            else:
                skipped_stages.append({
                    "name": stage_name,
                    "reason": "requirements not met"
                })
                stages_skipped += 1

        # Update document status to "active" if it was "inbox" and has stages
        status_changed = False
        if original_status == "inbox" and has_stages:
            self.status = "active"
            status_changed = True
            # Mark document as dirty so it gets saved
            self._dirty = True
        elif original_status != self.status:
            # Status was already changed during stage evaluation
            status_changed = True

        return {
            "success": True,
            "stages_evaluated": total_evaluated,
            "stages_started": stages_started,
            "stages_skipped": stages_skipped,
            "started_stages": started_stages,
            "skipped_stages": skipped_stages,
            "status_changed": status_changed,
            "document_status": self.status
        }
