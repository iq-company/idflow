from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from uuid import uuid4

from .models import DocRef, FileRef, VALID_STATUS

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

        # Validate status
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

        stage = Stage(name=name, parent=self, counter=counter, **kwargs)
        self.stages.append(stage)
        self._dirty = True
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
        pass

    def after_save(self) -> None:
        """Called after saving the document. Override in subclasses."""
        pass

    def before_create(self) -> None:
        """Called before creating the document. Override in subclasses."""
        pass

    def after_create(self) -> None:
        """Called after creating the document. Override in subclasses."""
        pass

    def before_destroy(self) -> None:
        """Called before destroying the document. Override in subclasses."""
        pass

    def after_destroy(self) -> None:
        """Called after destroying the document. Override in subclasses."""
        pass

    # CRUD operations
    def save(self) -> None:
        """Save the document and all dirty stages."""
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


class Stage(Document):
    """
    Stage model that inherits from Document and represents a stage within a parent document.

    Stages can appear multiple times within a document and have their own files and references.
    """

    def __init__(self, name: str, parent: Document, counter: int = 1, **kwargs):
        # Filter out name and counter from kwargs to avoid conflicts
        stage_kwargs = {k: v for k, v in kwargs.items() if k not in ['name', 'counter']}
        super().__init__(**stage_kwargs)
        self.name = name
        self.parent = parent
        self.counter = counter
        self._dirty = False
        self._data['name'] = name
        self._data['counter'] = counter
        self._data['parent_id'] = parent.id

    def __setattr__(self, name: str, value: Any) -> None:
        """Override __setattr__ to notify parent document of changes."""
        if name in ['id', 'status', '_data', '_stages', '_doc_refs', '_file_refs', '_body', '_dirty', 'name', 'parent', 'counter']:
            super().__setattr__(name, value)
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
        internal_attrs = ['_doc_dir', '_doc_file', '_data_dir', '_stages', '_doc_refs', '_file_refs']
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
