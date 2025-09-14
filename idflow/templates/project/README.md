# __PROJECT_NAME__

A minimal ID Flow project template.

## Quickstart

```bash
# Clone your repository
# (replace with your repo URL)
git clone <YOUR_REPO_URL> __PROJECT_NAME__
cd __PROJECT_NAME__

# Create virtual environment
python3 -m venv __VENV_NAME__
source __VENV_NAME__/bin/activate  # Windows: __VENV_NAME__\\Scripts\\activate

# Install project (installs idflow via pyproject)
pip install --upgrade pip
pip install -e .

# Install required extras
idflow extras install
```

## First steps

```bash
# Create a document
idflow doc add "My first document"

# List documents
idflow doc list
```

## Configuration
- `config/idflow.yml` sets base directories, ORM implementation and Conductor URL
- Project-defined extras live in `config/extras.d/`
- Vendor specs live in `config/vendors.d/` (see example `config/vendors.d/email_bot.toml`)

### Vendors

Vendor packages (git or path) can be configured via TOML in `config/vendors.d/`.
After adding a spec, fetch or update vendor sources via:

```bash
idflow vendor fetch
```

Checked-out vendors are placed in `.idflow/vendors/<name>` (git) or symlinked (path).
Resources are overlaid in this precedence: `lib -> vendors -> project`.

Example specs:

```toml
# config/vendors.d/email_bot.toml
name = "email_bot"
enabled = true
priority = 50

[source]
type = "git"
url = "https://github.com/org/email-bot-idflow.git"
ref = "v1.4.3"  # tag, branch or commit
```

```toml
# config/vendors.d/local_tools.toml
name = "local_tools"
enabled = true
priority = 60

[source]
type = "path"
path = "/absolute/path/to/another/idflow-project"  # can also be relative to project root
```

## Data layout
- `data/inbox`, `data/active`, `data/done` are created by the template
