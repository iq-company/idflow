import typer
from .copy import copy_vendor

app = typer.Typer(add_completion=False)
app.command("copy")(copy_vendor)

# Usage:
# ===
# # 1) interaktive Auswahl einer Quelle
# idflow vendor copy
# 
# # 2) alle erlaubten Verzeichnisse in das aktuelle Projekt kopieren
# idflow vendor copy --all
# 
# # 3) in anderes Zielverzeichnis
# idflow vendor copy --dest ./my-project
# Beim Kopieren wirst du pro bestehender Datei gefragt:
# O → überschreiben
# S → überspringen
# A → gesamten Vorgang abbrechen

# Story Desc
# erstelle einen weiteren cli ordner für sowas wie sync/vendor/copy (oder besseren vorschlag?) um in das Verzeichnis, in dem `idflow` aufgerufen wird, Dateien aus dem pip Folder zu kopieren (um Projektspezifische Änderungen vorzunehmen). 
# 
# Z.B. werden mit dem pip Ordner wie pipelines, tasks, prompts ausgeliefert. 
# 
# Diese werden dann durch die Konfiguration im Projektverzeichnis verwendet.
# 
# Wenn für das Projekt aber einzelne Files ergänzt werden sollen, sollen diese durch FS-Strukturgleichheit im Projekt überdefiniert werden können.
# 
# In dem cli Befehl soll eine Konstante definiert werden, in der die Verzeichnisse aufgezählt werden, die eben ins lokale Projekt kopiert werden können.
# 
# Z.B.
# tasks/
# templates/researcher
# templates/enricher
# templates/generator
# 
# Durch diese Definition möchte ich verhindern, dass einfach "alle" templates genommen werden "müssen" (wie bei tasks), sondern gehe auf eine mögliche feingranularere Struktur ein.
# 
# Der neue CLI Befehl soll entweder "--all" als Parameter haben (dann werden alle Verzeichnisse kopiert), oder nicht, dann sollen die möglichen Verzeichnisse nummeriert dargestellt werden, sodass der User die Zahl für einen Ordner via Prompt angeben kann, um den gewünschten Ordner ins Projektverzeichnis zu kopieren.
# 
# Sind bereits files vorhanden, soll je File gefragt werden, ob überschrieben oder abgebrochen werden soll.

