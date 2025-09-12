# CLI Reference

Die ID Flow CLI bietet umfassende Kommandozeilen-Tools für alle Aspekte des Dokumentenmanagements.

## 📋 Übersicht

```bash
idflow --help
```

### Hauptkategorien

- **`doc`** - Dokumentenmanagement (erstellen, auflisten, bearbeiten)
- **`stage`** - Stage-Management (evaluieren, ausführen)
- **`workflow`** - Workflow-Management (auflisten, hochladen)
- **`tasks`** - Task-Management (auflisten, hochladen, bereinigen)
- **`worker`** - Worker-Management (starten, stoppen, verwalten)
- **`vendor`** - Erweiterungen kopieren und anpassen

---

## 📄 Dokumentenmanagement (`doc`)

### Dokumente erstellen

```bash
# Einfaches Dokument
echo "Text Summary" | idflow doc add

# Mit Eigenschaften
idflow doc add \
  --set title="Observability für LLM-Content-Flows" \
  --set priority=0.72 \
  --list-add tags=observability \
  --list-add tags=llm

# Mit Dateien
idflow doc add \
  --add-file file_type_ident=./upload.pdf \
  --file-data '{"note":"original upload"}'
```

### Dokumente auflisten

```bash
# Nur UUIDs (Standard)
idflow doc list

# Mit Filtern und Spalten
idflow doc list \
  --filter 'title=observ*' \
  --filter 'priority=>0.5' \
  --col id --col title --col priority --col doc-keys
```

### Dokumente bearbeiten

```bash
# Status ändern
idflow doc set-status uuid active

# Eigenschaften aktualisieren
echo "new body" | idflow doc modify uuid \
  --set priority=0.8 \
  --list-add tags=observability \
  --add-doc research_source=xyz-2525-f82-... \
  --add-file attachment=./upload.pdf
```

### Dokumente löschen

```bash
# Einzelnes Dokument
idflow doc drop uuid

# Alle Dokumente
idflow doc drop-all --force
```

---

## 🔄 Stage-Management (`stage`)

### Stage evaluieren

```bash
# Alle Stages evaluieren
idflow stage evaluate

# Spezifische Stage evaluieren
idflow stage evaluate --stage research_blog_post_ideas
```

### Stage ausführen

```bash
# Stage manuell starten
idflow stage run --stage research_blog_post_ideas --doc-uuid uuid
```

---

## 🔧 Workflow-Management (`workflow`)

### Workflows auflisten

```bash
# Lokale und Remote-Workflows
idflow workflow list

# Nur lokale Workflows
idflow workflow list --local

# Nur Remote-Workflows
idflow workflow list --conductor

# Beide explizit
idflow workflow list --all
```

### Workflows hochladen

```bash
# Alle Workflows hochladen
idflow workflow upload

# Mit Force (ignoriert Version-Checks)
idflow workflow upload --force

# Spezifischen Workflow hochladen
idflow workflow upload --workflow workflow_name
```

---

## ⚙️ Task-Management (`tasks`) - **NEU!**

### Tasks auflisten

```bash
# Lokale und Remote-Tasks
idflow tasks list

# Nur lokale Tasks
idflow tasks list --local

# Nur Remote-Tasks
idflow tasks list --remote

# Synchronisationsstatus
idflow tasks list --sync
```

**Synchronisationsstatus zeigt:**
- Anzahl lokaler vs. Remote-Tasks
- Tasks nur lokal verfügbar
- Tasks nur remote verfügbar
- Gemeinsame Tasks

### Tasks hochladen

```bash
# Spezifischen Task hochladen
idflow tasks upload task_name

# Alle Tasks hochladen
idflow tasks upload --all

# Mit Force (überschreibt existierende)
idflow tasks upload --all --force
```

### Tasks bereinigen

```bash
# Spezifischen Task löschen
idflow tasks purge task_name

# Orphaned Tasks löschen (nur remote, nicht lokal)
idflow tasks purge --orphaned

# Mit Force (auch wenn in Nutzung)
idflow tasks purge --orphaned --force

# Bestätigung überspringen
idflow tasks purge --orphaned -y
```

**Orphaned Tasks:**
- Tasks die nur in Conductor existieren, aber nicht lokal
- Sicherheitscheck: Tasks in Nutzung werden nicht gelöscht (außer mit `--force`)
- Bestätigungsdialog zeigt alle zu löschenden Tasks

---

## 👷 Worker-Management (`worker`)

### Worker auflisten

```bash
# Verfügbare Worker anzeigen
idflow worker list
```

### Worker starten

```bash
# Alle Worker starten
idflow worker start --all

# Spezifische Worker starten
idflow worker start --worker gpt_researcher --worker duckduckgo_serp
```

### Worker stoppen

```bash
# Alle Worker stoppen
idflow worker killall

# Spezifischen Worker stoppen
idflow worker killall update_stage_status

# Mit Force (SIGKILL)
idflow worker killall --force

# Bestätigung überspringen
idflow worker killall -y
```

---

## 🔧 Erweiterungen (`vendor`)

### Erweiterungen kopieren

```bash
# Alle Erweiterungen kopieren
idflow vendor copy --all

# Interaktiv auswählen
idflow vendor copy
```

---

## 🎯 Praktische Beispiele

### Content-Pipeline

```bash
# 1. Dokument erstellen
echo "AI Trends 2024" | idflow doc add --set title="AI Trends 2024" --list-add tags=research

# 2. Tasks synchronisieren
idflow tasks list --sync
idflow tasks upload --all

# 3. Workflows hochladen
idflow workflow upload

# 4. Worker starten
idflow worker start --all

# 5. Stage evaluieren
idflow stage evaluate
```

### Cleanup-Workflow

```bash
# 1. Orphaned Tasks identifizieren
idflow tasks list --sync

# 2. Orphaned Tasks bereinigen
idflow tasks purge --orphaned

# 3. Status überprüfen
idflow tasks list --sync
```

### Development-Workflow

```bash
# 1. Erweiterungen kopieren
idflow vendor copy --all

# 2. Lokale Änderungen testen
idflow tasks upload --all --force
idflow workflow upload --force

# 3. Worker testen
idflow worker start --all
```

---

## 🔍 Troubleshooting

### Häufige Probleme

**Tasks nicht gefunden:**
```bash
# Tasks synchronisieren
idflow tasks upload --all
```

**Workflows nicht gefunden:**
```bash
# Workflows hochladen
idflow workflow upload
```

**Worker startet nicht:**
```bash
# Conductor-Status prüfen
curl http://localhost:8080/api/health

# Worker-Status prüfen
idflow worker list
```

**Orphaned Tasks:**
```bash
# Status prüfen
idflow tasks list --sync

# Bereinigen
idflow tasks purge --orphaned
```

### Debug-Informationen

```bash
# Detaillierte Ausgabe
idflow tasks list --sync --verbose

# Force-Modus für Problembehebung
idflow tasks upload --all --force
idflow workflow upload --force
```

---

## 📚 Weitere Informationen

- **[Workflow-Management](WORKFLOW_MANAGEMENT.md)** - Detaillierte Workflow-Dokumentation
- **[Task-Management](TASK_MANAGEMENT.md)** - Task-Entwicklung und -Management
- **[Worker-Framework](WORKER_FRAMEWORK_DOCUMENTATION.md)** - Conductor-Worker-Details
