# ID Flow: Gather, Enrich and Publish any Doc to any Kind of Docs (with ID Reference)

**ID Flow** A Document Pipeline System with extendible capabilities to Research, Enrich, QA, Publish with Agentic Support On Prem with local Markdown files.

## 🚀 Quick Start

### Installation

```bash
# For User (production)
pip install idflow

# Mit Research-Features (optional)
pip install idflow[research]

# For Devs
git clone https://github.com/iq-company/idflow.git
cd idflow

# Create venv
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows

# Install dependencies (editable mode)
pip install -e .
```

### Erste Schritte

```bash
# Projekt initialisieren
mkdir myproject && cd myproject
idflow init

# Dokument hinzufügen
echo "Mein erstes Dokument" | idflow doc add

# Dokumente auflisten
idflow doc list
```

## 📋 Kernfunktionen

- **📁 Markdown-first**: Alle Dokumente als Markdown mit YAML-Frontmatter
- **🆔 ID-basiert**: Jedes Dokument hat eine eindeutige ID als Ordnername
- **🔄 Workflow-Automatisierung**: Conductor-basierte Workflow-Orchestrierung
- **⚙️ Konfigurierbar**: Wählbare ORM-Implementierungen (Filesystem/Database)
- **🔧 Erweiterbar**: Modulare Task- und Stage-Architektur
- **💻 CLI-Interface**: Umfassende Kommandozeilen-Tools

## 📚 Dokumentation

### Grundlagen
- **[Architektur-Übersicht](docs/ARCHITECTURE_OVERVIEW.md)** - Systemarchitektur und Design-Prinzipien
- **[ORM-System](docs/README_ORM.md)** - Dokumenten-ORM und Datenmodell
- **[Requirements-System](docs/README_REQUIREMENTS.md)** - Stage-Requirements und Validierung

### CLI & Management
- **[CLI-Referenz](docs/CLI.md)** - Vollständige CLI-Dokumentation
- **[Workflow-Management](docs/WORKFLOW_MANAGEMENT.md)** - Workflow-Orchestrierung mit Conductor
- **[Task-Management](docs/TASK_MANAGEMENT.md)** - Task-Entwicklung und -Management

### Features & Erweiterungen
- **[Research-Features](docs/README_RESEARCH_FEATURES.md)** - Web-Scraping und AI-Research
- **[Worker-Framework](docs/WORKER_FRAMEWORK_DOCUMENTATION.md)** - Conductor-Worker-Management
- **[Entwicklung](docs/README_dev.md)** - Setup und Guidelines für Entwickler

## 🏗️ Architektur

```
┌─────────┐    ┌─────────────┐    ┌─────────┐    ┌──────────┐    ┌─────────┐
│ Gather  │───▶│ Documents   │───▶│ Enrich  │───▶│ Generate │───▶│Publish  │
│         │    │    In       │    │         │    │          │    │         │
└─────────┘    └─────────────┘    └─────────┘    └──────────┘    └─────────┘
```

**Dokumenten-Lebenszyklus:**
1. **Gather**: Dokumente aus verschiedenen Quellen sammeln
2. **Enrich**: Metadaten hinzufügen, deduplizieren, bewerten
3. **Generate**: Neue Inhalte erstellen (Blog-Posts, Social Media, etc.)
4. **Publish**: Inhalte über verschiedene Kanäle verteilen

## 🎯 Use Cases

| Use Case | Beschreibung | Status |
|----------|-------------|--------|
| **Content-Marketing** | Von Social Trends zu eigenen Content-Pieces | ✅ |
| **Visitor-Profiling** | Besucherdaten sammeln und anreichern | ✅ |
| **E-Mail-Management** | E-Mails organisieren ohne Datenschutz-Bedenken | ✅ |
| **Media-Analyse** | Podcasts, Videos analysieren und bewerten | ✅ |
| **Dokumenten-Verarbeitung** | PDFs, Bilder mit OCR/MLLM verarbeiten | ✅ |

## 🔧 Konfiguration

```yaml
# config/idflow.yml
base_dir: "data"
config_dir: "config"
document_implementation: "fs_markdown"  # oder "database"
conductor_server_url: "http://localhost:8080"
```

## 🚀 Neueste Features

### Task-Management (Neu!)
```bash
# Tasks auflisten und synchronisieren
idflow tasks list --sync

# Tasks hochladen
idflow tasks upload --all

# Orphaned Tasks bereinigen
idflow tasks purge --orphaned
```

### Workflow-Management
```bash
# Workflows auflisten
idflow workflow list --conductor

# Workflows hochladen
idflow workflow upload --all
```

## 🤝 Contribute

Wir freuen uns über Beiträge! Siehe [Entwicklungs-Guide](README_dev.md) für Details.

## 📄 Lizenz

MIT License - siehe [LICENSE](LICENSE) für Details.

---

**ID Flow** - Organisiere, verarbeite und publiziere Dokumente mit ID-basierter Doc Anreicherung.