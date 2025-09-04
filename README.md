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

#### For Users (Production)
```bash
# switch into an isolated directory
mkdir myproject
cd myproject

# global installation:
#   pipx install idflow
#
# or in venv:
python3 -m venv .venv && source .venv/bin/activate
pip install idflow
```

#### For Devs (Development)
```bash
# Clone repo
git clone <repository-url>
cd idflow

# Create venv
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows

# Install dependencies (editable mode)
pip install -e .

# Install test deps (optional)
pip install -e ".[test]"
```

### Running Tests

After installing the dependencies, you can run the test suite:

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run tests with coverage report
pytest --cov=tasks

# Run specific test file
pytest tasks/keyword_extract/test_keyword_extract.py

# Run specific test function
pytest tasks/keyword_extract/test_keyword_extract.py::test_basic_keyword_extraction

# Skip slow tests
pytest -m "not slow"

# Run only integration tests
pytest -m "integration"
```

**Note**: Make sure you're in the project root directory and have activated your virtual environment before running tests.

In the selected target directory run:

```bash
idflow init
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
│  ├─ archived/    # Doc State: Archived - Contains Docs in this state (not relevant anymore)
│  └─ .../
├─ idflow/         # Extensions
|  ├─ workflows/   # Workflow definitions
|  ├─ stages/      # Stage definitions
|  └─ tasks/       # Tasks (Workflow Pieces)
```

Refer to **`Configuration`** for further Details.

---

## CLI

### Document Control

#### Adding new Documents

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

#### Listing Documents

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

#### Manipulating Documents

##### State Changes

```bash
idflow doc set-status uuid active
```

##### Update Values

```bash
echo "new body" | idflow doc modify uuid \
  --set priority=0.8 \
  --list-add tags=observability \
  --add-doc research_source=xyz-2525-f82-... \
  --add-file attachment=./upload.pdf
```

#### Deleting Documents

```bash
# drop a single doc
idflow doc drop uuid

# drop all docs
idflow doc drop-all --force
```

### Change and Extend Functionalities

As described later, it's possible to extend or change existing behaviour (like Flows, Tasks, Pipelines, ...).
The Key is to add own folders/files into the correct folders with the correct names.
To change existing functionalities, the files, which should be extended can be added in the own project, which will
cause to use them instead of the original ones.

To copy a bunch (or all) of the delivered functionality the following commands can be used.

#### Copy extendables to the own project for changes
If just the full functionality should be copied, use `--all`:

```bash
idflow vendor copy --all
```

While copying you'll get prompted for each file, which already exists in your local project to decide if its copy should be overwritten or skipped.

If you want to extend only specific features, call:
```bash
idflow vendor copy
```

This will list the possible directories (containing features), to choose, which ones should be copied / extend.
All files of the directory will be copied. You can discard single files, if you want to rely on the original behaviour for
those files instead.

---

## Architecture

In general the easiest definition of what happens with idflow is:

```
# Adding new Documents
Gather Documents       → State Inbox
Add Documents manually → State Inbox

# Processing Documents
Docs Inbox → Reach `Stages` (like Research, Enrich, Generate, Publish) → State Done

# Stages
A Stage defines a State with a bunch of settings like requirements, start criteria or results.

Requirements can be other Stages, or Property Pattern of the Document (e.g. *tags* should be present and contain "invoice").

The Stage Presence of a Document has its own Status. A Stage Definition may provide additional States.

Each Document may pass many Stages in its lifecycle. The lifecycle itself is not limited by any Stage (with the only exception of a "block" exception in any Stage; this will cause the doc being moved into Status "blocked" to stop any further Processings).
A Documents' Status is typically changed to done from another application layer, or maybe from a scheduled task, which observes age and completed Stages.

```

```
┌─────────┐    ┌─────────────┐    ┌─────────┐    ┌──────────┐    ┌─────────┐
│ Gather  │───▶│ Documents   │───▶│ Enrich  │───▶│ Generate │───▶│Publish  │
│         │    │    In       │    │         │    │          │    │         │
└─────────┘    └─────────────┘    └─────────┘    └──────────┘    └─────────┘
```

**Flow Overview (example, may be configured completely different):**
- **Gather**: Collect documents from various sources (RSS, YouTube, manual input)
- **Enrich**: Many several enrich options, like Adding metadata, deduplication, ranking,  enhancing content, ...
- **Generate**: Create new content pieces as outputs (like blog posts, social media, newsletters)
- **Publish**: Distribute content through various channels (APIs, databases, etc.)

---

## Configuration

TODO:


---

## Stages

A Stage represents a collection of tasks belonging to a document for separate task orchestration in one structured unit.

Each Stage may be invoked in different ways:
- When one of the `trigger` conditions gets true
- It can be requested from a dependent Stage, which was entered
- It can be manually entered (by CLI or from a Task)

### Stage Definition

A Stage Definition consists of a name with several settings to declare dependencies and schedulable workflows.
They rely in ./stages/ project directory, and are all loaded and merged.
So if two stages have the same name, they will be merged, which can lead to unexpected behaviour.

`**stage-name.yml**`
```yaml
name: stage-name
active: true # optional, true by default (option for being disabled)
workflows:
  - name: wf_name
    # version: 1 # opt. a specific version of a workflow
    when: "doc.tags.includes('invoices')"
    # inputs:
    #   ocr_model: "type1"
# Defines requirements/prerequisites, which have to be met before this stage can be entered
# If another Stage needs to have been started before this Stage may be run, this other Stage
# can be *scheduled* or *started* by scheduling this Stage: If a Stage cannot be started due
# to unsolved requirements, it is entered in Status *scheduled*. It's *started* if, or as soon
# as the requirements are fulfilled.
# If a Stage was already *started* (fulfilled requirements), but wasn't processed until *completed*
# or *blocked*, was reached, its Status will be changed to *cancelled*, if the requirements doesn't
# fit anymore.
requirements:
  file_presence:
    key: upload_file
    count: 1
    count_operator: '>='
  stages:
    other_stage_name:
      status: started
# By default each stage may only be entered one single time for each Document.
# If there are use-cases for multiple calls, the ability of multi calls can be set here.
# When set to true, each run will be created in a single folder (with a uuid) within the Stage:
# multiple_callable: false
```

## Tasks and Task Categories

Tasks are the exposed python routines, which will be called/invoked from several stages.

Task Categories just give a semtantic grouping structure and keep its tasks as sub directories.

They will be delivered as core tasks or in further plugins. Tasks also may provide templates and other data, which can be overwritten in specific contents, if the files are located at the same place in the project structure.

The file structure will be the same in the project, in the core or in plugins:

```
task_categories/          # Doc-ID
├─ collectors/            # the Task Category `Collectors`
├─ researchers/           # the Task Category `Researchers`
├─ enrichers/             # the Task Category `Enrichers`
│  └─ seo                 # The Enricher Task "seo"
|     |─ __init__.py      # The task will be expected to be exposed in a generic way
│     |─ seo_task.py      # Sample of task implementation
|     └─ jinja_templates/ # Sample folder for templates
│        └─ result.md.j2  # Main Result template file
├─ generators/            # the Task Category `Generators`
│  └─ blog                # Blog Post Generator Task
|     |─ __init__.py      # The task will be expected to be exposed in a generic way
│     ├─ task.py          # Main Result file
│     └─ utils.py         # Additional file-reference to `newsletter.md`, if this was generated as a result from the Blog Post Generator
```

---

## Pipelines

Decide if a Stage is considered to be a pipeline, or if the pipeline connects several stage results.

---

## Anatomy of a single Document

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

### Document Stages

Each document may run through separate `Stages` due to several Pipelines and Flows, which might generate different further Documents / Results.
These are called `Stages`.
Those `Stages` will be located in the stages/ fs in the Document's directory. The Task Results are grouped within the Document Folder in further sub directories:

FS within `data/STATUS/`:
```
uuid/                             # Doc-ID
├─ doc.md                         # main parameters of the doc
└─ stages/                        # Stages will be located below this folder
   └─ research_for_blog_post/     # Stage Name
      └─ counter/                 # counter for the stage instance (1, 2, 3, ...)
         |─ stage.md              # main parameters of the current stage instance
         └─ researchers/          # Tasks from Category `Researchers`
            |─ deep-research-mit/ # task 1, scheduled in this stage
            |  |─ result.md       # a result definition similiar to doc.md Anatomy
            |  └─ uuid1           # Generated results as file-reference in result.md
            └─ deep-research-gpt/ # task 2
               └─ ...
```

---

## Roadmap

- **SQLite Index** - After each Document Update its Properties should be added into a local sqlite db for an efficient access to data and relationships.
- Get it **installable on Edge Devices** for Win, Mac, Linux to manage and discover data locally, with a GUI and without Docker knowledge (PyInstaller, cx_Freeze, Nuitka)
- Enable Docs to detach file references with s3 instead of keeping them locally in the bundle
- Add ORM Adapters to store docs in DBMS systems instead of the fs

---

## License

idflow is released under the [MIT License](https://opensource.org/licenses/MIT).
