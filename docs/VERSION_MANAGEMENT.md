# Version Management

This document explains how version management works in the idflow project.

## Version Format

We use [Semantic Versioning](https://semver.org/) (SemVer):
- **MAJOR.MINOR.PATCH** (e.g., `1.0.0`)
- **MAJOR**: Breaking changes (incompatible API changes)
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

## Version Management Script

The `scripts/version.py` script provides version management functionality:

### Commands

```bash
# Get current version
python scripts/version.py --get
# Output: 0.1.0

# Set specific version
python scripts/version.py --set 1.0.0

# Bump version
python scripts/version.py --bump patch   # 0.1.0 -> 0.1.1
python scripts/version.py --bump minor   # 0.1.0 -> 0.2.0
python scripts/version.py --bump major   # 0.1.0 -> 1.0.0

# Check version change (for CI)
python scripts/version.py --check-change
```

### Makefile Commands

```bash
# Show current version
make version

# Bump versions
make version-bump-patch    # 0.1.0 -> 0.1.1
make version-bump-minor    # 0.1.0 -> 0.2.0
make version-bump-major    # 0.1.0 -> 1.0.0

# Set specific version
make version-set VERSION=1.0.0
```

## Automated Version Management

### GitHub Actions Workflow

The `.github/workflows/version-bump.yml` workflow automatically:

1. **Triggers** on pushes to `main` branch when `pyproject.toml` is modified
2. **Checks** if the version number actually changed (not just file modification)
3. **Creates** a GitHub release with the new version if changed
4. **Uses** the actual version number (not `github.run_number`)

### How It Works

1. **File Change Detection**: Checks if `pyproject.toml` was modified
2. **Version Extraction**: Extracts current and previous versions using regex
3. **Version Comparison**: Compares versions to detect actual changes
4. **Release Creation**: Creates GitHub release with proper version tag

### Example Workflow

```bash
# 1. Update version in pyproject.toml
make version-bump-minor

# 2. Commit and push
git add pyproject.toml
git commit -m "Bump version to 0.2.0"
git push origin main

# 3. GitHub Actions automatically:
#    - Detects version change
#    - Creates release v0.2.0
#    - Triggers PyPI publishing
```

## Version Checking Logic

The improved version checking:

1. **File Modification Check**: `git diff HEAD~1 HEAD --name-only | grep pyproject.toml`
2. **Current Version**: `grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/'`
3. **Previous Version**: `git show HEAD~1:pyproject.toml | grep '^version = ' | sed 's/version = "\(.*\)"/\1/'`
4. **Comparison**: `[ "$CURRENT_VERSION" != "$PREVIOUS_VERSION" ]`

## Release Tags

- **Format**: `v{version}` (e.g., `v0.1.0`, `v1.0.0`)
- **Created by**: GitHub Actions workflow
- **Triggered by**: Version changes in `pyproject.toml`
- **Used for**: PyPI publishing

## Best Practices

1. **Always bump version** before releasing
2. **Update CHANGELOG.md** with changes
3. **Test locally** before pushing
4. **Use semantic versioning** consistently
5. **Tag releases** in Git (automatic via GitHub Actions)

## Troubleshooting

### Version Not Detected

```bash
# Check if version is in correct format
grep '^version = ' pyproject.toml

# Should output: version = "0.1.0"
```

### Version Change Not Triggered

```bash
# Check if pyproject.toml was actually modified
git diff HEAD~1 HEAD --name-only | grep pyproject.toml

# Check version extraction
python scripts/version.py --check-change
```

### Manual Release

If automated release fails:

```bash
# 1. Create tag manually
git tag v0.1.0
git push origin v0.1.0

# 2. Create release on GitHub
# Go to GitHub → Releases → Create new release
```

## Integration with PyPI

The version management integrates with PyPI publishing:

1. **Version bump** → **GitHub release** → **PyPI publish**
2. **Version number** is used as PyPI package version
3. **Release notes** are generated from commit history
4. **Automated testing** ensures package works after release
