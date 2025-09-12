# Research Features

This document describes the optional research features available in idflow.

## Installation

To use the research features, install idflow with the research extras:

```bash
pip install idflow[research]
```

This will install the following additional dependencies:
- `requests>=2.31.0` - HTTP library for API calls
- `playwright>=1.40.0` - Browser automation for web scraping
- `beautifulsoup4>=4.12.0` - HTML parsing
- `gpt-researcher>=0.1.0` - AI research automation

## Available Research Tasks

### GPT Researcher (`gpt_researcher`)

Conducts AI-powered research on given topics using the GPT Researcher framework.

**Parameters:**
- `query` (str): The research query/topic
- `docId` (str): Document ID for tracking
- `max_results` (int, optional): Maximum number of research results (default: 5)
- `research_depth` (str, optional): Research depth level - "basic", "intermediate", or "advanced" (default: "basic")

**Example Usage:**
```python
from idflow.tasks.gpt_researcher import gpt_researcher

result = gpt_researcher(
    query="artificial intelligence trends 2024",
    docId="doc_123",
    max_results=10,
    research_depth="advanced"
)
```

### DuckDuckGo Search (`duckduckgo_search`)

Performs web searches using DuckDuckGo to find relevant web results.

**Parameters:**
- `query` (str): Search query
- `docId` (str): Document ID for tracking
- `max_results` (int, optional): Maximum number of search results (default: 10)

**Example Usage:**
```python
from idflow.tasks.duckduckgo_serp import duckduckgo_search

result = duckduckgo_search(
    query="machine learning tutorials",
    docId="doc_123",
    max_results=15
)
```

### Playwright Crawl (`playwright_crawl`)

Crawls web pages using Playwright to extract content from search results.

**Parameters:**
- `search_results` (Dict): Results from DuckDuckGo search
- `docId` (str): Document ID for tracking
- `max_pages` (int, optional): Maximum number of pages to crawl (default: 5)

**Example Usage:**
```python
from idflow.tasks.duckduckgo_serp import playwright_crawl

result = playwright_crawl(
    search_results=search_data,
    docId="doc_123",
    max_pages=10
)
```

## Error Handling

If the research dependencies are not installed, the tasks will return an error message with installation instructions:

```json
{
    "error": "Research dependencies not installed. Please install with: pip install idflow[research]",
    "missing_dependency": "No module named 'requests'",
    "query": "your query",
    "docId": "your_doc_id",
    "method": "task_name"
}
```

## Worker Management

You can check which workers are available and their dependency status:

```bash
# List all available workers
idflow worker list

# This will show:
# ✓ keyword_extract (idflow/tasks/keyword_extract/keyword_extract.py)
# ⚠ gpt_researcher (idflow/tasks/gpt_researcher/gpt_researcher.py) - requires: pip install idflow[research]
# ⚠ duckduckgo_search (idflow/tasks/duckduckgo_serp/duckduckgo_serp.py) - requires: pip install idflow[research]
```

## Workflow Integration

These research tasks can be integrated into idflow workflows by referencing them in your workflow definitions. The tasks will automatically handle dependency checking and provide appropriate error messages if dependencies are missing.

## Development

When developing new research tasks, follow this pattern:

1. Add optional dependencies to `pyproject.toml` under `[project.optional-dependencies]`
2. Use try/except blocks to check for dependencies at module level
3. Return helpful error messages if dependencies are missing
4. Update this documentation with new task descriptions
