# Dokumentations-Übersicht

Diese Dokumentation ist in thematische Bereiche unterteilt, um die Navigation und das Verständnis zu verbessern.

## 📚 Dokumentationsstruktur

### 🏠 Hauptdokumentation
- **[README.md](../README.md)** - Projektübersicht und Quick Start
- **[Architektur-Übersicht](ARCHITECTURE_OVERVIEW.md)** - Systemarchitektur und Design-Prinzipien

### 🔧 CLI & Management
- **[CLI-Referenz](CLI.md)** - Vollständige Kommandozeilen-Dokumentation
- **[Task-Management](TASK_MANAGEMENT.md)** - Task-Entwicklung und -Synchronisation
- **[Workflow-Management](WORKFLOW_MANAGEMENT.md)** - Workflow-Orchestrierung mit Conductor

### 🏗️ Kern-Systeme
- **[ORM-System](README_ORM.md)** - Dokumenten-ORM und Datenmodell
- **[Requirements-System](README_REQUIREMENTS.md)** - Stage-Requirements und Validierung
- **[Worker-Framework](WORKER_FRAMEWORK_DOCUMENTATION.md)** - Conductor-Worker-Management

### 🚀 Features & Erweiterungen
- **[Research-Features](README_RESEARCH_FEATURES.md)** - Web-Scraping und AI-Research
- **[Entwicklung](README_dev.md)** - Setup und Guidelines für Entwickler

### 📋 Projekt-Management
- **[Changelog](../CHANGELOG.md)** - Versionshistorie und Änderungen
- **[Publishing](PUBLISHING.md)** - Release-Prozess und Veröffentlichung
- **[Version Management](VERSION_MANAGEMENT.md)** - Versionsverwaltung
- **[Changed Files Review](CHANGED_FILES_REVIEW.md)** - Änderungsübersicht

## 🆕 Neue Features

### Task-Management (Neu!)
Das neue Task-Management-System bietet:

- **Bidirektionale Synchronisation**: Lokale ↔ Remote Task-Sync
- **Orphaned Task Cleanup**: Automatische Bereinigung nicht mehr benötigter Tasks
- **Usage-Check**: Sicherheitsprüfung vor Task-Löschung
- **CLI-Integration**: Vollständige Kommandozeilen-Unterstützung

**Hauptkommandos:**
```bash
# Status prüfen
idflow tasks list --sync

# Synchronisieren
idflow tasks upload --all
idflow tasks purge --orphaned
```

### Verbesserte Workflow-Integration
- **WorkflowManager-Erweiterung**: Zentralisierte Workflow- und Task-Verwaltung
- **Automatische Synchronisation**: Intelligente Version-Checks
- **Fehlerbehandlung**: Robuste Error-Recovery-Mechanismen

## 🎯 Schnellstart nach Kategorie

### Für Benutzer
1. [README.md](../README.md) - Projektübersicht
2. [CLI-Referenz](CLI.md) - Kommandozeilen-Tools
3. [Workflow-Management](../WORKFLOW_MANAGEMENT.md) - Workflow-Grundlagen

### Für Entwickler
1. [Entwicklung](../README_dev.md) - Setup und Guidelines
2. [Task-Management](TASK_MANAGEMENT.md) - Task-Entwicklung
3. [Worker-Framework](../WORKER_FRAMEWORK_DOCUMENTATION.md) - Conductor-Integration

### Für System-Administratoren
1. [Architektur-Übersicht](../ARCHITECTURE_OVERVIEW.md) - System-Design
2. [ORM-System](../README_ORM.md) - Datenmodell
3. [Requirements-System](../README_REQUIREMENTS.md) - Validierung

## 🔍 Navigation

### Nach Funktionalität
- **Dokumentenmanagement**: [CLI-Referenz](CLI.md) → `doc` Kommandos
- **Task-Entwicklung**: [Task-Management](TASK_MANAGEMENT.md)
- **Workflow-Orchestrierung**: [Workflow-Management](../WORKFLOW_MANAGEMENT.md)
- **Worker-Management**: [Worker-Framework](../WORKER_FRAMEWORK_DOCUMENTATION.md)

### Nach Komplexität
- **Einfach**: [README.md](../README.md) → [CLI-Referenz](CLI.md)
- **Mittel**: [Workflow-Management](../WORKFLOW_MANAGEMENT.md) → [Task-Management](TASK_MANAGEMENT.md)
- **Fortgeschritten**: [Architektur-Übersicht](../ARCHITECTURE_OVERVIEW.md) → [ORM-System](../README_ORM.md)

## 📝 Dokumentations-Standards

### Struktur
- **Übersicht**: Kurze Einführung in das Thema
- **Grundlagen**: Basis-Konzepte und -Prinzipien
- **Praktische Beispiele**: Code-Beispiele und Use Cases
- **Referenz**: Vollständige API/CLI-Dokumentation
- **Troubleshooting**: Häufige Probleme und Lösungen

### Formatierung
- **Emojis**: Für bessere visuelle Navigation
- **Code-Blöcke**: Syntax-Highlighting für alle Code-Beispiele
- **Links**: Querverweise zwischen verwandten Dokumenten
- **Tabellen**: Für strukturierte Informationen

## 🤝 Beitragen zur Dokumentation

### Verbesserungen vorschlagen
1. Issue erstellen mit Dokumentations-Problem
2. Pull Request mit Verbesserungen
3. Feedback zu bestehender Dokumentation

### Neue Dokumentation
1. Thema identifizieren
2. Struktur nach bestehenden Standards
3. Beispiele und Code-Snippets hinzufügen
4. Links zu verwandten Dokumenten

---

**Hinweis**: Diese Dokumentationsstruktur wird kontinuierlich verbessert. Feedback und Vorschläge sind willkommen!
