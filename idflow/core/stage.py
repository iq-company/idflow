from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from uuid import uuid4

from .models import DocRef, FileRef, VALID_STAGE_STATUS
from .document import Document

T = TypeVar('T', bound='Stage')


class Stage(Document):
    """
    Stage model that inherits from Document and represents a stage within a parent document.

    Stages can appear multiple times within a document and have their own files and references.
    """

    def __init__(self, name: str, parent: Document, counter: int = 1, **kwargs):
        # Validate that parent is a Document, not a Stage
        if isinstance(parent, Stage):
            raise ValueError(f"Stage parent must be a Document, not a Stage. Got: {type(parent)}")

        # Filter out name and counter from kwargs to avoid conflicts
        stage_kwargs = {k: v for k, v in kwargs.items() if k not in ['name', 'counter']}

        # Set default status for stages if not provided
        if 'status' not in stage_kwargs:
            stage_kwargs['status'] = 'scheduled'

        super().__init__(**stage_kwargs)
        self.name = name
        self.parent = parent
        self.counter = counter
        self._dirty = False
        self._data['name'] = name
        self._data['counter'] = counter
        self._data['parent_id'] = parent.id

        # Load stage definition
        self._stage_definition = None
        self._load_stage_definition()

    def _validate_status(self) -> None:
        """Validate the stage status using stage-specific valid statuses."""
        if self.status not in VALID_STAGE_STATUS:
            raise ValueError(f"Invalid stage status: {self.status}. Must be one of {VALID_STAGE_STATUS}")

    def set_status(self, status: str) -> None:
        """Set the stage status and mark as dirty."""
        super().__setattr__('status', status)
        super().__setattr__('_dirty', True)
        if hasattr(self, 'parent') and self.parent:
            self.parent.mark_stage_dirty(self)

    def __setattr__(self, name: str, value: Any) -> None:
        """Override __setattr__ to notify parent document of changes."""
        if name in ['id', '_data', '_stages', '_doc_refs', '_file_refs', '_body', '_dirty', 'name', 'parent', 'counter']:
            super().__setattr__(name, value)
        elif name == 'status':
            # Handle status separately to mark as dirty and update _data
            super().__setattr__(name, value)
            # Also update _data so to_dict() returns the correct status
            try:
                if self._data:
                    self._data['status'] = value
                    # Only mark as dirty after initialization is complete and parent exists
                    if hasattr(self, 'parent') and self.parent:
                        super().__setattr__('_dirty', True)
                        self.parent.mark_stage_dirty(self)
            except (AttributeError, RecursionError):
                # During initialization, attributes may not be available yet
                pass
        elif name == 'body':
            # Handle body separately to avoid duplication
            super().__setattr__('_body', value)
            self._dirty = True
            if hasattr(self, 'parent') and self.parent:
                self.parent.mark_stage_dirty(self)
        else:
            self._data[name] = value
            self._dirty = True
            if hasattr(self, 'parent') and self.parent:
                self.parent.mark_stage_dirty(self)

    @property
    def stage_path(self) -> Path:
        """Get the filesystem path for this stage relative to the parent document."""
        return self.parent._get_stage_path(self.name, self.counter)

    def to_dict(self) -> Dict[str, Any]:
        """Convert stage to dictionary representation, filtering out internal attributes."""
        result = self._data.copy()

        # Remove internal ORM attributes that shouldn't be serialized
        internal_attrs = ['_doc_dir', '_doc_file', '_data_dir', '_stages', '_doc_refs', '_file_refs', '_stage_definition']
        for attr in internal_attrs:
            if attr in result:
                del result[attr]

        # Remove parent object reference (keep only parent_id)
        if 'parent' in result:
            del result['parent']

        # Add the serialized references
        result['_doc_refs'] = [ref.model_dump() for ref in self.doc_refs]
        result['_file_refs'] = [ref.model_dump() for ref in self.file_refs]

        return result

    def _load_stages(self) -> List['Stage']:
        """Stages don't have sub-stages, so return empty list."""
        return []

    def _save(self) -> None:
        """Save stage data."""
        self.parent._save_stage(self)

    def _create(self) -> None:
        """Create stage data."""
        self.parent._create_stage(self)

    def _destroy(self) -> None:
        """Destroy stage data."""
        self.parent._destroy_stage(self)

    @classmethod
    def _find(cls, uuid: str) -> Optional['Stage']:
        """Find stage by UUID - not implemented for stages."""
        raise NotImplementedError("Stages cannot be found independently")

    @classmethod
    def _where(cls, **filters) -> List['Stage']:
        """Find stages by filters - not implemented for stages."""
        raise NotImplementedError("Stages cannot be queried independently")

    def _load_stage_definition(self) -> None:
        """Load the stage definition for this stage."""
        try:
            from .stage_definitions import get_stage_definitions
            stage_definitions = get_stage_definitions()
            self._stage_definition = stage_definitions.get_definition(self.name)
        except Exception:
            # If stage definitions can't be loaded, set to None
            self._stage_definition = None

    @property
    def stage_definition(self):
        """Get the stage definition for this stage."""
        return self._stage_definition

    def check_requirements(self) -> bool:
        """Check if the requirements for this stage are met."""
        if not self._stage_definition:
            return True
        return self._stage_definition.check_requirements(self.parent)

    def trigger_workflows(self, conductor_client=None) -> List[str]:
        """Trigger the configured workflows for this stage."""
        if not self._stage_definition:
            return []
        return self._stage_definition.trigger_workflows(self.parent, self.counter, conductor_client)

    def before_save(self) -> None:
        """Called before saving the stage."""
        super().before_save()

        # Only process if stage definition exists and status is not final
        if not self._stage_definition or self.status in {"done", "blocked", "cancelled", "archived"}:
            return

        # Check requirements and update status accordingly
        requirements_met = self.check_requirements()

        if requirements_met and self.status == "scheduled":
            # Requirements are met and stage is scheduled -> activate
            self.status = "active"
            # Trigger workflows
            self.trigger_workflows()
        elif not requirements_met and self.status == "active":
            # Requirements no longer met and stage is active -> cancel
            self.status = "cancelled"

    def after_create(self) -> None:
        """Override after_create to prevent stage evaluation on stages."""
        # Stages should not trigger stage evaluation like documents do
        # Just call the parent's before_create behavior without evaluation
        pass

    def after_save(self) -> None:
        """Override after_save to prevent stage evaluation on stages."""
        # Stages should not trigger stage evaluation like documents do
        pass

    def persist_sub_doc(self, filename: str, content: str) -> Path:
        """
        Persistiert einen Sub-Dokument-Inhalt als einfache Markdown-Datei.

        Args:
            filename: Name der Datei (ohne .md Extension)
            content: Der Inhalt der Datei

        Returns:
            Path zur erstellten Datei
        """
        from .io import ensure_dir

        # Stelle sicher, dass das Stage-Verzeichnis existiert
        ensure_dir(self.stage_path)

        # Erstelle den Dateipfad
        file_path = self.stage_path / f"{filename}.md"

        # Schreibe den Inhalt
        file_path.write_text(content, encoding='utf-8')

        return file_path

    def persist_sub_doc_frontmatter(self, filename: str, content_dict: Dict[str, Any]) -> Path:
        """
        Persistiert einen Sub-Dokument-Inhalt als Markdown-Datei mit Frontmatter.

        Args:
            filename: Name der Datei (ohne .md Extension)
            content_dict: Dictionary mit Frontmatter-Daten und 'body' oder 'content' für den Hauptinhalt

        Returns:
            Path zur erstellten Datei
        """
        from .io import ensure_dir, write_frontmatter

        # Stelle sicher, dass das Stage-Verzeichnis existiert
        ensure_dir(self.stage_path)

        # Erstelle den Dateipfad
        file_path = self.stage_path / f"{filename}.md"

        # Extrahiere den Hauptinhalt
        body_content = content_dict.get('body', '')

        # Entferne body/content aus dem Dict für das Frontmatter
        frontmatter_data = {k: v for k, v in content_dict.items() if k not in ['body', 'content']}

        # Schreibe mit Frontmatter
        write_frontmatter(file_path, frontmatter_data, body_content)

        return file_path
