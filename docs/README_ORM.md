# Document ORM System

This document describes the new Document ORM (Object-Relational Mapping) system that abstracts data manipulation for documents in idflow.

## Overview

The ORM system provides a clean abstraction layer over document operations, replacing direct filesystem manipulation with object-oriented interfaces. It includes lifecycle hooks, relation management, and query capabilities. **The system is now configurable**, allowing you to choose which Document implementation to use through configuration.

## Architecture

### Base Classes

#### `Document` (Abstract Base Class)
- **Location**: `idflow/core/document.py`
- **Purpose**: Abstract base class defining the interface for all document operations
- **Features**:
  - Lifecycle hooks (before_save, after_save, before_create, after_create, before_destroy, after_destroy)
  - Document and file reference management
  - Stage management
  - CRUD operations (create, save, destroy)
  - Query methods (find, where)

#### `Stage` (Document Subclass)
- **Purpose**: Represents a stage within a parent document
- **Features**:
  - Inherits all Document functionality
  - Has a parent document reference
  - Can contain files and references
  - Cannot be queried independently

### Concrete Implementations

#### `FSMarkdownDocument` (Default)
- **Location**: `idflow/core/fs_markdown.py`
- **Purpose**: Filesystem-based implementation using markdown files with YAML frontmatter
- **Features**:
  - Implements all abstract methods from Document
  - Handles filesystem operations (create, read, update, delete)
  - Manages file copying and reference creation
  - Supports stage persistence

#### `DatabaseDocument` (Future)
- **Purpose**: Database-based implementation for scalable document storage
- **Features**: (To be implemented)
  - Database persistence
  - Transaction support
  - Advanced querying capabilities

### Configuration-Driven Selection

#### `DocumentFactory`
- **Location**: `idflow/core/document_factory.py`
- **Purpose**: Factory class that loads the appropriate Document implementation based on configuration
- **Features**:
  - Automatically selects implementation based on `document_implementation` config
  - Supports runtime switching between implementations
  - Provides clean interface for CLI and application code

## Configuration

The ORM system is now configurable through the `idflow.yml` configuration file:

```yaml
# config/idflow.yml
base_dir: "data"
config_dir: "config"

# Choose your document implementation
document_implementation: "fs_markdown"  # or "database" (future)
```

### Environment Variables

You can also override the implementation using environment variables:

```bash
export IDFLOW_DOCUMENT_IMPL="fs_markdown"
```

### Supported Implementations

1. **`fs_markdown`** (default): Filesystem storage with markdown files
2. **`database`** (planned): Database storage for scalability

## Key Features

### 1. Lifecycle Hooks

The ORM provides six lifecycle hooks that can be overridden in subclasses:

```python
class MyDocument(FSMarkdownDocument):
    def before_create(self):
        print("About to create document")
        # Add validation, logging, etc.

    def after_create(self):
        print("Document created successfully")
        # Send notifications, update indexes, etc.

    def before_save(self):
        print("About to save document")
        # Add timestamps, validation, etc.

    def after_save(self):
        print("Document saved successfully")
        # Update caches, etc.

    def before_destroy(self):
        print("About to destroy document")
        # Cleanup, validation, etc.

    def after_destroy(self):
        print("Document destroyed successfully")
        # Remove from indexes, etc.
```

### 2. Document Relations

#### Document References
```python
# Add a reference to another document
doc.add_doc_ref("related", "uuid-of-related-doc")
doc.add_doc_ref("parent", "uuid-of-parent-doc", {"role": "parent"})

# Access references
for ref in doc.doc_refs:
    print(f"Reference: {ref.key} -> {ref.uuid}")
    print(f"Data: {ref.data}")
```

#### File References
```python
# Copy a file and create a reference
file_ref = doc.copy_file(Path("./example.txt"), "example_file")
file_ref.data = {"description": "Example file", "type": "text"}

# Access file references
for ref in doc.file_refs:
    print(f"File: {ref.key} -> {ref.filename}")
    print(f"UUID: {ref.uuid}")
    print(f"Data: {ref.data}")
```

### 3. Stages

Stages are sub-documents that can appear multiple times within a document:

```python
# Add stages to a document
planning_stage = doc.add_stage("planning", status="done")
planning_stage.body = "Planning phase completed"
planning_stage.set("start_date", "2024-01-01")

development_stage = doc.add_stage("development", status="active")
development_stage.body = "Development in progress"

# Access stages
for stage in doc.stages:
    print(f"Stage: {stage.name} - {stage.status}")
    print(f"Body: {stage.body}")
```

### 4. Query Methods

#### Find by UUID
```python
# Get the configured document class
from idflow.core.document_factory import get_document_class
DocumentClass = get_document_class()

# Find a document
doc = DocumentClass.find("document-uuid-here")
if doc:
    print(f"Found document: {doc.title}")
```

#### Find by Filters
```python
# Find by status
active_docs = DocumentClass.where(status="active")

# Find by document reference
docs_with_refs = DocumentClass.where(doc_ref="related")

# Find by file reference
docs_with_files = DocumentClass.where(file_ref="example_file")

# Find where property exists
docs_with_title = DocumentClass.where(exists="title")

# Find by custom property
docs_with_priority = DocumentClass.where(priority="high")
```

### 5. CRUD Operations

```python
# Get the configured document class
from idflow.core.document_factory import create_document

# Create
doc = create_document(title="New Document", status="inbox")
doc.create()

# Read (already loaded when created/found)
print(doc.title)
print(doc.body)

# Update
doc.title = "Updated Title"
doc.set("priority", "high")
doc.save()

# Delete
doc.destroy()
```

## CLI Integration

All CLI commands now use the configurable ORM system:

- `add.py` - Creates documents using the configured implementation
- `list.py` - Queries documents using the configured implementation
- `modify.py` - Modifies documents using the configured implementation
- `drop.py` - Deletes documents using the configured implementation
- `set_status.py` - Updates status using the configured implementation
- `locate.py` - Finds documents using the configured implementation
- `drop_all.py` - Deletes all documents using the configured implementation

## Usage Examples

### Basic Document Creation
```python
from idflow.core.document_factory import create_document

# Create a new document using the configured implementation
doc = create_document(
    title="My Document",
    status="active",
    body="This is the document content"
)

# Add some properties
doc.set("priority", "high")
doc.set("tags", ["important", "work"])

# Create the document
doc.create()
```

### Working with Relations
```python
# Add document references
doc.add_doc_ref("parent", "parent-uuid")
doc.add_doc_ref("child", "child-uuid", {"relationship": "depends_on"})

# Add file references
file_ref = doc.copy_file(Path("./attachment.pdf"), "documentation")
file_ref.data = {"type": "pdf", "pages": 10}

# Save changes
doc.save()
```

### Custom Document Classes
```python
from idflow.core.document_factory import get_document_class

# Get the configured base class
BaseDocument = get_document_class()

class ProjectDocument(BaseDocument):
    def before_save(self):
        # Auto-update last_modified timestamp
        self.set("last_modified", datetime.now().isoformat())

    def after_create(self):
        # Send notification
        self.set("created_at", datetime.now().isoformat())
        print(f"Project document {self.id} created")

# Use the custom class
project = ProjectDocument(
    title="New Project",
    status="active",
    project_code="PRJ-001"
)
project.create()
```

## Benefits

1. **Configurability**: Choose the storage backend through configuration
2. **Abstraction**: Clean separation between business logic and storage details
3. **Consistency**: Uniform interface for all document operations
4. **Extensibility**: Easy to add new features through inheritance
5. **Maintainability**: Centralized logic for common operations
6. **Testing**: Easier to mock and test document operations
7. **Lifecycle Management**: Built-in hooks for custom behavior
8. **Relation Management**: Structured handling of document and file references
9. **Query Interface**: Simple and powerful document finding capabilities

## Migration

The existing CLI commands have been updated to use the new configurable ORM without changing their external interface. This means:

- Existing scripts continue to work
- Command-line options remain the same
- Output format is preserved
- Performance characteristics are similar
- **New**: You can now switch implementations through configuration

## Future Enhancements

The ORM system is designed to be extensible:

1. **Database Backend**: `DatabaseDocument` class for database storage
2. **Caching**: Could add caching layers in the ORM
3. **Validation**: Could add schema validation in lifecycle hooks
4. **Indexing**: Could add search indexing in after_save hooks
5. **Audit Trail**: Could add change tracking in before_save hooks
6. **Cloud Storage**: Could add cloud storage implementations
7. **Hybrid Storage**: Could add implementations that combine multiple backends
