# Workflow Management

## Overview

ID Flow verwendet Conductor für Workflow-Orchestrierung. Workflows werden als JSON-Dateien im `idflow/workflows/` Verzeichnis definiert und müssen zu Conductor hochgeladen werden, bevor sie ausgeführt werden können.

## 🆕 Neue Features

### Task-Management Integration
- **Task-Synchronisation**: Automatische Synchronisation zwischen lokalen und Remote-Tasks
- **Orphaned Task Cleanup**: Bereinigung von nicht mehr benötigten Remote-Tasks
- **Usage-Check**: Sicherheitsprüfung vor Task-Löschung
- **Bidirektionale Sync**: Vollständige Synchronisation in beide Richtungen

## Workflow Upload Strategy

### Automatic vs Manual Upload

**Important**: Workflows are NOT automatically uploaded during stage evaluation to avoid race conditions and database locks. Instead, they should be uploaded manually using the CLI command.

### Manual Upload Commands

```bash
# Upload all workflows (with version checking)
idflow workflow upload

# Force upload all workflows (ignores version checks)
idflow workflow upload --force

# Upload specific workflow
idflow workflow upload --workflow workflow_name

# Force upload specific workflow
idflow workflow upload --workflow workflow_name --force
```

### Task Management Commands (NEW!)

```bash
# List and sync tasks
idflow tasks list --sync

# Upload all tasks
idflow tasks upload --all

# Purge orphaned tasks
idflow tasks purge --orphaned
```

### List Commands

```bash
# List workflows (local and remote)
idflow workflow list

# List only local workflows
idflow workflow list --local

# List only remote workflows
idflow workflow list --conductor

# List tasks with sync status
idflow tasks list --sync
```

### Upload Output Examples

**When all workflows are up to date:**
```
Found 10 workflow files
Workflow stage_evaluation_trigger is up to date (already exists in Conductor)
...
Skipped 10 workflows (already up to date)

Summary: All 10 workflows are up to date
```

**When some workflows need uploading:**
```
Found 10 workflow files
Workflow stage_evaluation_trigger is up to date (already exists in Conductor)
✓ Uploaded workflow: sub_workflow_1
...

Workflow upload results:
  ✓ sub_workflow_1

Skipped 9 workflows (already up to date)

Summary: 1/10 workflows uploaded successfully
```

**Single workflow upload:**
```
Uploading workflow 'sub_workflow_1' to Conductor...
Workflow sub_workflow_1 is up to date (already exists in Conductor)

Skipped 1 workflows (already up to date)

Summary: All 1 workflows are up to date
```

**Force upload single workflow:**
```
Uploading workflow 'sub_workflow_1' to Conductor...
✓ Uploaded workflow: sub_workflow_1

Workflow upload results:
  ✓ sub_workflow_1

Summary: 1/1 workflows uploaded successfully
```

### How Version Checking Works

The upload system uses a simple version-based approach:

1. **Conductor Version Check**: Verifies the exact workflow version exists in Conductor
2. **Upload Decision**: Only uploads if the specific version is missing

This ensures that:
- Workflows are not re-uploaded unnecessarily
- Missing or new versions are detected and uploaded
- Race conditions during parallel operations are avoided
- Simple and predictable behavior based on version numbers

### When to Upload Workflows

Upload workflows after:
- Creating new workflow files
- Modifying existing workflow definitions
- Starting the Conductor server
- After workflow-related errors

### Workflow Lifecycle

1. **Development**: Create/modify workflow JSON files in `idflow/workflows/`
2. **Upload**: Run `idflow worker upload` to upload to Conductor
3. **Execution**: Workflows are triggered automatically during stage evaluation
4. **Monitoring**: Check workflow status in Conductor UI or via API

## Stage Evaluation and Workflow Triggering

### Automatic Stage Evaluation

Stage evaluation is triggered automatically when:
- A document is saved (if status is "inbox" or "active")
- Manual evaluation via `idflow stage evaluate`
- Workflow completion events

### Workflow Triggering Process

1. **Stage Requirements Check**: Verify if stage requirements are met
2. **Workflow Existence Check**: Warn if required workflows are missing
3. **Workflow Execution**: Start configured workflows via Conductor
4. **Status Updates**: Update stage and document status accordingly

### Missing Workflow Warnings

If workflows are missing during stage evaluation, you'll see warnings like:
```
Warning: Missing workflows: research_blog_post_ideas v2, sub_workflow_1 v2
Run 'idflow worker upload' to upload missing workflows
```

## 🔄 Task-Management Integration

### Vollständige Synchronisation

```bash
# 1. Status prüfen
idflow tasks list --sync
idflow workflow list --conductor

# 2. Tasks synchronisieren
idflow tasks upload --all

# 3. Workflows synchronisieren
idflow workflow upload

# 4. Orphaned Tasks bereinigen
idflow tasks purge --orphaned
```

### Development Workflow

1. **Tasks entwickeln**: Neue Tasks in `idflow/tasks/` erstellen
2. **Tasks testen**: `idflow tasks upload task_name`
3. **Workflows anpassen**: JSON-Dateien in `idflow/workflows/` modifizieren
4. **Workflows testen**: `idflow workflow upload`
5. **Integration testen**: `idflow stage evaluate`

### Production Deployment

1. **Vollständige Sync**: Alle Tasks und Workflows synchronisieren
2. **Orphaned Cleanup**: Nicht mehr benötigte Tasks bereinigen
3. **Worker starten**: `idflow worker start --all`
4. **Monitoring**: Status regelmäßig überprüfen

## Best Practices

### Development Workflow

1. Modify workflow JSON files
2. Test locally with `idflow workflow upload`
3. Verify workflows in Conductor UI
4. Test stage evaluation

### Production Deployment

1. Upload workflows before starting workers
2. Monitor workflow execution
3. Use `--force` flag only when necessary
4. Keep workflow versions in sync

### Troubleshooting

**Workflow not found errors**:
- Run `idflow worker upload` to upload missing workflows
- Check workflow version numbers match
- Verify Conductor server is running

**Database lock errors**:
- Avoid parallel workflow uploads
- Use single upload command instead of multiple parallel operations
- Check Conductor server status

**Stage evaluation not triggering workflows**:
- Ensure workflows are uploaded
- Check stage requirements are met
- Verify document status is "inbox" or "active"

## API Reference

### Workflow Manager

```python
from idflow.core.workflow_manager import get_workflow_manager

workflow_manager = get_workflow_manager()

# Upload all workflows
results = workflow_manager.upload_workflows(force=False)

# Check if specific workflow needs upload
needs_upload = workflow_manager.needs_upload("workflow_name", file_path)
```

### Conductor Client

```python
from idflow.core.conductor_client import start_workflow, search_workflows

# Start a workflow
workflow_id = start_workflow("workflow_name", input_data)

# Search existing workflows
workflows = search_workflows(size=100)
```
