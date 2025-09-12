# Documentation Overview

This documentation is organized into thematic areas to improve navigation and understanding.

## 📚 Documentation Structure

### 🏠 Main Documentation
- **[README.md](../README.md)** - Project overview and quick start
- **[Architecture Overview](ARCHITECTURE_OVERVIEW.md)** - System architecture and design principles

### 🔧 CLI & Management
- **[CLI Reference](CLI.md)** - Complete command-line documentation
- **[Task Management](TASK_MANAGEMENT.md)** - Task development and synchronization
- **[Workflow Management](WORKFLOW_MANAGEMENT.md)** - Workflow orchestration with Conductor

### 🏗️ Core Systems
- **[ORM System](README_ORM.md)** - Document ORM and data model
- **[Requirements System](README_REQUIREMENTS.md)** - Stage requirements and validation
- **[Worker Framework](WORKER_FRAMEWORK_DOCUMENTATION.md)** - Conductor worker management

### 🚀 Features & Extensions
- **[Research Features](README_RESEARCH_FEATURES.md)** - Web scraping and AI research
- **[Development](README_dev.md)** - Setup and guidelines for developers

### 📋 Project Management
- **[Changelog](../CHANGELOG.md)** - Version history and changes
- **[Publishing](PUBLISHING.md)** - Release process and publication
- **[Version Management](VERSION_MANAGEMENT.md)** - Version management
- **[Changed Files Review](CHANGED_FILES_REVIEW.md)** - Change overview

## 🆕 New Features

### Task Management (New!)
The new task management system offers:

- **Bidirectional Synchronization**: Local ↔ Remote task sync
- **Orphaned Task Cleanup**: Automatic cleanup of no longer needed tasks
- **Usage Check**: Safety check before task deletion
- **CLI Integration**: Complete command-line support

**Main commands:**
```bash
# Check status
idflow tasks list --sync

# Synchronize
idflow tasks upload --all
idflow tasks purge --orphaned
```

### Improved Workflow Integration
- **WorkflowManager Extension**: Centralized workflow and task management
- **Automatic Synchronization**: Intelligent version checks
- **Error Handling**: Robust error recovery mechanisms

## 🎯 Quick Start by Category

### For Users
1. [README.md](../README.md) - Project overview
2. [CLI Reference](CLI.md) - Command-line tools
3. [Workflow Management](../WORKFLOW_MANAGEMENT.md) - Workflow basics

### For Developers
1. [Development](../README_dev.md) - Setup and guidelines
2. [Task Management](TASK_MANAGEMENT.md) - Task development
3. [Worker Framework](../WORKER_FRAMEWORK_DOCUMENTATION.md) - Conductor integration

### For System Administrators
1. [Architecture Overview](../ARCHITECTURE_OVERVIEW.md) - System design
2. [ORM System](../README_ORM.md) - Data model
3. [Requirements System](../README_REQUIREMENTS.md) - Validation

## 🔍 Navigation

### By Functionality
- **Document Management**: [CLI Reference](CLI.md) → `doc` commands
- **Task Development**: [Task Management](TASK_MANAGEMENT.md)
- **Workflow Orchestration**: [Workflow Management](../WORKFLOW_MANAGEMENT.md)
- **Worker Management**: [Worker Framework](../WORKER_FRAMEWORK_DOCUMENTATION.md)

### By Complexity
- **Simple**: [README.md](../README.md) → [CLI Reference](CLI.md)
- **Intermediate**: [Workflow Management](../WORKFLOW_MANAGEMENT.md) → [Task Management](TASK_MANAGEMENT.md)
- **Advanced**: [Architecture Overview](../ARCHITECTURE_OVERVIEW.md) → [ORM System](../README_ORM.md)

## 📝 Documentation Standards

### Structure
- **Overview**: Brief introduction to the topic
- **Fundamentals**: Basic concepts and principles
- **Practical Examples**: Code examples and use cases
- **Reference**: Complete API/CLI documentation
- **Troubleshooting**: Common problems and solutions

### Formatting
- **Emojis**: For better visual navigation
- **Code Blocks**: Syntax highlighting for all code examples
- **Links**: Cross-references between related documents
- **Tables**: For structured information

## 🤝 Contributing to Documentation

### Suggest Improvements
1. Create issue with documentation problem
2. Pull request with improvements
3. Feedback on existing documentation

### New Documentation
1. Identify topic
2. Structure according to existing standards
3. Add examples and code snippets
4. Link to related documents

---

**Note**: This documentation structure is continuously improved. Feedback and suggestions are welcome!