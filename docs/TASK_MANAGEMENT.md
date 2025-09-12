# Task Management

The task management system enables the development, synchronization, and management of Conductor tasks.

## 📋 Overview

Tasks are the executable components in ID Flow workflows. They are implemented as Python functions and automatically converted to Conductor task definitions.

## 🏗️ Task Architecture

### Task Structure

```
idflow/tasks/
├── task_name/
│   ├── __init__.py
│   ├── task_name.py          # Main implementation
│   └── requirements.txt      # Task-specific dependencies (optional)
```

### Task Implementation

```python
from conductor.client.worker.worker_task import worker_task

@worker_task(task_definition_name='my_task')
def my_task(task_input):
    """
    Task implementation

    Args:
        task_input: Dictionary with input parameters

    Returns:
        Dictionary with result data
    """
    # Task logic here
    result = {
        'status': 'success',
        'data': 'processed_data',
        'message': 'Task completed successfully'
    }

    return result
```

## 🔧 Task Management CLI

### List Tasks

```bash
# All tasks (local and remote)
idflow tasks list

# Only local tasks
idflow tasks list --local

# Only remote tasks
idflow tasks list --remote

# Synchronization status
idflow tasks list --sync
```

**Synchronization status shows:**
- **Local Tasks**: Tasks in `idflow/tasks/` directory
- **Remote Tasks**: Tasks registered in Conductor
- **Common Tasks**: Tasks available locally and remotely
- **Local Only**: Tasks only available locally (need to be uploaded)
- **Remote Only**: Orphaned tasks (only remote, not local)

### Upload Tasks

```bash
# Upload specific task
idflow tasks upload task_name

# Upload all tasks
idflow tasks upload --all

# With force (overwrites existing)
idflow tasks upload --all --force
```

**Upload behavior:**
- Automatic task definition generation from `@worker_task` decorator
- Version checking (only new/changed tasks are uploaded)
- Error handling for invalid task definitions

### Clean Up Tasks

```bash
# Delete specific task
idflow tasks purge task_name

# Delete orphaned tasks
idflow tasks purge --orphaned

# With force (even if in use)
idflow tasks purge --orphaned --force

# Skip confirmation
idflow tasks purge --orphaned -y
```

**Safety features:**
- **Usage Check**: Tasks in workflows are not deleted (except with `--force`)
- **Confirmation Dialog**: Shows all tasks to be deleted before execution
- **Orphaned Only**: Only deletes tasks that are not locally available

## 🛠️ Task Development

### Create New Task

1. **Create directory:**
```bash
mkdir -p idflow/tasks/my_new_task
```

2. **Implement task:**
```python
# idflow/tasks/my_new_task/my_new_task.py
from conductor.client.worker.worker_task import worker_task

@worker_task(task_definition_name='my_new_task')
def my_new_task(task_input):
    # Task implementation
    return {'result': 'success'}
```

3. **Upload task:**
```bash
idflow tasks upload my_new_task
```

### Customize Task Definition

The automatically generated task definition can be customized through parameters in the `@worker_task` decorator:

```python
@worker_task(
    task_definition_name='my_task',
    retry_count=5,
    timeout_seconds=1200,
    timeout_policy='TIME_OUT_WF',
    retry_logic='FIXED',
    retry_delay_seconds=60,
    response_timeout_seconds=300,
    concurrent_exec_limit=50,
    rate_limit_frequency_in_seconds=1,
    rate_limit_per_frequency=10
)
def my_task(task_input):
    return {'result': 'success'}
```

### Task Dependencies

For tasks with special dependencies:

```bash
# requirements.txt in task directory
echo "requests>=2.31.0" > idflow/tasks/my_task/requirements.txt
echo "beautifulsoup4>=4.12.0" >> idflow/tasks/my_task/requirements.txt
```

## 🔄 Synchronization

### Local → Remote

```bash
# Check status
idflow tasks list --sync

# Upload missing tasks
idflow tasks upload --all
```

### Remote → Local (Cleanup)

```bash
# Identify orphaned tasks
idflow tasks list --sync

# Clean up orphaned tasks
idflow tasks purge --orphaned
```

### Bidirectional Synchronization

```bash
# Complete synchronization
idflow tasks list --sync
idflow tasks upload --all
idflow tasks purge --orphaned
```

## 🧪 Testing

### Test Task

```bash
# Test task locally
python -c "
from idflow.tasks.my_task.my_task import my_task
result = my_task({'input': 'test'})
print(result)
"
```

### Test Task in Workflow

```bash
# Start workers
idflow worker start --all

# Execute workflow with task
idflow stage run --stage my_stage --doc-uuid test-uuid
```

## 📊 Monitoring

### Monitor Task Status

```bash
# Local tasks
idflow tasks list --local

# Remote tasks
idflow tasks list --remote

# Synchronization status
idflow tasks list --sync
```

### Task Performance

```bash
# Conductor UI
open http://localhost:8080

# API queries
curl http://localhost:8080/api/metadata/taskdefs
```

## 🔧 Configuration

### Task Manager Configuration

```python
# idflow/core/workflow_manager.py
class WorkflowManager:
    def __init__(self, workflows_dir=None, tasks_dir=None):
        self.workflows_dir = workflows_dir or Path("idflow/workflows")
        self.tasks_dir = tasks_dir or Path("idflow/tasks")
```

### Conductor Configuration

```yaml
# config/idflow.yml
conductor_server_url: "http://localhost:8080"
conductor_api_key_env_var: "CONDUCTOR_API_KEY"
```

## 🚨 Troubleshooting

### Common Issues

**Task not recognized:**
```bash
# Check @worker_task decorator
grep -r "@worker_task" idflow/tasks/my_task/

# Validate task definition
idflow tasks upload my_task --verbose
```

**Upload errors:**
```bash
# Check Conductor connection
curl http://localhost:8080/api/health

# Check API key
echo $CONDUCTOR_API_KEY
```

**Task in use:**
```bash
# Bypass usage check (caution!)
idflow tasks purge task_name --force
```

**Synchronization issues:**
```bash
# Complete re-synchronization
idflow tasks upload --all --force
idflow tasks purge --orphaned --force
```

### Debug Modes

```bash
# Verbose output
idflow tasks list --sync --verbose

# Force mode
idflow tasks upload --all --force
```

## 📚 Best Practices

### Task Development

1. **Small, focused tasks**: One task per function
2. **Robust error handling**: Try-catch for all external dependencies
3. **Clear return values**: Structured JSON responses
4. **Documentation**: Docstrings for all parameters and return values

### Synchronization

1. **Regular syncs**: Always synchronize after changes
2. **Orphaned cleanup**: Regular cleanup of no longer needed tasks
3. **Version control**: Track task changes in Git
4. **Testing**: Test tasks before upload

### Production

1. **Backup**: Backup important task definitions
2. **Monitoring**: Monitor task performance
3. **Rollback plan**: Be able to quickly revert in case of problems
4. **Documentation**: Document task purpose and usage

## 🔗 Related Documentation

- **[CLI Reference](CLI.md)** - Complete CLI documentation
- **[Workflow Management](WORKFLOW_MANAGEMENT.md)** - Workflow orchestration
- **[Worker Framework](WORKER_FRAMEWORK_DOCUMENTATION.md)** - Conductor worker details
- **[Research Features](README_RESEARCH_FEATURES.md)** - Web scraping and AI research