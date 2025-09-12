# ID Flow: Gather, Enrich and Publish any Doc to any Kind of Docs (with ID Reference)

**ID Flow** A Document Pipeline System with extendible capabilities to Research, Enrich, QA, Publish with Agentic Support On Prem with local Markdown files.

## 🚀 Quick Start

### Installation

```bash
# For Users (recommended: use virtual environment)
mkdir myproject && cd myproject
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows

pip install idflow

# With Features (optional)
pip install idflow[research,writer]

# For Developers
git clone https://github.com/iq-company/idflow.git
cd idflow

# Create venv
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows

# Install dependencies (editable mode)
pip install -e .
```

### First Steps

```bash
# Initialize current directory
idflow init

# With additional features
idflow init myproject --add-feature research --add-feature writer

# Add document
idflow doc add "My first document"

# List documents
idflow doc list
```

## 📋 Core Features

- **📁 Markdown-first**: All documents as Markdown with YAML frontmatter
- **🆔 ID-based**: Each document has a unique ID as folder name
- **🔄 Workflow Automation**: Conductor-based workflow orchestration
- **⚙️ Configurable**: Selectable ORM implementations (Filesystem/Database)
- **🔧 Extensible**: Modular task and stage architecture
- **💻 CLI Interface**: Comprehensive command-line tools

## 📚 Documentation

### Fundamentals
- **[Architecture Overview](docs/ARCHITECTURE_OVERVIEW.md)** - System architecture and design principles
- **[ORM System](docs/README_ORM.md)** - Document ORM and data model
- **[Requirements System](docs/README_REQUIREMENTS.md)** - Stage requirements and validation

### CLI & Management
- **[CLI Reference](docs/CLI.md)** - Complete CLI documentation
- **[Workflow Management](docs/WORKFLOW_MANAGEMENT.md)** - Workflow orchestration with Conductor
- **[Task Management](docs/TASK_MANAGEMENT.md)** - Task development and management

### Features & Extensions
- **[Research Features](docs/README_RESEARCH_FEATURES.md)** - Web scraping and AI research
- **[Worker Framework](docs/WORKER_FRAMEWORK_DOCUMENTATION.md)** - Conductor worker management
- **[Development](docs/README_dev.md)** - Setup and guidelines for developers

## 🏗️ Architecture

```
┌─────────┐    ┌─────────────┐    ┌─────────┐    ┌──────────┐    ┌─────────┐
│ Gather  │───▶│ Documents   │───▶│ Enrich  │───▶│ Generate │───▶│Publish  │
│         │    │    In       │    │         │    │          │    │         │
└─────────┘    └─────────────┘    └─────────┘    └──────────┘    └─────────┘
```

**Document Lifecycle:**
1. **Gather**: Collect documents from various sources
2. **Enrich**: Add metadata, deduplicate, evaluate
3. **Generate**: Create new content (blog posts, social media, etc.)
4. **Publish**: Distribute content through various channels

## 🎯 Use Cases

| Use Case | Description | Status |
|----------|-------------|--------|
| **Content Marketing** | From social trends to own content pieces | ✅ |
| **Visitor Profiling** | Collect and enrich visitor data | ✅ |
| **Email Management** | Organize emails without privacy concerns | ✅ |
| **Media Analysis** | Analyze and evaluate podcasts, videos | ✅ |
| **Document Processing** | Process PDFs, images with OCR/MLLM | ✅ |

## 🔧 Configuration

```yaml
# config/idflow.yml
base_dir: "data"
config_dir: "config"
document_implementation: "fs_markdown"  # or "database"
conductor_server_url: "http://localhost:8080"
```

## 🚀 Latest Features

### Task Management (New!)
```bash
# List and synchronize tasks
idflow tasks list --sync

# Upload tasks
idflow tasks upload --all

# Clean up orphaned tasks
idflow tasks purge --orphaned
```

### Workflow Management
```bash
# List workflows
idflow workflow list --conductor

# Upload workflows
idflow workflow upload --all
```

## 🤝 Contribute

We welcome contributions! See [Development Guide](README_dev.md) for details.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**ID Flow** - Organize, process and publish documents with ID-based document enrichment.