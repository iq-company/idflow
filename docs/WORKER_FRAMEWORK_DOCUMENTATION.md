# idflow Worker Framework Documentation

## Overview

This document describes the worker framework and CLI infrastructure created for the idflow project. The framework provides a complete solution for managing Conductor task workers, including discovery, execution, and lifecycle management.

## Architecture

### Core Components

1. **Worker CLI Module** (`idflow/cli/worker/`)
2. **Conductor Client** (`idflow/core/conductor_client.py`)
3. **Workflow Manager** (`idflow/core/workflow_manager.py`)
4. **Task Definitions** (`idflow/tasks/`)
5. **Workflow Definitions** (`idflow/workflows/`)

### Worker Framework

The worker framework is built on top of the Conductor Python SDK and provides:

- **Automatic Worker Discovery**: Scans for `@worker_task` decorated functions
- **Task Lifecycle Management**: Handles task polling, execution, and status updates
- **CLI Interface**: Complete command-line interface for worker management
- **Conductor Integration**: Seamless integration with Conductor orchestration engine

## File Structure

```
idflow/
├── cli/
│   └── worker/
│       ├── __init__.py          # Worker CLI module exports
│       └── worker.py            # Main worker CLI implementation
├── core/
│   ├── conductor_client.py      # Conductor API client
│   └── workflow_manager.py      # Workflow and task management
├── tasks/                       # Task implementations
│   ├── gpt_researcher/
│   ├── duckduckgo_serp/
│   ├── create_blog_post_draft/
│   └── ...
└── workflows/                   # Workflow definitions
    ├── research_blog_post_ideas/
    ├── create_blog_post_draft/
    └── ...
```

## Key Files

### 1. Worker CLI (`idflow/cli/worker/worker.py`)

**Purpose**: Main CLI interface for worker management

**Key Features**:
- `list` command: Lists all available task workers
- `start` command: Starts workers using Conductor SDK
- `upload` command: Uploads workflows to Conductor

**Implementation Details**:
- Uses `conductor.client.automator.task_handler.TaskHandler` for worker management
- Automatic worker discovery via `scan_for_annotated_workers=True`
- Signal handling for graceful shutdown
- Configuration management for Conductor connection

**Usage**:
```bash
# List available workers
idflow worker list

# Start all workers
idflow worker start --all

# Start specific workers
idflow worker start --worker gpt_researcher --worker duckduckgo_serp

# Upload workflows and tasks
idflow worker upload
```

### 2. Conductor Client (`idflow/core/conductor_client.py`)

**Purpose**: Python client for Conductor API interaction

**Key Features**:
- Workflow management (start, get status, search)
- Task definition management
- Direct API calls for complex operations
- Error handling and retry logic

**API Methods**:
- `start_workflow(workflow_name, input_data)`
- `get_workflow_status(workflow_id)`
- `upload_workflow(workflow_definition)`
- `upload_task_definition(task_definition)`

### 3. Workflow Manager (`idflow/core/workflow_manager.py`)

**Purpose**: Manages workflow and task definitions

**Key Features**:
- Loads workflow definitions from JSON files
- Loads task definitions from Python files
- Uploads definitions to Conductor
- Handles metadata and validation

**Workflow Loading**:
- Scans `idflow/workflows/` directory
- Loads JSON workflow definitions
- Validates required fields (name, version, tasks)

**Task Loading**:
- Scans `idflow/tasks/` directory
- Extracts task definitions from `@worker_task` decorators
- Generates Conductor-compatible task definitions

### 4. Task Implementations

**Location**: `idflow/tasks/{task_name}/`

**Structure**:
```
idflow/tasks/gpt_researcher/
├── gpt_researcher.py    # Main task implementation
└── requirements.txt     # Task-specific dependencies
```

**Task Implementation Pattern**:
```python
from conductor.client.worker.worker_task import worker_task

@worker_task(task_definition_name='gpt_researcher')
def gpt_researcher(task_input):
    # Task implementation
    return {'result': 'success'}
```

### 5. Workflow Definitions

**Location**: `idflow/workflows/{workflow_name}/`

**Structure**:
```
idflow/workflows/research_blog_post_ideas/
├── research_blog_post_ideas.json    # Workflow definition
└── requirements.txt                 # Workflow dependencies
```

**Workflow Definition Pattern**:
```json
{
  "name": "workflow_name",
  "version": 1,
  "schemaVersion": 2,
  "inputParameters": ["param1", "param2"],
  "tasks": [
    {
      "name": "task_name",
      "taskReferenceName": "task_ref",
      "type": "SIMPLE",
      "inputParameters": {
        "param": "${workflow.input.param1}"
      }
    }
  ],
  "outputParameters": {
    "result": "${task_ref.output.result}"
  },
  "ownerEmail": "idflow@example.com"
}
```

## CLI Integration

### Main CLI (`idflow/__main__.py`)

The worker CLI is integrated into the main idflow CLI:

```python
from idflow.cli.worker import app as worker_app

# Register worker commands
app.add_typer(worker_app, name="worker", help="Manage Conductor task workers")
```

### CLI Commands

| Command | Description |
|---------|-------------|
| `idflow worker list` | List all available task workers |
| `idflow worker start --all` | Start all available workers |
| `idflow worker start --worker <name>` | Start specific workers |
| `idflow worker upload` | Upload workflows and tasks to Conductor |

## Configuration

### Conductor Connection

The framework connects to Conductor using the following configuration:

```python
config = Configuration()
config.host = 'http://localhost:8080'
config.base_path = '/api'
```

### Worker Configuration

Workers are configured with:
- **Polling Interval**: 0.1 seconds (configurable)
- **Domain**: None (global domain)
- **Auto-discovery**: Enabled for `@worker_task` decorated functions

## Task Lifecycle

1. **Discovery**: Framework scans for `@worker_task` decorated functions
2. **Registration**: Task definitions are uploaded to Conductor
3. **Polling**: Workers poll Conductor for available tasks
4. **Execution**: Tasks are executed when available
5. **Status Update**: Task status is updated in Conductor
6. **Completion**: Results are returned to the workflow

## Error Handling

### Worker Errors
- **Connection Errors**: Retry logic with exponential backoff
- **Task Execution Errors**: Proper error reporting to Conductor
- **Configuration Errors**: Clear error messages and validation

### Workflow Errors
- **JavaScript Errors**: Proper error handling in INLINE tasks
- **Task Dependencies**: Validation of task references
- **Input Validation**: Type checking and required parameter validation

## Testing

### Test Commands

```bash
# Test worker discovery
idflow worker list

# Test worker startup
idflow worker start --all

# Test workflow execution
curl -X POST "http://localhost:8080/api/workflow/direct_task_workflow" \
  -H "Content-Type: application/json" \
  -d '{"docId": "test-1"}'
```

### Test Workflows

- **`direct_task_workflow`**: Simple workflow for testing basic functionality
- **`research_blog_post_ideas`**: Complex workflow with parallel tasks and JavaScript

## Dependencies

### Core Dependencies
- `conductor-python`: Conductor Python SDK
- `typer`: CLI framework
- `requests`: HTTP client
- `pydantic`: Data validation

### Task Dependencies
- `gpt-researcher`: AI research tool
- `playwright`: Web automation
- `duckduckgo-search`: Search API

## Future Enhancements

### Planned Features
1. **Worker Scaling**: Dynamic worker scaling based on load
2. **Health Monitoring**: Worker health checks and monitoring
3. **Task Queuing**: Priority-based task queuing
4. **Metrics Collection**: Performance metrics and analytics
5. **Configuration Management**: External configuration files

### Workflow Improvements
1. **Error Recovery**: Automatic retry and recovery mechanisms
2. **Conditional Logic**: More sophisticated workflow control flow
3. **Data Transformation**: Built-in data transformation capabilities
4. **Integration Testing**: Comprehensive workflow testing framework

## Troubleshooting

### Common Issues

1. **Worker Connection Errors**
   - Check Conductor server status
   - Verify network connectivity
   - Check configuration settings

2. **Task Execution Failures**
   - Check task dependencies
   - Verify input parameters
   - Review error logs

3. **Workflow Failures**
   - Check JavaScript syntax in INLINE tasks
   - Verify task references
   - Review workflow definition

### Debug Commands

```bash
# Check worker status
ps aux | grep "idflow worker"

# Check Conductor status
curl http://localhost:8080/api/health

# List running workflows
curl http://localhost:8080/api/workflow/search?size=10
```

## Conclusion

The idflow worker framework provides a robust, scalable solution for managing Conductor task workers. It combines the power of the Conductor orchestration engine with a user-friendly CLI interface and automatic worker discovery, making it easy to build and manage complex workflows.

The framework is designed to be extensible and maintainable, with clear separation of concerns and comprehensive error handling. It provides a solid foundation for building sophisticated document processing workflows.
