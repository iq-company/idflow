# baker-cli

Ein kleines, pragmatisches Python-CLI, das deine Docker-Build-Kaskaden **einheitlich lokal und im CI** steuert:

* **Targets & Bundles** werden in **YAML** definiert
* **Tags** entstehen per **Checksum** (self / self+deps) *oder* per **Expressions** (ENV, Dateien, Git-SHA, …)
* **Nur bauen, wenn nötig**: Existenzcheck lokal oder in der Registry
* Erzeugt auf Wunsch ein **`docker-bake.hcl`** und baut via **`docker buildx bake`**
* **Build-Args** sind definierbar, werden interpoliert und **fließen in den Hash** ein
* Konfigurationswerte lassen sich **per CLI überschreiben** (`--set key=value`)

---

## Inhalt

* [Quickstart](#quickstart)
* [Voraussetzungen](#voraussetzungen)
* [Repository-Layout](#repository-layout)
* [Konfiguration (`build-settings.yml`)](#konfiguration-build-settingsyml)

  * [Targets](#targets)
  * [Bundles](#bundles)
  * [Interpolation & Expressions](#interpolation--expressions)
  * [Tag-Expressions (Funktionen)](#tag-expressions-funktionen)
  * [Build-Args & Hashing](#build-args--hashing)
* [CLI](#cli)

  * [`plan`](#plan)
  * [`gen-hcl`](#gen-hcl)
  * [`build`](#build)
  * [Globale Overrides (`--set`)](#globale-overrides---set)
* [Existenzcheck & Push-Strategie](#existenzcheck--push-strategie)
* [GitHub Actions Beispiel](#github-actions-beispiel)
* [Tipps & Best Practices](#tipps--best-practices)
* [Troubleshooting](#troubleshooting)
* [Sicherheitshinweise](#sicherheitshinweise)

---

## Quickstart

```bash
# 1) Abhängigkeit
pip install pyyaml

# 2) Plan anzeigen (lokal prüfen, ohne Push)
python baker.py --settings build-settings.yml plan --check local --push=off --targets cascade-base

# 3) Bauen (lokal, ohne Push)
python baker.py --settings build-settings.yml build --check local --push=off --targets cascade-base

# 4) Optional: HCL generieren
python baker.py --settings build-settings.yml gen-hcl -o docker-bake.hcl
```

---

## Voraussetzungen

* **Python** 3.10+
* **Docker** mit **Buildx** (`docker buildx version`)
* Für Remote-Checks/Push: Login zur Registry (z. B. GHCR)

  ```bash
  echo $GITHUB_TOKEN | docker login ghcr.io -u <OWNER> --password-stdin
  ```

---

## Repository-Layout

```
.
├─ baker.py
├─ build-settings.yml
└─ conductor/
   ├─ Dockerfile.base
   ├─ sqlite/Dockerfile
   ├─ ui/Dockerfile
   └─ Dockerfile.sqlite
```

---

## Konfiguration (`build-settings.yml`)

### Minimalbeispiel

```yaml
registry: ${env("REGISTRY","ghcr.io")}
owner:    ${env("OWNER", env("GITHUB_REPOSITORY_OWNER",""))}
push: ${env("PUSH","true")}     # "true"/"false" (wird zu bool konvertiert)
check: auto                     # auto | local | remote
platforms: ["linux/amd64"]
builder: ""
namespace_prefix: ""
hash:
  tag_length: 8

targets:
  conductor-base:
    dockerfile: conductor/Dockerfile.base
    context: .
    deps: []
    hash_mode: self
    image: conductor-base
    latest: true
    build_args:
      BASE_ALPINE: "3.20"
      GIT_SHA: ${gitShortSha()}
    # Optional: expliziter Tag (sonst currentChecksum())
    # tag: ${readFile("conductor/base-version.txt") or currentChecksum()}

  builder-sqlite:
    dockerfile: conductor/sqlite/Dockerfile
    context: .
    deps: [conductor-base]
    hash_mode: self
    image: builder-sqlite
    latest: true
    build_args:
      SQLITE_VERSION: ${env("SQLITE_VERSION","3.46")}
    tag: ${env("SQLITE_BUILDER_VERSION","dev")}-${gitShortSha()}

  builder-ui:
    dockerfile: conductor/ui/Dockerfile
    context: .
    deps: [conductor-base]
    hash_mode: self
    image: builder-ui
    latest: true
    build_args:
      VITE_API_BASE: https://api.example.com
    tag: ${readFile("conductor/ui/version.txt")}-${currentChecksum()}

  srv-sqlite:
    dockerfile: conductor/Dockerfile.sqlite
    context: .
    deps: [conductor-base, builder-sqlite, builder-ui]
    hash_mode: self+deps
    image: srv-sqlite
    latest: true
    build_args:
      RUNTIME_USER: "10001"
    tag: ${readFile("container-version.txt")}-${currentChecksum()}

bundles:
  cascade-base: [conductor-base, builder-sqlite, builder-ui, srv-sqlite]
  cascade-sqlite-builder: [builder-sqlite, srv-sqlite]
  cascade-ui-builder: [builder-ui, srv-sqlite]
```

### Targets

Felder pro Target:

| Feld         | Typ                  | Pflicht             | Beschreibung                                                                     |
| ------------ | -------------------- | ------------------- | -------------------------------------------------------------------------------- |
| `dockerfile` | string               | ✔                   | Pfad zur Dockerfile                                                              |
| `context`    | string               | – (.)               | Build-Context                                                                    |
| `deps`       | list<string>         | – (\[])             | Abhängigkeiten (andere Targets)                                                  |
| `hash_mode`  | `self` / `self+deps` | – (`self`)          | Bestimmt, ob der Hash nur die eigenen Dateien/Args umfasst oder inkl. Dep-Hashes |
| `hash_files` | list<string>         | – (\[`dockerfile`]) | Dateien für den Self-Hash                                                        |
| `image`      | string               | – (Name)            | Imagename ohne Registry/Owner                                                    |
| `latest`     | bool                 | – (false)           | Zusätzlich `:latest` taggen                                                      |
| `build_args` | map\<string, string> | – ({})              | Build-Args (werden interpoliert & gehasht)                                       |
| `tag`        | string/expression    | –                   | Optionaler Tag; ansonsten wird der berechnete Hash verwendet                     |

### Bundles

Einfache Name-→Targetliste-Gruppierungen für bequeme Auswahl in CLI/CI.

---

### Interpolation & Expressions

* **Globale Interpolation**: In allen Strings sind `${...}` erlaubt (z. B. `registry`, `owner`, `build_args`-Werte).
* **Tag-Expressions**: Zusätzlich target-spezifische Funktionen (siehe unten).

#### Globale Funktionen

* `env("VAR","default")` – liest Umgebungsvariable
* `readFile("path")` – Dateiinhalt (getrimmt)
* `checksum("file1","file2",...)` – SHA256 über Datei-Inhalte
* `gitShortSha()` – `git rev-parse --short HEAD` (Fallback `nogit`)
* `concat(a,b,...)` – Stringverkettung

> Ergebnis wird auf zulässige Docker-Tag-Zeichen normalisiert (`[A-Za-z0-9_.-]`).

### Tag-Expressions (Funktionen)

Nur in `tag:` (oder in Strings, die `${...}` enthalten, innerhalb eines Targets):

* `currentChecksum()` – der für dieses Target berechnete Hash (je nach `hash_mode`)
* `depChecksum("targetName")` – Hash eines anderen Targets

Beispiele:

```yaml
tag: ${readFile("container-version.txt")}-${currentChecksum()}
tag: ${env("REL_TAG","dev")}-${gitShortSha()}
tag: ${depChecksum("builder-ui")}-${currentChecksum()}
```

### Build-Args & Hashing

* `build_args` werden **nach Interpolation** deterministisch in den **Self-Hash** aufgenommen (sorted `ARG KEY=VALUE`).
* Änderungen an Build-Args → neuer Hash → neues Tag (sofern `tag:` nicht explizit etwas anderes vorgibt).
* **Hinweis zu Secrets**: Geheimnisse nicht als Build-Arg hashen; nutze stattdessen Docker Build **Secrets**.

---

## CLI

```text
usage: baker.py [--settings build-settings.yml] [--set key=VAL] {plan,gen-hcl,build} [...]
```

### `plan`

Zeigt Entscheidung (bauen/skip), Tags und Referenzen. Baut nichts.

```bash
python baker.py \
  --settings build-settings.yml \
  plan \
  --targets cascade-base \
  --check remote \
  --print-env
```

Nützliche Flags:

* `--targets <name|bundle> ...`
* `--force <target> ...` – auch bauen, wenn Tag existiert
* `--skip <target> ...` – auslassen
* `--end <target> ...` – Planung endet bei diesem Target
* `--check auto|local|remote`
* `--push on|off` – nur als Plan-Signal (beeinflusst `auto`-Check)
* `--json` – maschinenlesbare Ausgabe
* `--print-env` – druckt `TAG_<TARGET>` Variablen (für CI)

### `gen-hcl`

Erzeugt ein `docker-bake.hcl` basierend auf Settings + berechneten Tags.

```bash
python baker.py --settings build-settings.yml gen-hcl -o docker-bake.hcl --targets cascade-base
```

### `build`

Baut (und optional pusht) nur die Targets, die laut Plan nötig sind.

```bash
python baker.py \
  --settings build-settings.yml \
  build \
  --targets cascade-base \
  --check remote \
  --push
```

### Globale Overrides (`--set`)

Überschreibt beliebige Settings per **Dot-Notation**:

```bash
# Push erzwingen
--set push=true

# Registry/Owner überschreiben
--set registry=ghcr.io --set owner=my-user

# Platforms als JSON
--set 'platforms=["linux/amd64","linux/arm64"]'

# latest für ein Target deaktivieren
--set targets.srv-sqlite.latest=false

# Build-Arg ändern
--set targets.builder-ui.build_args.VITE_API_BASE=https://staging.example.com
```

Parsing-Regeln:

* `true/false/1/0/yes/no/on/off` → Bool
* JSON (`[...]`, `{...}`, `"..."`, Zahl) → geparst
* `a,b,c` → Liste
* sonst String

---

## Existenzcheck & Push-Strategie

* **Check lokal**: `docker image inspect <ref>`
* **Check remote**: `docker buildx imagetools inspect <ref>`
* `check: auto` wählt:

  * **remote**, wenn `push: true`
  * **local**, wenn `push: false`
* Übersteuerbar per CLI: `--check local|remote`
* **Push**:

  * aus `build-settings.yml` (`push:`), interpolierbar (`${env("PUSH","true")}`)
  * oder per CLI `--push` / `--push=off`
  * beim Build: `--push` Flag wird an `buildx bake` übergeben

---

## GitHub Actions Beispiel

```yaml
name: Build Conductor

on:
  push:
    branches: [ main ]
    paths:
      - conductor/**/Dockerfile*
      - build-settings.yml
      - baker.py

permissions:
  contents: read
  packages: write

env:
  REGISTRY: ghcr.io
  OWNER: ${{ github.repository_owner }}
  # optional: beeinflusst YAML-Interpolation (push:)
  PUSH: ${{ github.ref == 'refs/heads/main' && 'true' || 'false' }}

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ env.OWNER }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Python deps
        run: pipx run pip install pyyaml

      - name: Plan (remote check)
        run: |
          python baker.py \
            --settings build-settings.yml \
            plan \
            --set check=remote \
            --targets cascade-base \
            --print-env

      - name: Build & Push (nur wenn nötig)
        run: |
          python baker.py \
            --settings build-settings.yml \
            build \
            --set check=remote \
            --set push=${{ github.ref == 'refs/heads/main' }} \
            --targets cascade-base
```

---

## Tipps & Best Practices

* **Versionen aus Dateien**: Pflege `container-version.txt` & Co., kombiniere mit `currentChecksum()`:

  ```yaml
  tag: ${readFile("container-version.txt")}-${currentChecksum()}
  ```
* **Monorepo**: Nutze `namespace_prefix`, um Namen zu präfixen.
* **Multi-Arch**:

  ```bash
  --set 'platforms=["linux/amd64","linux/arm64"]'
  ```
* **Gezielt bauen**:

  ```bash
  # nur UI-Kette
  python baker.py build --targets cascade-ui-builder
  ```

---

## Troubleshooting

* **`docker buildx imagetools` nicht gefunden**
  → Buildx installieren/aktivieren: `docker buildx create --use`
* **`FileNotFoundError` bei `hash_files`**
  → Pfad korrigieren oder Datei anlegen.
* **Tag enthält unerlaubte Zeichen**
  → Tags werden automatisch normalisiert. Prüfe deine Expressions.
* **Remote-Check schlägt fehl (401/403)**
  → Registry-Login prüfen (Token/Permissions).
* **Nichts wird gebaut, obwohl ich will**
  → `--force <target>` verwenden.

---

## Sicherheitshinweise

* **Secrets** nicht als `build_args` hashen (ändern sonst den Tag und landen evtl. im Image-Layer).
  Nutze **Build Secrets** (`--secret` in Docker) für wirklich geheime Werte.
* **Tag-Inhalte** aus Dateien/ENVs sind öffentlich sichtbar (Image-Tag). Keine Geheimnisse dort!

