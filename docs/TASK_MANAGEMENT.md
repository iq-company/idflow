# Task Management

Das Task-Management-System ermöglicht die Entwicklung, Synchronisation und Verwaltung von Conductor-Tasks.

## 📋 Übersicht

Tasks sind die ausführbaren Komponenten in ID Flow Workflows. Sie werden als Python-Funktionen implementiert und automatisch zu Conductor-Task-Definitionen konvertiert.

## 🏗️ Task-Architektur

### Task-Struktur

```
idflow/tasks/
├── task_name/
│   ├── __init__.py
│   ├── task_name.py          # Hauptimplementierung
│   └── requirements.txt      # Task-spezifische Dependencies (optional)
```

### Task-Implementierung

```python
from conductor.client.worker.worker_task import worker_task

@worker_task(task_definition_name='my_task')
def my_task(task_input):
    """
    Task-Implementierung

    Args:
        task_input: Dictionary mit Eingabeparametern

    Returns:
        Dictionary mit Ergebnisdaten
    """
    # Task-Logik hier
    result = {
        'status': 'success',
        'data': 'processed_data',
        'message': 'Task completed successfully'
    }

    return result
```

## 🔧 Task-Management CLI

### Tasks auflisten

```bash
# Alle Tasks (lokal und remote)
idflow tasks list

# Nur lokale Tasks
idflow tasks list --local

# Nur Remote-Tasks
idflow tasks list --remote

# Synchronisationsstatus
idflow tasks list --sync
```

**Synchronisationsstatus zeigt:**
- **Lokale Tasks**: Tasks in `idflow/tasks/` Verzeichnis
- **Remote Tasks**: Tasks in Conductor registriert
- **Gemeinsame Tasks**: Tasks verfügbar lokal und remote
- **Nur lokal**: Tasks nur lokal verfügbar (müssen hochgeladen werden)
- **Nur remote**: Orphaned Tasks (nur remote, nicht lokal)

### Tasks hochladen

```bash
# Spezifischen Task hochladen
idflow tasks upload task_name

# Alle Tasks hochladen
idflow tasks upload --all

# Mit Force (überschreibt existierende)
idflow tasks upload --all --force
```

**Upload-Verhalten:**
- Automatische Task-Definition-Generierung aus `@worker_task` Decorator
- Version-Checking (nur neue/geänderte Tasks werden hochgeladen)
- Fehlerbehandlung für ungültige Task-Definitionen

### Tasks bereinigen

```bash
# Spezifischen Task löschen
idflow tasks purge task_name

# Orphaned Tasks löschen
idflow tasks purge --orphaned

# Mit Force (auch wenn in Nutzung)
idflow tasks purge --orphaned --force

# Bestätigung überspringen
idflow tasks purge --orphaned -y
```

**Sicherheitsfeatures:**
- **Usage-Check**: Tasks in Workflows werden nicht gelöscht (außer mit `--force`)
- **Bestätigungsdialog**: Zeigt alle zu löschenden Tasks vor der Ausführung
- **Orphaned-Only**: Löscht nur Tasks die nicht lokal verfügbar sind

## 🛠️ Task-Entwicklung

### Neue Task erstellen

1. **Verzeichnis erstellen:**
```bash
mkdir -p idflow/tasks/my_new_task
```

2. **Task implementieren:**
```python
# idflow/tasks/my_new_task/my_new_task.py
from conductor.client.worker.worker_task import worker_task

@worker_task(task_definition_name='my_new_task')
def my_new_task(task_input):
    # Task-Implementierung
    return {'result': 'success'}
```

3. **Task hochladen:**
```bash
idflow tasks upload my_new_task
```

### Task-Definition anpassen

Die automatisch generierte Task-Definition kann durch Parameter im `@worker_task` Decorator angepasst werden:

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

### Task-Dependencies

Für Tasks mit speziellen Dependencies:

```bash
# requirements.txt in Task-Verzeichnis
echo "requests>=2.31.0" > idflow/tasks/my_task/requirements.txt
echo "beautifulsoup4>=4.12.0" >> idflow/tasks/my_task/requirements.txt
```

## 🔄 Synchronisation

### Lokal → Remote

```bash
# Status prüfen
idflow tasks list --sync

# Fehlende Tasks hochladen
idflow tasks upload --all
```

### Remote → Lokal (Cleanup)

```bash
# Orphaned Tasks identifizieren
idflow tasks list --sync

# Orphaned Tasks bereinigen
idflow tasks purge --orphaned
```

### Bidirektionale Synchronisation

```bash
# Vollständige Synchronisation
idflow tasks list --sync
idflow tasks upload --all
idflow tasks purge --orphaned
```

## 🧪 Testing

### Task testen

```bash
# Task lokal testen
python -c "
from idflow.tasks.my_task.my_task import my_task
result = my_task({'input': 'test'})
print(result)
"
```

### Task in Workflow testen

```bash
# Worker starten
idflow worker start --all

# Workflow mit Task ausführen
idflow stage run --stage my_stage --doc-uuid test-uuid
```

## 📊 Monitoring

### Task-Status überwachen

```bash
# Lokale Tasks
idflow tasks list --local

# Remote-Tasks
idflow tasks list --remote

# Synchronisationsstatus
idflow tasks list --sync
```

### Task-Performance

```bash
# Conductor UI
open http://localhost:8080

# API-Abfragen
curl http://localhost:8080/api/metadata/taskdefs
```

## 🔧 Konfiguration

### Task-Manager Konfiguration

```python
# idflow/core/workflow_manager.py
class WorkflowManager:
    def __init__(self, workflows_dir=None, tasks_dir=None):
        self.workflows_dir = workflows_dir or Path("idflow/workflows")
        self.tasks_dir = tasks_dir or Path("idflow/tasks")
```

### Conductor-Konfiguration

```yaml
# config/idflow.yml
conductor_server_url: "http://localhost:8080"
conductor_api_key_env_var: "CONDUCTOR_API_KEY"
```

## 🚨 Troubleshooting

### Häufige Probleme

**Task wird nicht erkannt:**
```bash
# @worker_task Decorator prüfen
grep -r "@worker_task" idflow/tasks/my_task/

# Task-Definition validieren
idflow tasks upload my_task --verbose
```

**Upload-Fehler:**
```bash
# Conductor-Verbindung prüfen
curl http://localhost:8080/api/health

# API-Key prüfen
echo $CONDUCTOR_API_KEY
```

**Task in Nutzung:**
```bash
# Usage-Check umgehen (Vorsicht!)
idflow tasks purge task_name --force
```

**Synchronisationsprobleme:**
```bash
# Vollständige Neu-Synchronisation
idflow tasks upload --all --force
idflow tasks purge --orphaned --force
```

### Debug-Modi

```bash
# Verbose-Ausgabe
idflow tasks list --sync --verbose

# Force-Modus
idflow tasks upload --all --force
```

## 📚 Best Practices

### Task-Entwicklung

1. **Kleine, fokussierte Tasks**: Eine Aufgabe pro Task
2. **Robuste Fehlerbehandlung**: Try-catch für alle externen Abhängigkeiten
3. **Klare Rückgabewerte**: Strukturierte JSON-Responses
4. **Dokumentation**: Docstrings für alle Parameter und Rückgabewerte

### Synchronisation

1. **Regelmäßige Syncs**: Nach Änderungen immer synchronisieren
2. **Orphaned Cleanup**: Regelmäßige Bereinigung nicht mehr benötigter Tasks
3. **Version Control**: Task-Änderungen in Git verfolgen
4. **Testing**: Tasks vor Upload testen

### Production

1. **Backup**: Wichtige Task-Definitionen sichern
2. **Monitoring**: Task-Performance überwachen
3. **Rollback-Plan**: Bei Problemen schnell zurücksetzen können
4. **Dokumentation**: Task-Zweck und -Verwendung dokumentieren

## 🔗 Verwandte Dokumentation

- **[CLI-Referenz](CLI.md)** - Vollständige CLI-Dokumentation
- **[Workflow-Management](WORKFLOW_MANAGEMENT.md)** - Workflow-Orchestrierung
- **[Worker-Framework](WORKER_FRAMEWORK_DOCUMENTATION.md)** - Conductor-Worker-Details
- **[Research-Features](README_RESEARCH_FEATURES.md)** - Web-Scraping und AI-Research
