# Workflow Management

## Overview

IdFlow uses Conductor for workflow orchestration. Workflows are defined as JSON files in the `idflow/workflows/` directory and need to be uploaded to Conductor before they can be executed.

## Workflow Upload Strategy

### Automatic vs Manual Upload

**Important**: Workflows are NOT automatically uploaded during stage evaluation to avoid race conditions and database locks. Instead, they should be uploaded manually using the CLI command.

### Manual Upload Command

```bash
# Upload all workflows (with version checking)
idflow worker upload

# Force upload all workflows (ignores version checks)
idflow worker upload --force

# Upload specific workflow
idflow worker upload --workflow workflow_name

# Force upload specific workflow
idflow worker upload --workflow workflow_name --force
```

### List Workflows Command

```bash
# List both local and Conductor workflows (default)
idflow worker list

# List only local workflow files
idflow worker list --local

# List only workflows in Conductor
idflow worker list --conductor

# Explicitly list both (same as default)
idflow worker list --all
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

## Best Practices

### Development Workflow

1. Modify workflow JSON files
2. Test locally with `idflow worker upload`
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
