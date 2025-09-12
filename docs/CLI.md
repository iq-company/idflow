# CLI Reference

The ID Flow CLI provides comprehensive command-line tools for Dealing with Document Pipelines

## 📋 Overview

```bash
idflow --help
```

### Main Categories

- **`init`** - Project initialization (create project, setup venv)
- **`doc`** - Document management (create, list, edit)
- **`stage`** - Stage management (evaluate, execute)
- **`workflow`** - Workflow management (list, upload)
- **`tasks`** - Task management (list, upload, cleanup)
- **`worker`** - Worker management (start, stop, manage)
- **`vendor`** - Copy and customize extensions

---

## 🚀 Project Initialization (`init`)

### Create New Project

```bash
# Create new project with virtual environment
idflow init myproject

# Create project with features
idflow init myproject --add-feature research --add-feature writer
```

### Initialize Current Directory

```bash
# Initialize current directory (if empty or only contains .venv)
idflow init

# Initialize with features
idflow init --add-feature research --add-feature writer
```

### Smart Installation

The `init` command automatically detects the installation source:

- **🔧 Local Development**: If run within an idflow project directory, it uses the local development version with `pip install -e`
- **📦 PyPI Installation**: If no local idflow project is found, it installs from PyPI

**Examples:**
```bash
# In development environment (automatically uses local idflow)
cd /path/to/idflow
idflow init demo-project

```

### Project Structure

The `init` command creates:

```
myproject/
├── .venv/                    # Virtual environment
├── data/                     # Document storage
│   ├── inbox/               # New documents
│   ├── active/              # Active documents
│   └── done/                # Completed documents
├── config/
│   └── idflow.yml           # Configuration file
├── .gitignore               # Git ignore file
└── README.md                # Project documentation (optional)
```

### Configuration

The generated `config/idflow.yml`:

```yaml
# ID Flow Configuration
base_dir: "data"
config_dir: "config"
document_implementation: "fs_markdown"
conductor_server_url: "http://localhost:8080"
```

---

## 📄 Document Management (`doc`)

### Create Documents

```bash
# Simple document
echo "Text Summary" | idflow doc add

# With properties
idflow doc add \
  --set title="Observability for LLM-Content-Flows" \
  --set priority=0.72 \
  --list-add tags=observability \
  --list-add tags=llm

# With files
idflow doc add \
  --add-file file_type_ident=./upload.pdf \
  --file-data '{"note":"original upload"}'
```

### List Documents

```bash
# Only UUIDs (default)
idflow doc list

# With filters and columns
idflow doc list \
  --filter 'title=observ*' \
  --filter 'priority=>0.5' \
  --col id --col title --col priority --col doc-keys
```

### Edit Documents

```bash
# Change status
idflow doc set-status uuid active

# Update properties
echo "new body" | idflow doc modify uuid \
  --set priority=0.8 \
  --list-add tags=observability \
  --add-doc research_source=xyz-2525-f82-... \
  --add-file attachment=./upload.pdf
```

### Delete Documents

```bash
# Single document
idflow doc drop uuid

# All documents
idflow doc drop-all --force
```

---

## 🔄 Stage Management (`stage`)

### Evaluate Stages

```bash
# Evaluate all stages
idflow stage evaluate

# Evaluate specific stage
idflow stage evaluate --stage research_blog_post_ideas
```

### Execute Stages

```bash
# Manually start stage
idflow stage run --stage research_blog_post_ideas --doc-uuid uuid
```

---

## 🔧 Workflow Management (`workflow`)

### List Workflows

```bash
# Only local workflows (default)
idflow workflow list

# Explicitly only local workflows
idflow workflow list --local

# Local and remote workflows
idflow workflow list --all

# Only remote workflows (only in Conductor)
idflow workflow list --remote

# Without version information
idflow workflow list --no-versions
```

### Upload Workflows

```bash
# Upload all workflows
idflow workflow upload

# With force (ignores version checks)
idflow workflow upload --force

# Upload specific workflow
idflow workflow upload --workflow workflow_name
```

### Prune Unknown/Outdated Workflows

```bash
# Clean up remote workflows (only those that no longer exist locally)
idflow workflow prune

# Clean up specific workflow
idflow workflow prune --workflow workflow_name

# Clean up specific version
idflow workflow prune --workflow workflow_name --version 2

# Dry-run (show only, don't delete)
idflow workflow prune --dry-run

# With force (even with active workflow runs)
idflow workflow prune --force
```

**Safety Checks:**
- Only deletes workflows that no longer exist locally
- Checks for running/pending workflow runs before deletion
- Prevents deletion of active runs (except with `--force`)
- Shows details of active runs
- Confirmation dialog before deletion

---

## ⚙️ Task Management (`tasks`) - **NEW!**

### List Tasks

```bash
# Local and remote tasks
idflow tasks list

# Only local tasks
idflow tasks list --local

# Only remote tasks
idflow tasks list --remote

# Synchronization status
idflow tasks list --sync
```

**Synchronization status shows:**
- Number of local vs. remote tasks
- Tasks only available locally
- Tasks only available remotely
- Common tasks

### Upload Tasks

```bash
# Upload specific task
idflow tasks upload task_name

# Upload all tasks
idflow tasks upload --all

# With force (overwrites existing)
idflow tasks upload --all --force
```

### Clean Up Tasks

```bash
# Delete specific task
idflow tasks purge task_name

# Delete orphaned tasks (only remote, not local)
idflow tasks purge --orphaned

# With force (even if in use)
idflow tasks purge --orphaned --force

# Skip confirmation
idflow tasks purge --orphaned -y
```

**Orphaned Tasks:**
- Tasks that only exist in Conductor, but not locally
- Safety check: Tasks in use are not deleted (except with `--force`)
- Confirmation dialog shows all tasks to be deleted

---

## 👷 Worker Management (`worker`)

### List Workers

```bash
# Show available workers
idflow worker list
```

### Start Workers

```bash
# Start all workers
idflow worker start --all

# Start specific workers
idflow worker start --worker gpt_researcher --worker duckduckgo_serp
```

### Stop Workers

```bash
# Stop all workers
idflow worker killall

# Stop specific worker
idflow worker killall update_stage_status

# With force (SIGKILL)
idflow worker killall --force

# Skip confirmation
idflow worker killall -y
```

---

## 🔧 Extensions (`vendor`)

### Copy Extensions

```bash
# Copy all extensions
idflow vendor copy --all

# Interactive selection
idflow vendor copy
```

---

## 🎯 Practical Examples

### Content Pipeline

```bash
# 1. Create document
echo "AI Trends 2024" | idflow doc add --set title="AI Trends 2024" --list-add tags=research

# 2. Synchronize tasks
idflow tasks list --sync
idflow tasks upload --all

# 3. Upload workflows
idflow workflow upload

# 4. Start workers
idflow worker start --all

# 5. Evaluate stages
idflow stage evaluate
```

### Cleanup Workflow

```bash
# 1. Check workflows
idflow workflow list --remote

# 2. Identify orphaned tasks
idflow tasks list --sync

# 3. Clean up orphaned tasks
idflow tasks purge --orphaned

# 4. Clean up orphaned workflows
idflow workflow prune --dry-run
idflow workflow prune

# 5. Check status
idflow workflow list --remote
idflow tasks list --sync
```

### Development Workflow

```bash
# 1. Copy extensions
idflow vendor copy --all

# 2. Test local changes
idflow tasks upload --all --force
idflow workflow upload --force

# 3. Test workers
idflow worker start --all
```

---

## 🔍 Troubleshooting

### Common Issues

**Tasks not found:**
```bash
# Synchronize tasks
idflow tasks upload --all
```

**Workflows not found:**
```bash
# Upload workflows
idflow workflow upload
```

**Worker won't start:**
```bash
# Check Conductor status
curl http://localhost:8080/api/health

# Check worker status
idflow worker list
```

**Orphaned Tasks:**
```bash
# Check status
idflow tasks list --sync

# Clean up
idflow tasks purge --orphaned
```

**Orphaned Workflows:**
```bash
# Check status
idflow workflow list --remote

# Check dry-run
idflow workflow prune --dry-run

# Clean up
idflow workflow prune
```

**Active Workflow Runs:**
```bash
# Check workflows with active runs
idflow workflow prune --dry-run

# Delete with force (caution!)
idflow workflow prune --force
```

### Debug Information

```bash
# Detailed output
idflow tasks list --sync --verbose

# Force mode for troubleshooting
idflow tasks upload --all --force
idflow workflow upload --force
```

---

## 📚 Further Information

- **[Workflow Management](WORKFLOW_MANAGEMENT.md)** - Detailed workflow documentation
- **[Task Management](TASK_MANAGEMENT.md)** - Task development and management
- **[Worker Framework](WORKER_FRAMEWORK_DOCUMENTATION.md)** - Conductor worker details