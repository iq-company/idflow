# Vendor System - Modular Extensions

The vendor system allows projects to integrate external packages and make their content available as modular extensions. This enables sharing of tasks, workflows, stages, and extras between different idflow projects.

## Overview

The vendor system implements a hierarchical resource resolution with the following precedence:

```
Project (highest priority) > Vendors > Core Package (lowest priority)
```

This allows projects to:
- Include external packages as "vendors"
- Override vendor content with project-specific implementations
- Extend vendor functionality while maintaining updateability

## Vendor Configuration

### Configuration Directory

Vendor specifications are defined in TOML files under `config/vendors.d/`:

```
project/
├── config/
│   └── vendors.d/
│       ├── email_bot.toml
│       └── analytics.toml
└── .idflow/
    └── vendors/
        ├── email_bot -> /path/to/email_bot
        └── analytics/ (git clone)
```

### Vendor Types

#### Git Vendors

For remote repositories:

```toml
# config/vendors.d/email_bot.toml
name = "email_bot"
type = "git"
url = "https://github.com/company/email-bot-idflow.git"
ref = "main"  # branch, tag, or commit
priority = 10
enabled = true
```

#### Path Vendors

For local filesystem references:

```toml
# config/vendors.d/local_tasks.toml
name = "local_tasks"
type = "path"
path = "/home/user/shared-idflow-tasks"
priority = 20
enabled = true
```

### Priority System

- Lower numbers = higher priority
- Vendors with higher priority override those with lower priority
- Project content always overrides vendor content
- Core package content has the lowest priority

## Resource Types

### Tasks

Tasks are directory-based resources:

```
vendor_project/
└── tasks/
    ├── email_sender/
    │   └── email_sender.py
    └── data_processor/
        └── data_processor.py
```

### Workflows

Workflows are directory-based with JSON definitions:

```
vendor_project/
└── workflows/
    ├── email_campaign/
    │   └── email_campaign.json
    └── data_pipeline/
        └── data_pipeline.json
```

### Stages

Stages are YAML files:

```
vendor_project/
└── stages/
    ├── email_stage.yml
    └── processing_stage.yml
```

### Extras

Vendor projects can define their own optional dependencies:

```
vendor_project/
└── config/
    └── extras.d/
        └── extras.toml
```

Example `extras.toml`:
```toml
[email_features]
packages = [
    "sendgrid>=6.0.0",
    "jinja2>=3.0.0"
]
extends = [
    "ai_prompts"  # Extend core package extra
]

[analytics]
packages = [
    "pandas>=1.5.0",
    "plotly>=5.0.0"
]
```

## CLI Commands

### Vendor Management

```bash
# List configured vendors
idflow vendor specs

# Fetch/update all vendors
idflow vendor fetch

# Enable/disable vendors
idflow vendor enable email_bot
idflow vendor disable analytics
```

### Resource Listing

All listing commands now show origin classification:

```bash
# List with origin classification
idflow vendor list
idflow tasks list
idflow workflow list
idflow stage list
idflow worker list
idflow extras list
```

Origin types:
- **standard**: From core package
- **vendor**: From vendor packages
- **extended**: Project override of vendor/core content
- **custom**: Project-only content

### Resource Copying

Copy vendor resources to project for customization:

```bash
# Interactive selection
idflow vendor copy

# Direct specification
idflow vendor copy --section tasks --element email_sender
```

## Origin Classification

The system automatically classifies resources based on their source:

- **standard**: Core package resources
- **vendor**: Resources from vendor packages (highest priority vendor wins)
- **extended**: Project resources that override vendor/core content
- **custom**: Project-only resources

This classification is displayed in all CLI commands for transparency.

## Workspace Management

### Vendor Workspace

Vendors are materialized in `.idflow/vendors/`:

- **Git vendors**: Cloned repositories
- **Path vendors**: Symbolic links to original locations

The workspace is automatically managed and should be added to `.gitignore`.

### Updates

```bash
# Update all vendors
idflow vendor fetch

# Git vendors: git pull/checkout
# Path vendors: symlink refresh
```

## Best Practices

### Project Structure

Organize vendor projects like standard idflow projects:

```
vendor_project/
├── config/
│   ├── vendors.d/          # Nested vendor dependencies
│   └── extras.d/           # Optional dependencies
├── tasks/                  # Task implementations
├── workflows/              # Workflow definitions
├── stages/                 # Stage definitions
└── README.md              # Documentation
```

### Version Management

- Use specific git tags/commits for production
- Use branches for development integration
- Document breaking changes in vendor projects

### Dependency Management

- Define vendor-specific extras in `config/extras.d/`
- Use `extends` to build on core package extras
- Keep vendor dependencies minimal and well-documented

### Testing Integration

Test vendor integration in your project:

```bash
# Check resource availability
idflow vendor list

# Verify stages load correctly
idflow stage list

# Test workflow execution
idflow workflow list
```

## Examples

### Email Bot Integration

1. **Configure vendor**:
```toml
# config/vendors.d/email_bot.toml
name = "email_bot"
type = "git"
url = "https://github.com/company/email-bot-idflow.git"
ref = "v1.2.0"
priority = 10
enabled = true
```

2. **Fetch vendor**:
```bash
idflow vendor fetch
```

3. **List available resources**:
```bash
idflow vendor list
```

4. **Use vendor stage**:
```bash
# Stage automatically available
idflow stage list
# Shows: email_campaign    active    vendor
```

5. **Customize if needed**:
```bash
idflow vendor copy --section stages --element email_campaign
# Now shows: email_campaign    active    extended
```

### Local Development Setup

```toml
# config/vendors.d/shared_tasks.toml
name = "shared_tasks"
type = "path"
path = "../shared-idflow-components"
priority = 5
enabled = true
```

This allows live development against shared components without version management overhead.

## Migration Guide

### From Direct Copying

If you previously copied resources manually:

1. Create vendor configuration
2. Run `idflow vendor fetch`
3. Remove manually copied files
4. Verify resources are available via vendor system

### Adding Vendor Support to Existing Projects

1. Create `config/vendors.d/` directory
2. Add vendor specifications
3. Update `.gitignore` to exclude `.idflow/`
4. Run `idflow vendor fetch`

## Troubleshooting

### Resource Not Found

```bash
# Check vendor status
idflow vendor specs

# Verify fetch completed
idflow vendor fetch

# Check resource listing
idflow vendor list
```

### Priority Conflicts

- Check vendor priorities in configuration
- Lower numbers have higher priority
- Project content always wins

### Dependency Issues

```bash
# Check extras requirements
idflow extras list

# Install missing dependencies
idflow extras install

# Clean unused dependencies
idflow extras purge
```

## Implementation Notes

### Resource Resolution

The system uses `ResourceResolver` for consistent resource discovery across all CLI commands. This ensures:

- Uniform origin classification
- Consistent overlay behavior
- Reliable precedence handling

### Performance

- Vendor workspaces are cached
- Resource discovery is optimized for repeated access
- Symbolic links minimize disk usage for path vendors

### Security

- Git vendors are isolated in workspace
- Path vendors respect original permissions
- No automatic code execution from vendors
