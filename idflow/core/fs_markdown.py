from __future__ import annotations
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar
from uuid import uuid4

from .document import Document
from .stage import Stage
from .models import FileRef
from .io import ensure_dir, write_frontmatter, read_frontmatter
from .repo import find_doc_dir
from .config import config

T = TypeVar('T', bound='FSMarkdownDocument')

class FSMarkdownDocument(Document):
    """
    Filesystem Markdown implementation of the Document ORM.

    This class implements the Document interface using the filesystem as storage,
    where each document is stored as a markdown file with YAML frontmatter.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Store the original status for status change detection
        self._original_status = self.status
        self._doc_dir: Optional[Path] = None
        self._doc_file: Optional[Path] = None
        self._data_dir: Optional[Path] = None

        # Set data directory from config
        self._data_dir = config.base_dir

    @property
    def doc_dir(self) -> Path:
        """Get the document directory path."""
        if self._doc_dir is None:
            # Always calculate the path based on current status and ID
            self._doc_dir = config.base_dir / self.status / self.id
        return self._doc_dir

    @property
    def doc_file(self) -> Path:
        """Get the document file path."""
        if self._doc_file is None:
            # Always calculate the path based on current status and ID
            self._doc_file = config.base_dir / self.status / self.id / "doc.md"
        return self._doc_file

    @property
    def data_dir(self) -> Path:
        """Get the data directory path."""
        return self._data_dir

    def _get_stage_path(self, stage_name: str, counter: int = 1) -> Path:
        """Get the filesystem path for a stage."""
        return self.doc_dir / "stages" / stage_name / str(counter)

    def _load_stages(self) -> List[Stage]:
        """Load stages from the filesystem."""
        from .stage import Stage

        stages = []
        stages_dir = self.doc_dir / "stages"

        if stages_dir.exists():
            for stage_name_dir in stages_dir.iterdir():
                if stage_name_dir.is_dir():
                    # Each stage name can have multiple counter directories
                    for counter_dir in stage_name_dir.iterdir():
                        if counter_dir.is_dir() and counter_dir.name.isdigit():
                            stage_file = counter_dir / "stage.md"
                            if stage_file.exists():
                                try:
                                    stage_data, body = read_frontmatter(stage_file)
                                    counter = int(counter_dir.name)
                                    # Filter out name, counter, and body from stage_data to avoid conflicts
                                    filtered_stage_data = {k: v for k, v in stage_data.items() if k not in ['name', 'counter', 'body']}
                                    stage = Stage(
                                        name=stage_name_dir.name,
                                        parent=self,
                                        counter=counter,
                                        body=body,
                                        **filtered_stage_data
                                    )
                                    stages.append(stage)
                                except Exception:
                                    # Skip corrupted stage files
                                    continue

        return stages

    def _save_stage(self, stage: Stage) -> None:
        """Save a stage to the filesystem."""
        stage_dir = self._get_stage_path(stage.name, stage.counter)
        ensure_dir(stage_dir)

        stage_file = stage_dir / "stage.md"
        stage_data = stage.to_dict()
        write_frontmatter(stage_file, stage_data, stage.body)

    def _create_stage(self, stage: Stage) -> None:
        """Create a new stage in the filesystem."""
        self._save_stage(stage)

    def _destroy_stage(self, stage: Stage) -> None:
        """Destroy a stage from the filesystem."""
        stage_dir = self._get_stage_path(stage.name, stage.counter)
        if stage_dir.exists():
            shutil.rmtree(stage_dir)

    def _save(self) -> None:
        """Save the document to the filesystem."""
        # Check if status has changed and we need to move the directory
        if hasattr(self, '_original_status') and self._original_status != self.status:
            self._move_to_status_directory()

        # Ensure the status is correctly set in the data
        self._data['status'] = self.status

        ensure_dir(self.doc_dir)
        doc_data = self.to_dict()

        # Remove body from data since it's handled separately
        if 'body' in doc_data:
            del doc_data['body']

        write_frontmatter(self.doc_file, doc_data, self.body)

    def _move_to_status_directory(self) -> None:
        """Move the document directory to the correct status directory."""
        if not hasattr(self, '_original_status'):
            return

        old_status = self._original_status
        new_status = self.status

        if old_status == new_status:
            return

        # Get the old and new directory paths
        base_dir = config.base_dir
        old_dir = base_dir / old_status / self.id
        new_dir = base_dir / new_status / self.id

        # Ensure the new status directory exists
        ensure_dir(new_dir.parent)

        # Move the directory
        if old_dir.exists():
            if new_dir.exists():
                # Remove the new directory if it exists (shouldn't happen, but just in case)
                shutil.rmtree(new_dir)
            shutil.move(str(old_dir), str(new_dir))

            # Reset internal paths so they get recalculated with new status
            self._doc_dir = None
            self._doc_file = None

        # Update the original status to prevent infinite loops
        self._original_status = new_status

    def _create(self) -> None:
        """Create a new document in the filesystem."""
        self._save()

    def _destroy(self) -> None:
        """Destroy the document from the filesystem."""
        if self.doc_dir.exists():
            shutil.rmtree(self.doc_dir)

    @classmethod
    def _find(cls: Type[T], uuid: str) -> Optional[T]:
        """Find a document by UUID in the filesystem."""
        base_dir = config.base_dir
        valid_statuses = ['inbox', 'active', 'done', 'blocked', 'archived']

        for status in valid_statuses:
            doc_dir = base_dir / status / uuid
            doc_file = doc_dir / "doc.md"

            if doc_file.exists():
                try:
                    doc_data, body = read_frontmatter(doc_file)
                    doc = cls(body=body, **doc_data)
                    # Store the original status from the filesystem location
                    doc._original_status = status
                    # Mark as persisted since it was loaded from storage
                    doc._persisted = True
                    # Reset internal paths so they get recalculated
                    doc._doc_dir = None
                    doc._doc_file = None
                    return doc
                except Exception:
                    continue

        return None

    @classmethod
    def _where(cls: Type[T], **filters) -> List[T]:
        """Find documents matching the given filters in the filesystem."""
        base_dir = config.base_dir
        documents = []
        valid_statuses = ['inbox', 'active', 'done', 'blocked', 'archived']

        for status in valid_statuses:
            status_dir = base_dir / status
            if not status_dir.exists():
                continue

            for doc_dir in status_dir.iterdir():
                if not doc_dir.is_dir():
                    continue

                doc_file = doc_dir / "doc.md"
                if not doc_file.exists():
                    continue

                try:
                    doc_data, body = read_frontmatter(doc_file)
                    doc = cls(body=body, **doc_data)
                    # Store the original status for status change detection
                    doc._original_status = status
                    # Mark as persisted since it was loaded from storage
                    doc._persisted = True

                    # Apply filters
                    if cls._matches_filters(doc, filters):
                        documents.append(doc)
                except Exception:
                    # Skip corrupted documents
                    continue

        return documents

    @classmethod
    def _matches_filters(cls, doc: T, filters: Dict[str, Any]) -> bool:
        """Check if a document matches the given filters."""
        for key, value in filters.items():
            if key == 'status':
                if doc.status != value:
                    return False
            elif key == 'doc_ref':
                # Check if document has a reference with the given key
                ref_keys = [ref.key for ref in doc.doc_refs]
                if value not in ref_keys:
                    return False
            elif key == 'file_ref':
                # Check if document has a file reference with the given key
                ref_keys = [ref.key for ref in doc.file_refs]
                if value not in ref_keys:
                    return False
            elif key == 'exists':
                # Check if a property exists
                if doc.get(value) is None:
                    return False
            else:
                # Check if property value matches
                doc_value = doc.get(key)
                if doc_value != value:
                    return False

        return True

    @classmethod
    def from_file(cls: Type[T], file_path: Path) -> T:
        """Create a document instance from a markdown file."""
        if not file_path.exists():
            raise FileNotFoundError(f"Document file not found: {file_path}")

        doc_data, body = read_frontmatter(file_path)
        doc = cls(body=body, **doc_data)

        # Try to determine the original status from the file path
        try:
            # Extract status from path: data/status/uuid/doc.md
            path_parts = file_path.parts
            if len(path_parts) >= 3 and path_parts[-3] in ['inbox', 'active', 'done', 'blocked', 'archived']:
                doc._original_status = path_parts[-3]
        except Exception:
            # If we can't determine the status, use the current status
            doc._original_status = doc.status

        return doc

    @classmethod
    def from_dir(cls: Type[T], dir_path: Path) -> T:
        """Create a document instance from a document directory."""
        doc_file = dir_path / "doc.md"
        return cls.from_file(doc_file)

    def copy_file(self, src_path: Path, file_key: str) -> FileRef:
        """Copy a file to the document directory and create a file reference."""
        if not src_path.exists() or not src_path.is_file():
            raise FileNotFoundError(f"Source file not found: {src_path}")

        # Ensure document directory exists
        self.doc_dir.mkdir(parents=True, exist_ok=True)

        file_uuid = str(uuid4())
        dst_path = self.doc_dir / file_uuid

        # Copy the file
        shutil.copyfile(src_path, dst_path)

        # Create and add file reference
        file_ref = self.add_file_ref(
            key=file_key,
            filename=src_path.name,
            uuid=file_uuid
        )

        return file_ref

    def get_file_path(self, file_ref: FileRef) -> Path:
        """Get the filesystem path for a file reference."""
        return self.doc_dir / file_ref.uuid

    def list_files(self) -> List[Path]:
        """List all files in the document directory."""
        files = []
        for item in self.doc_dir.iterdir():
            if item.is_file() and item.name != "doc.md":
                files.append(item)
        return files

    def list_stage_files(self, stage: Stage) -> List[Path]:
        """List all files in a stage directory."""
        stage_dir = self._get_stage_path(stage.name, stage.counter)
        if not stage_dir.exists():
            return []

        files = []
        for item in stage_dir.iterdir():
            if item.is_file() and item.name != "stage.md":
                files.append(item)
        return files
