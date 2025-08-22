# ID Flow: Gather, Enrich and Publish any Doc to any Kind of Docs (with ID Reference)

**Markdown-first** – Organizes all Docs (ID based) with Markdown + Frontmatter.

**No Dependencies** – The basic "ORM" deals directly on the filesystem, organized in "ID Bundles" (Doc = Folder, ID = Foldername).
This makes docs versionizable by default with git.

There will be ORM Adapters to connect to other Datasources (like DBMS), for cases, where FS won't match some requirements.

**Modular and Extendible** – Collector (e.g. Newsportals/RSS/YouTube), Enricher (Keywords/Readability/Deduplication), Generators (Blog Post, LinkedIn, Mailing), Publisher (API Calls, DBMS Calls, ...).

**CLI Comfort** – Add and Discover Docs, Start Tasks and Flows, Change Docs States with an easy pip CLI `idflow`.

---

### Use Cases

|Use Case| Description | Yet possible |
|---|---|---|
|1|**From Social Trends to own Content Pieces**| |
||Gather IDs Manually or from Public Trends (YT, Google Trends, RSS, Newsportals) for Marketing Content Pieces| |
||Researches Topics on the Web| |
||Enriches / Deduplicates / Ranks Topic in Context of existing Docs| |
||Generate Blog Posts with related Social (like LinkedIn) and Newsletter Versions. Respects previously generated Research and detected existing docs, for internal References| |
||Revisions the Output for complying with tonality, positioning and further company related pillars| |
|2|**Collect Data From Visitors**| |
||Collect Visitor Profiles with very less Information| |
||Enrich Data after Consens with GeoIP, with CTA Interaction, or other Interactions| |
||Generate Outbound Activities based on reached Stages| |
|3|**Organize and Handle E-Mails without any Privacy Concern**| |
||Gather E-Mails via IMAP| |
||Extract Destination People, Conversations, and Knowledge in separate Docs/IDs (On Premises in Full Control of your Data)| |
||Consider Spam, Delegate or Priority| |
||Enrich Data from other Data Sources (like CRM or ERP System) based on the Mail Inquiry| |
||Generate Drafts based on the collected Knowledge (RAG, GraphRAG) possible with local hosted LLMs.| |
||Gain Insights about your Communication and Data Graphs.| |
|4|**Analyize Media** (like Podcasts)| |
||Gather Episodes as Docs| |
||Extract Topics and Predictions| |
||Enrich with Real World Data| |
||Rank Prediction vs Real World and Publish Results to Publisher Adapters (like DBMS, API Calls, ...)| |
|5|**Handle Images or PDFs**| |
||Gather Files in an FS Folder and register it as Doc ID | |
||Enriches information via OCR and/or MLLM | |
||Enriches a Category based on the Enriched Information| |
||Enriches Document with structured Information based on the Document Category | |
||Publishes Document to other Systems (like ERP, if it was an Invoice for example) | |

---

## Quickstart

### Installation and Setup
```bash
# switch into an isolated directory
mkdir myproject
cd myproject

# global installation:
#   pipx install mdflow
#
# or in venv:
python -m venv .venv && source .venv/bin/activate
pip install mdflow
```

In the selected target directory run:

```bash
mdflow init
```

This will generate some files, like:

```
myproject/
├─ config/
│  ├─ idflow.yml   # The base config
│  └─ brand.yml    # Tone of Voice, Positioning, No-Gos
├─ data/           # Holds all documents in its defined statuses
│  |─ inbox/       # Doc State: Inbox - Contains Docs in this state (initially Gathered or Added)
│  ├─ active/      # Doc State: Active - Contains Docs in this state (further Actions expected)
│  ├─ done/        # Doc State: Done - Contains Docs in this state (no further expected Actions)
│  ├─ blocked/     # Doc State: Blocked - Contains Docs in this state (any flow considered to stop process)
│  |─ archived/    # Doc State: Archived - Contains Docs in this state (not relevant anymore)
│  └─ .../
```

Refer to **`Configuration`** for further Details.

---

## CLI

### Adding new Documents

Command: `idflow add doc [--status inbox]` generates a new Document in status "inbox" (by default) and returns the generated `uuid`.

Adds a new doc with a simple text summary:

```bash
echo "Text Summary" | idflow add doc
```

Adds a new doc with several properties:

```bash
idflow add doc \
  --set title="Observability für LLM-Content-Flows" \
  --set priority=0.72 \
  --list-add tags=observability \
  --list-add tags=llm \
  --json sources='[{"type":"rss","url":"https://..."},{"type":"youtube","id":"..."}]'
```

Adds a new doc with setting dict values:

```bash
idflow add doc --set 'meta.owner=alice' --set 'meta.flags.hot=true'
```

Adds a new doc with files:

```bash
idflow add doc \
  --add-file file_type_ident=./upload.pdf \
  --file-data '{"note":"original upload"}' # opt
```

### Listing Documents

```bash
# only uuids (default)
idflow doc list

# Filters by title with pattern + priority by numerical comparison,
# Outputs Cols id|title|priority|doc-keys
idflow doc list \
  --filter 'title=observ*' \
  --filter 'priority=>0.5' \
  --col id --col title --col priority --col doc-keys
```

### Manipulating Documents

#### State Changes

```bash
idflow doc set-status uuid active
```

#### Update Values

```bash
echo "new body" | idflow doc modify uuid \
  --set priority=0.8 \
  --list-add tags=observability \
  --add-doc research_source=xyz-2525-f82-... \
  --add-file attachment=./upload.pdf
```

### Deleting Documents



---

## Configuration


---

## Events and Pipelines

---

## Anatomy of a single Document ID

Each Document keeps its own folder within the `data/{status}/{uuid}` directory.

There is one main file inside, which holds all the main and meta information of the document:

**`data/inbox/{uuid}/doc.md`**

```yaml
---
id: "7c6e3f1a-9f2b-4f1b-9a0d-2b51f8b0f2d1"
status: "inbox"         # inbox | active | done | blocked | archived

# sample contents: ----------------------
title: "Observability für LLM-Content-Flows"
notes: "Langfuse + Guardrails vergleichen, Praxis-Szenarien"
tags: ["observability","guardrails","llm"]
sources:
  - { type: "rss", url: "https://..." }
  - { type: "youtube", id: "..." }
priority: 0.72
_doc_refs:
  - { key: 'ref_type_ident', uuid: 'xyz-2525-f82-...', data: {} }
_file_refs:
  - { key: 'file_type_ident', filename: 'upload.pdf', uuid: 'zab-2221-f82-...', data: {} }
# end of sample contents ----------------
---
Text Summary
```

Actually only `id` and `status` are considered to be always present.

Further properties may be created dynamically from the Manual Adder (CLI), Gatherer or even the Enrichment Tasks.

### Property Types

| Property Type | Data | Descr |
| --- | --- | --- |
| value | str, float, None, ... | Just a simple Value to be set |
| _doc_refs | list of dict(key, uuid, data) | Establishes Reference to other Documents with a given "key" as association identifier. Additional data can be serialized in optional *data* property. |
| _file_refs | list of dict(key, filename, uuid, data) | Keeps file references with its original filename as data, while only the `uuid` is used as filename for persistence in the document's directory. Additional data can be serialized in optional *data* property. |
| list | list, dict, value | Is a list which may contain other lists, dicts or values as records |
| dict | list, dict, value | Is a dict, which expects string typed keys and values of the types list, dict, value |


---

## Roadmap

- **SQLite Index** - After each Document Update its Properties should be added into a local sqlite db for an efficient access to data and relationships.
- Get it **installable on Edge Devices** for Win, Mac, Linux to manage and discover data locally, with a GUI and without Docker knowledge (PyInstaller, cx_Freeze, Nuitka)

---

## License

idflow is released under the [MIT License](https://opensource.org/licenses/MIT).
