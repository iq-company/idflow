# Requirements System Documentation

This document describes the comprehensive requirements system for idflow stages, including all supported operators and pattern matching capabilities.

## Overview

The requirements system allows you to define conditions that must be met before a stage can be executed. Requirements are checked automatically when documents are saved or when stage evaluation is triggered.

## Requirement Types

### 1. File Presence Requirements

Check for the presence of files with specific keys.

```yaml
requirements:
  file_presence:
    key: content
    count: 1
    count_operator: '>='  # >=, ==, >, <=, <, !=
```

**Supported Operators:**
- `>=` - Greater than or equal
- `==` - Equal
- `>` - Greater than
- `<=` - Less than or equal
- `<` - Less than
- `!=` - Not equal

### 2. Stage Requirements

Check for the completion status of other stages.

```yaml
requirements:
  stages:
    previous_stage:
      status: 'done'  # done, active, scheduled, blocked, cancelled
```

### 3. Attribute Requirements

Check individual document attributes with various operators.

```yaml
requirements:
  attribute_checks:
    - attribute: seo_keywords
      operator: EQ
      value: 'research, blog, ideas'
      case_sensitive: true
    - attribute: priority
      operator: GT
      value: 3
    - attribute: author
      operator: NE
      value: 'Jane Doe'
```

**Supported Operators:**

#### Basic Comparison Operators
- `EQ` - Equal
- `NE` - Not equal
- `GT` - Greater than
- `LT` - Less than
- `GTE` - Greater than or equal
- `LTE` - Less than or equal
- `IS` - Identity (is)
- `IS_NOT` - Not identity (is not)

#### Pattern Matching Operators
- `CP` - Contains Pattern (Glob matching)
- `NP` - Not Contains Pattern (Glob matching)
- `REGEX` - Regex pattern matching
- `NOT_REGEX` - Regex pattern not matching

### 4. List Requirements

Check list attributes for specific values.

```yaml
requirements:
  list_checks:
    - attribute: tags
      operator: HAS
      value: 'blog_post_ideas'
      case_sensitive: false
    - attribute: categories
      operator: NOT_CONTAINS
      value: 'draft'
      case_sensitive: false
```

**Supported Operators:**
- `HAS` / `CONTAINS` / `INCLUDES` - Contains value
- `NOT_HAS` / `NOT_CONTAINS` / `NOT_INCLUDES` - Does not contain value

## Pattern Matching Details

### Glob Pattern Matching

Uses Python's `fnmatch` module for Unix shell-style wildcards.

**Supported Wildcards:**
- `*` - Matches any sequence of characters
- `?` - Matches any single character
- `[abc]` - Matches any character in the set
- `[!abc]` - Matches any character not in the set

**Examples:**
```yaml
# Match files starting with "blog_"
- attribute: filename
  operator: CP
  value: 'blog_*'

# Match files ending with ".md"
- attribute: filename
  operator: CP
  value: '*.md'

# Match files with specific pattern
- attribute: filename
  operator: CP
  value: 'blog_????_??_??.md'

# Exclude draft files
- attribute: filename
  operator: NP
  value: 'draft_*'
```

### Regex Pattern Matching

Uses Python's `re` module for regular expression matching.

**Examples:**
```yaml
# Match URLs starting with https
- attribute: url
  operator: REGEX
  value: '^https://.*'

# Match email addresses
- attribute: email
  operator: REGEX
  value: '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

# Exclude Gmail addresses
- attribute: email
  operator: NOT_REGEX
  value: '.*@gmail\.com'

# Match titles starting with "How to"
- attribute: title
  operator: REGEX
  value: '^How to.*'
```

## Case Sensitivity

All string comparisons support case sensitivity control:

```yaml
attribute_checks:
  - attribute: title
    operator: CP
    value: 'blog*'
    case_sensitive: false  # Default: true
```

## Complete Example

```yaml
name: research_blog_post_ideas
active: true
multiple_callable: false
workflows:
  - name: research_blog_post_ideas
    version: 1
    when: "doc.tags && doc.tags.includes('blog_post_ideas')"
    inputs:
      research_methods: ["gpt_researcher", "duckduckgo_serp"]
requirements:
  # File presence requirement
  file_presence:
    key: content
    count: 1
    count_operator: '>='

  # Attribute requirements
  attribute_checks:
    - attribute: seo_keywords
      operator: EQ
      value: 'research, blog, ideas'
      case_sensitive: true
    - attribute: priority
      operator: GT
      value: 3
    - attribute: filename
      operator: CP
      value: 'blog_*.md'
      case_sensitive: false
    - attribute: url
      operator: REGEX
      value: '^https://.*'
      case_sensitive: false

  # List requirements
  list_checks:
    - attribute: tags
      operator: HAS
      value: 'blog_post_ideas'
      case_sensitive: false
    - attribute: tags
      operator: NOT_HAS
      value: 'draft'
      case_sensitive: false

  # Stage requirements
  stages:
    previous_stage:
      status: 'done'
```

## Error Handling

- **Invalid regex patterns**: Return `False` without crashing
- **Non-string values with pattern matching**: Return `False`
- **Missing attributes**: Return `False`
- **Invalid operators**: Raise `ValueError`

## Testing

The requirements system is thoroughly tested. Run tests with:

```bash
python -m pytest tests/test_stages.py::TestRequirements -v
```

## Examples

See `examples/requirements_example.py` for a complete working example demonstrating all requirement types and operators.
