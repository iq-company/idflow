# ID Flow Test Suite

This directory contains comprehensive tests for the ID Flow CLI functionality, ensuring that all features work as documented in the README.

## Test Structure

### Test Files

- **`test_cli_docs.py`** - Unit tests for document management CLI commands
- **`test_cli_vendor.py`** - Unit tests for vendor CLI functionality
- **`test_cli_integration.py`** - Integration tests for complete CLI workflows
- **`conftest.py`** - Pytest configuration and common fixtures

### Test Categories

#### Unit Tests (`test_cli_docs.py`, `test_cli_vendor.py`)
- Test individual CLI command functions
- Mock external dependencies (typer, file system)
- Fast execution, isolated testing
- Cover all command options and error cases

#### Integration Tests (`test_cli_integration.py`)
- Test complete CLI workflows
- Test document lifecycle from creation to deletion
- Test command interactions and state changes
- More realistic testing scenarios

## Running Tests

### Prerequisites
```bash
# Install test dependencies
pip install -e ".[test]"

# Or install pytest directly
pip install pytest pytest-cov
```

### Basic Test Execution
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_cli_docs.py

# Run specific test class
pytest tests/test_cli_docs.py::TestCLIDocumentManagement

# Run specific test method
pytest tests/test_cli_docs.py::TestCLIDocumentManagement::test_add_doc_basic
```

### Test Categories
```bash
# Run only unit tests
pytest -m "unit"

# Run only integration tests
pytest -m "integration"

# Run only CLI tests
pytest -m "cli"

# Skip slow tests
pytest -m "not slow"
```

### Coverage Reports
```bash
# Run with coverage report
pytest --cov=idflow --cov-report=html

# Generate coverage report in terminal
pytest --cov=idflow --cov-report=term-missing

# Generate coverage report in XML format
pytest --cov=idflow --cov-report=xml
```

### Test Output Options
```bash
# Show print statements
pytest -s

# Show local variables on test failure
pytest -l

# Stop on first failure
pytest -x

# Run tests in parallel (requires pytest-xdist)
pytest -n auto
```

## Test Coverage

### Document Management Commands

#### `idflow doc add`
- ✅ Basic document creation
- ✅ Property setting with `--set`
- ✅ List operations with `--list-add`
- ✅ JSON values with `--json`
- ✅ Document references with `--add-doc`
- ✅ File references with `--add-file`
- ✅ Dot notation paths (e.g., `meta.owner=alice`)
- ✅ Stdin body reading
- ✅ Status specification
- ✅ Error handling for invalid inputs

#### `idflow doc list`
- ✅ Basic document listing
- ✅ Column specification with `--col`
- ✅ Pattern matching filters (e.g., `title="Test*"`)
- ✅ Numerical comparison filters (e.g., `priority=">0.7"`)
- ✅ Existence filters (e.g., `tags="exists"`)
- ✅ Document reference filters (e.g., `doc-ref="key"`)
- ✅ File reference filters (e.g., `file-ref="key"`)
- ✅ Multiple filter combinations

#### `idflow doc modify`
- ✅ Property modification with `--set`
- ✅ List additions with `--list-add`
- ✅ JSON value updates with `--json`
- ✅ Document reference additions
- ✅ File reference additions
- ✅ Body content updates
- ✅ Stdin body reading

#### `idflow doc set-status`
- ✅ Status transitions between all valid statuses
- ✅ Directory movement on status change
- ✅ Status validation
- ✅ Error handling for invalid statuses

#### `idflow doc drop`
- ✅ Single document deletion
- ✅ Error handling for non-existent documents

#### `idflow doc drop-all`
- ✅ Bulk document deletion
- ✅ Confirmation prompts
- ✅ Force option handling

### Vendor Commands

#### `idflow vendor copy`
- ✅ Interactive directory selection
- ✅ Copy all directories with `--all`
- ✅ Custom destination specification
- ✅ File conflict resolution (overwrite/skip/abort)
- ✅ Directory structure preservation
- ✅ Error handling for permission/disk issues

### Error Handling
- ✅ Invalid status values
- ✅ Malformed property arguments
- ✅ Invalid JSON input
- ✅ Non-existent document operations
- ✅ File system errors
- ✅ Permission errors

## Test Data

### Sample Documents
The tests use various sample documents to test different scenarios:

- **Basic Document**: Simple document with basic properties
- **Document with References**: Document containing doc and file references
- **Complex Document**: Document with nested properties and complex structures

### Test Files
Various test files are created for file reference testing:
- Text files
- PDF files (mock)
- Image files (mock)
- Configuration files
- Markdown files

## Test Fixtures

### Common Fixtures
- **`temp_workspace`**: Temporary directory for test isolation
- **`temp_data_dir`**: Data directory with status subdirectories
- **`mock_uuid`**: Consistent UUID generation for testing
- **`mock_typer`**: Mocked typer functions
- **`mock_stdin`**: Mocked stdin for testing

### Document Fixtures
- **`sample_document_content`**: Basic document content
- **`sample_document_with_refs`**: Document with references
- **`complex_document_content`**: Complex nested document

## Writing New Tests

### Test Naming Convention
- Test methods: `test_<functionality>_<scenario>`
- Test classes: `Test<Component><Category>`
- Test files: `test_<component>.py`

### Test Structure
```python
def test_feature_scenario(self, fixture1, fixture2):
    """Test description."""
    # Arrange
    # ... setup code ...

    # Act
    # ... execute code ...

    # Assert
    # ... verification code ...
```

### Adding New Test Cases
1. Identify the functionality to test
2. Choose appropriate test category (unit/integration)
3. Use existing fixtures or create new ones
4. Follow the Arrange-Act-Assert pattern
5. Add appropriate test markers
6. Ensure proper cleanup in fixtures

## Continuous Integration

### GitHub Actions
The test suite is designed to run in CI/CD pipelines:
- Fast execution for unit tests
- Comprehensive coverage reporting
- Integration test validation
- Error handling verification

### Local Development
```bash
# Run tests before committing
pytest

# Run specific test categories during development
pytest -m "unit"  # Fast feedback
pytest -m "integration"  # Full validation
```

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Ensure you're in the project root
cd /path/to/idflow

# Install in editable mode
pip install -e .

# Install test dependencies
pip install -e ".[test]"
```

#### Test Failures
```bash
# Run with verbose output to see details
pytest -v

# Show local variables on failure
pytest -l

# Stop on first failure
pytest -x
```

#### Coverage Issues
```bash
# Check if coverage is installed
pip install pytest-cov

# Run with coverage
pytest --cov=idflow
```

## Contributing

When adding new CLI functionality:
1. Add corresponding tests to the appropriate test file
2. Ensure both unit and integration test coverage
3. Update this README with new test coverage information
4. Maintain test isolation and proper cleanup
5. Follow existing test patterns and conventions
