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

## Data layout
- `data/inbox`, `data/active`, `data/done` are created by the template
