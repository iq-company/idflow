.PHONY: help install install-dev test clean build check publish-test publish-pypi test-install

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install the package
	pip install .

install-dev: ## Install in development mode
	pip install -e .

install-research: ## Install with research features
	pip install -e ".[research]"

install-test: ## Install with test dependencies
	pip install -e ".[test]"

install-all: ## Install with all optional dependencies
	pip install -e ".[research,test]"

test: ## Run tests
	pytest

test-verbose: ## Run tests with verbose output
	pytest -v

test-coverage: ## Run tests with coverage
	pytest --cov=idflow --cov-report=html

clean: ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +

build: ## Build the package
	python -m build

check: ## Check the package
	twine check dist/*

publish-test: ## Publish to TestPyPI
	twine upload --repository testpypi dist/*

publish-pypi: ## Publish to PyPI
	twine upload dist/*

test-install: ## Test installation from PyPI
	pip install idflow
	idflow --help

publish-all: clean build check ## Clean, build, check, and prompt for publishing
	@echo "Package built successfully!"
	@echo "To publish to TestPyPI: make publish-test"
	@echo "To publish to PyPI: make publish-pypi"

version: ## Show current version
	@python scripts/version.py --get

version-bump-patch: ## Bump patch version (0.1.0 -> 0.1.1)
	@python scripts/version.py --bump patch

version-bump-minor: ## Bump minor version (0.1.0 -> 0.2.0)
	@python scripts/version.py --bump minor

version-bump-major: ## Bump major version (0.1.0 -> 1.0.0)
	@python scripts/version.py --bump major

version-set: ## Set version (usage: make version-set VERSION=1.0.0)
	@python scripts/version.py --set $(VERSION)

lint: ## Run linting
	flake8 idflow/
	black --check idflow/
	isort --check-only idflow/

format: ## Format code
	black idflow/
	isort idflow/

docs: ## Generate documentation
	@echo "Documentation is in README.md and PUBLISHING.md"

setup-dev: ## Setup development environment
	python -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -e ".[test,research]"
	@echo "Development environment ready! Activate with: source .venv/bin/activate"
