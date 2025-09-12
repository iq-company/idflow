# Publishing Guide

This guide explains how to publish the idflow package to PyPI.

## Prerequisites

1. **PyPI Account**: Create an account at [pypi.org](https://pypi.org/account/register/)
2. **TestPyPI Account**: Create an account at [test.pypi.org](https://test.pypi.org/account/register/)
3. **API Tokens**: Generate API tokens for both PyPI and TestPyPI
4. **GitHub Secrets**: Add the tokens to your GitHub repository secrets

## Package Information

- **Package Name**: `idflow`
- **Repository**: `https://github.com/yourusername/idflow`
- **PyPI**: `https://pypi.org/project/idflow/`
- **TestPyPI**: `https://test.pypi.org/project/idflow/`

## Manual Publishing

### 1. Prepare the Package

```bash
# Clean previous builds
python scripts/publish.py --clean

# Build the package
python scripts/publish.py --build

# Check the package
python scripts/publish.py --check
```

### 2. Test on TestPyPI

```bash
# Publish to TestPyPI first
python scripts/publish.py --test

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ idflow
idflow --help
```

### 3. Publish to PyPI

```bash
# Publish to PyPI
python scripts/publish.py --pypi

# Test installation from PyPI
python scripts/publish.py --test-install
```

### 4. All-in-One Command

```bash
# Run all steps interactively
python scripts/publish.py --all
```

## Automated Publishing

### GitHub Actions

The repository includes GitHub Actions workflows for automated publishing:

1. **Release Trigger**: Automatically publishes when a GitHub release is created
2. **Manual Trigger**: Allows manual publishing via GitHub Actions UI

### Setup GitHub Secrets

Add these secrets to your GitHub repository:

- `PYPI_API_TOKEN`: Your PyPI API token
- `TEST_PYPI_API_TOKEN`: Your TestPyPI API token

### Creating a Release

1. Update version in `pyproject.toml`
2. Commit and push changes
3. Create a GitHub release with the same version tag
4. GitHub Actions will automatically publish to PyPI

## Version Management

### Semantic Versioning

Follow [Semantic Versioning](https://semver.org/):
- `MAJOR.MINOR.PATCH` (e.g., `1.0.0`)
- `MAJOR`: Breaking changes
- `MINOR`: New features (backward compatible)
- `PATCH`: Bug fixes (backward compatible)

### Updating Version

1. Edit `pyproject.toml`:
   ```toml
   [project]
   version = "0.2.0"  # Update version
   ```

2. Update `CHANGELOG.md` with changes

3. Commit and push:
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "Bump version to 0.2.0"
   git push
   ```

## Package Structure

```
idflow/
├── idflow/                 # Main package
├── tests/                  # Test files
├── scripts/                # Publishing scripts
├── .github/workflows/      # GitHub Actions
├── pyproject.toml         # Package configuration
├── README.md              # Package description
├── LICENSE                # MIT License
└── CHANGELOG.md           # Version history
```

## Dependencies

### Core Dependencies
- `typer>=0.12` - CLI framework
- `pydantic>=2` - Data validation
- `PyYAML>=6` - YAML processing
- `conductor-python` - Workflow engine
- `litellm>=1.0.0` - LLM integration
- `keybert>=0.9.0` - Keyword extraction

### Optional Dependencies
- `idflow[research]` - Research features
- `idflow[test]` - Testing dependencies

## Troubleshooting

### Common Issues

1. **Package already exists**: Update version number
2. **Authentication failed**: Check API tokens
3. **Build failed**: Check `pyproject.toml` syntax
4. **Import errors**: Verify package structure

### Debug Commands

```bash
# Check package structure
python -c "import idflow; print(idflow.__file__)"

# Validate pyproject.toml
python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))"

# Test package locally
pip install -e .
```

## Best Practices

1. **Always test on TestPyPI first**
2. **Use semantic versioning**
3. **Update CHANGELOG.md**
4. **Tag releases in Git**
5. **Test installation after publishing**
6. **Keep dependencies up to date**

## Support

For issues with publishing:
1. Check the [PyPI documentation](https://packaging.python.org/)
2. Review GitHub Actions logs
3. Test locally with TestPyPI
4. Create an issue in the repository
