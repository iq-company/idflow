# idflow Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        idflow CLI                              │
├─────────────────────────────────────────────────────────────────┤
│  doc  │  vendor  │  stage  │  worker  │  (future commands)     │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Worker Framework                            │
├─────────────────────────────────────────────────────────────────┤
│  Worker Discovery  │  Task Management  │  Lifecycle Management  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Conductor Integration                         │
├─────────────────────────────────────────────────────────────────┤
│  Workflow Engine  │  Task Orchestration  │  Event Handling     │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Task Workers                                │
├─────────────────────────────────────────────────────────────────┤
│  gpt_researcher  │  duckduckgo_serp  │  create_blog_post_draft │
│  llm_text_complete │  keyword_extract │  (future tasks)        │
└─────────────────────────────────────────────────────────────────┘
```

## Component Relationships

### 1. CLI Layer
- **Main CLI**: `idflow/__main__.py`
- **Worker CLI**: `idflow/cli/worker/worker.py`
- **Stage CLI**: `idflow/cli/stage/evaluate.py`
- **Document CLI**: `idflow/cli/doc/`

### 2. Core Services
- **Document Management**: `idflow/core/document.py`
- **Stage Management**: `idflow/core/stage_definitions.py`
- **Conductor Client**: `idflow/core/conductor_client.py`
- **Workflow Manager**: `idflow/core/workflow_manager.py`

### 3. Task Layer
- **Task Definitions**: `idflow/tasks/{task_name}/`
- **Worker Decorators**: `@worker_task` decorator
- **Task Implementation**: Python functions with Conductor integration

### 4. Workflow Layer
- **Workflow Definitions**: `idflow/workflows/{workflow_name}/`
- **JSON Workflows**: Conductor-compatible workflow definitions
- **JavaScript Tasks**: INLINE tasks for complex logic

## Data Flow

### 1. Document Processing Flow
```
Document Creation → Stage Evaluation → Workflow Trigger → Task Execution → Result Storage
```

### 2. Worker Management Flow
```
Worker Discovery → Task Registration → Polling → Execution → Status Update
```

### 3. Workflow Execution Flow
```
Workflow Start → Task Scheduling → Parallel Execution → Result Consolidation → Completion
```

## Key Design Patterns

### 1. Decorator Pattern
- **Usage**: `@worker_task` decorator for task definitions
- **Benefits**: Declarative task registration, automatic metadata extraction
- **Implementation**: Conductor SDK integration

### 2. Factory Pattern
- **Usage**: Document factory for different ORM implementations
- **Benefits**: Pluggable storage backends
- **Implementation**: `create_document()` function

### 3. Observer Pattern
- **Usage**: Stage completion events
- **Benefits**: Decoupled event handling
- **Implementation**: Conductor event handlers

### 4. Strategy Pattern
- **Usage**: Different research methods (GPT Researcher, DuckDuckGo SERP)
- **Benefits**: Pluggable research strategies
- **Implementation**: Parallel workflow execution

## Configuration Management

### 1. Environment Configuration
- **Conductor Host**: `http://localhost:8080`
- **API Base Path**: `/api`
- **Worker Polling Interval**: 0.1 seconds

### 2. Task Configuration
- **Task Definitions**: Extracted from `@worker_task` decorators
- **Dependencies**: Per-task requirements.txt files
- **Metadata**: Automatic generation from decorators

### 3. Workflow Configuration
- **Workflow Definitions**: JSON files in `idflow/workflows/`
- **Input Parameters**: Defined in workflow JSON
- **Output Parameters**: Result mapping from tasks

## Error Handling Strategy

### 1. Worker Errors
- **Connection Errors**: Retry with exponential backoff
- **Task Execution Errors**: Proper error reporting to Conductor
- **Configuration Errors**: Clear error messages and validation

### 2. Workflow Errors
- **JavaScript Errors**: Try-catch blocks in INLINE tasks
- **Task Dependencies**: Validation of task references
- **Input Validation**: Type checking and required parameters

### 3. System Errors
- **Conductor Unavailable**: Graceful degradation
- **Worker Failures**: Automatic restart and recovery
- **Configuration Issues**: Clear error messages

## Scalability Considerations

### 1. Horizontal Scaling
- **Worker Scaling**: Multiple worker instances
- **Load Distribution**: Conductor's built-in load balancing
- **Resource Management**: Per-worker resource limits

### 2. Vertical Scaling
- **Task Complexity**: Configurable task timeouts
- **Memory Management**: Per-task memory limits
- **CPU Utilization**: Worker process management

### 3. Performance Optimization
- **Task Polling**: Configurable polling intervals
- **Batch Processing**: Grouped task execution
- **Caching**: Result caching for repeated operations

## Security Considerations

### 1. API Security
- **Authentication**: Conductor API authentication
- **Authorization**: Task-level permissions
- **Input Validation**: Sanitization of user inputs

### 2. Data Security
- **Sensitive Data**: Secure handling of API keys
- **Data Encryption**: Encryption in transit and at rest
- **Access Control**: Role-based access control

### 3. Network Security
- **TLS/SSL**: Encrypted communication
- **Firewall Rules**: Network access control
- **Rate Limiting**: API rate limiting

## Monitoring and Observability

### 1. Logging
- **Worker Logs**: Task execution logs
- **Workflow Logs**: Workflow execution traces
- **System Logs**: Infrastructure logs

### 2. Metrics
- **Task Metrics**: Execution time, success rate
- **Workflow Metrics**: Completion rate, error rate
- **System Metrics**: Resource utilization

### 3. Health Checks
- **Worker Health**: Worker process status
- **Conductor Health**: Conductor service status
- **System Health**: Overall system health

## Future Enhancements

### 1. Advanced Features
- **Dynamic Scaling**: Auto-scaling based on load
- **Advanced Scheduling**: Priority-based task scheduling
- **Data Pipeline**: Stream processing capabilities

### 2. Integration Features
- **External APIs**: Integration with external services
- **Database Integration**: Direct database connectivity
- **Message Queues**: Message queue integration

### 3. Developer Experience
- **IDE Integration**: Development tools and plugins
- **Testing Framework**: Comprehensive testing tools
- **Documentation**: Auto-generated documentation

## Conclusion

The idflow architecture provides a robust, scalable foundation for building complex document processing workflows. The design emphasizes modularity, extensibility, and maintainability while providing a user-friendly CLI interface and seamless Conductor integration.

The architecture successfully addresses the core requirements of document management, workflow orchestration, and task execution while providing a solid foundation for future enhancements and scaling.

