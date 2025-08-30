import typer
from .add import add
from .list import list_docs
from .modify import modify
from .set_status import set_status
from .drop import drop
from .drop_all import drop_all
from .locate import locate
from .show import show

app = typer.Typer(add_completion=False)
app.command("add")(add)
app.command("list")(list_docs)
app.command("modify")(modify)
app.command("set-status")(set_status)
app.command("drop")(drop)
app.command("drop-all")(drop_all)
app.command("locate")(locate)
app.command("show")(show)

# Story desc:
# Create a python cli with Typer that accepts values to manage "Documents" (markdown + frontmatter).
#
# Base command `idflow add doc` should create an empty document (with default status "inbox" and a generated uuid as id)
# in data/inbox/uuid/doc.md
# Within these files, almost arbitrary properties should be definable:
# ### Property Types | Property Type | Data | Descr |
# | --- | --- | --- |
# | value | str, float, None, ... | Just a simple Value to be set |
# | _doc_refs | list of dict(key, uuid, data) | Establishes Reference to other Documents with a given "key" as association identifier. Additional data can be serialized in optional *data* property. |
# | _file_refs | list of dict(key, filename, uuid, data) | Keeps file references with its original filename as data, while only the uuid is used as filename for persistence in the document's directory. Additional data can be serialized in optional *data* property. |
# | list | list, dict, value | Is a list which may contain other lists, dicts or values as records |
# | dict | list, dict, value | Is a dict, which expects string typed keys and values of the types list, dict, value |
#
# Example file:
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
# The Property Types should be implemented with Typer.
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
# Create the following additional cli `idflow doc` commands:
# - list
#   here filters should be settable, e.g. --filter title="observ*" --filter priority=">0.5"
#   In the output, only the uuid per line is output by default.
#   The individual properties should be definable (e.g. --col title).
#   For the special fields refs and docs, only whether there is one or more entries for the transmitted filter key counts.
#   In the output, all keys should be displayed separated by ","
# - set-status status change
# - modify here further values should be settable (via set, list-add, ...).
# - drop pass a single uuid for deletion
# - drop-all with extra prompt (or opt. --force)
