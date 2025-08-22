import typer
from .add import add
from .list import list_docs
from .modify import modify
from .set_status import set_status
from .drop import drop
from .drop_all import drop_all

app = typer.Typer(add_completion=False)
app.command("add")(add)
app.command("list")(list_docs)
app.command("modify")(modify)
app.command("set-status")(set_status)
app.command("drop")(drop)
app.command("drop-all")(drop_all)

# Story desc:
# Erstelle mit Typer ein python cli, das Werte entgegennimmt um "Documents" (markdown + frontmatter) zu verwalten.
#
# Basisbefehl `idflow add doc` sollte ein leeres Document erstellen (mit default Status "inbox" und einer generierten uuid als id)
# in data/inbox/uuid/doc.md
# Innerhalb dieser Dateien sollen aber nahezu beliebige Properties mit definiert werden können:
# ### Property Types | Property Type | Data | Descr |
# | --- | --- | --- |
# | value | str, float, None, ... | Just a simple Value to be set |
# | _doc_refs | list of dict(key, uuid, data) | Establishes Reference to other Documents with a given "key" as association identifier. Additional data can be serialized in optional *data* property. |
# | _file_refs | list of dict(key, filename, uuid, data) | Keeps file references with its original filename as data, while only the uuid is used as filename for persistence in the document's directory. Additional data can be serialized in optional *data* property. |
# | list | list, dict, value | Is a list which may contain other lists, dicts or values as records |
# | dict | list, dict, value | Is a dict, which expects string typed keys and values of the types list, dict, value |
#
# Bsp Datei:
# ```yaml
# ---
# id: "7c6e3f1a-9f2b-4f1b-9a0d-2b51f8b0f2d1"
# status: "inbox"         # inbox | active | done | blocked | archived
#
# # sample contents: ----------------------
# title: "Observability für LLM-Content-Flows"
# notes: "Langfuse + Guardrails vergleichen, Praxis-Szenarien"
# tags: ["observability","guardrails","llm"]
# sources:
#   - { type: "rss", url: "https://..." }
#   - { type: "youtube", id: "..." }
# priority: 0.72
# _doc_refs:
#   - { key: 'ref_type_ident', uuid: 'xyz-2525-f82-...', data: {} }
# _file_refs:
#   - { key: 'file_type_ident', filename: 'upload.pdf', uuid: 'zab-2221-f82-...', data: {} }
# # end of sample contents ----------------
# ---
# Text Summary
# ````
# Die Property Types sollen mit Typer realisiert werden.
#
# Samples:
#
# Leeres Doc + Body via stdin
#
# `echo "Text Summary" | idflow add doc``
#
#
# Properties (property=…), lists and json
# ```bash
# idflow add doc \
#   --set title="Observability für LLM-Content-Flows" \
#   --set priority=0.72 \
#   --list-add tags=observability \
#   --list-add tags=llm \
#   --json sources='[{"type":"rss","url":"https://..."},{"type":"youtube","id":"..."}]'
# ```
#
#
# Dot-Paths generates Structures
# `idflow add doc --set 'meta.owner=alice' --set 'meta.flags.hot=true' `
#
# Doc-Refs (key is obligatory, doc-data optional)
#
# ```bash
# idflow add doc \
#   --add-doc research_source=xyz-2525-f82-... \
#   --doc-data '{"role":"source"}'
# ```
#
#
# File-Refs (key is obligatory, file-data optional)
#
# ```bash
# idflow add doc \
#   --add-file file_type_ident=./upload.pdf \
#   --file-data '{"note":"original upload"}'
# ```
#
#
# Erstelle folgende weitere cli `idflow doc` Befehle:
# - list
#   hierbei sollten filter gesetzt werden können, wie z.b. --filter title="observ*" --filter priority=">0.5"
#   In der Ausgabe wird per default nur die uuid je zeile ausgegeben.
#   Die einzelnen Properties sollen aber definierbar sein (z.B. --col title).
#   Für die Spezialfelder refs und docs zählt nur, ob es zum übermittelten filter key eine oder mehrere Einträge gibt.
#   In der Ausgabe sollen alle keys "," separiert dargestellt werden
# - set-status Statusänderung
# - modify hierbei sollen weitere werte gesetzt werden können (via set, list-add, ...).
# - drop übergabe einer einzelnen uuid zum Löschen
# - drop-all mit extra prompt (oder opt. --force)
