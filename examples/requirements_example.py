#!/usr/bin/env python3
"""
Example demonstrating the new requirements functionality.

This example shows how to use the extended requirements system with:
- Attribute checks (EQ, NE, GT, LT, etc.)
- List checks (HAS, CONTAINS, INCLUDES, etc.)
- File presence requirements
- Stage requirements
"""

from idflow.core.document_factory import get_document_class
from idflow.core.stage_definitions import get_stage_definitions

def main():
    """Demonstrate the new requirements functionality."""

    # Get the document class (FSMarkdownDocument)
    Document = get_document_class()

    # Create a test document with various attributes
    doc = Document(
        id="test-doc-123",
        status="active",
        tags=["blog_post_ideas", "research", "content"],
        seo_keywords="research, blog, ideas",
        url="https://example.com/blog",
        priority=5,
        author="John Doe"
    )

    # Add some file references
    doc.add_file_ref("content", "main_content.md", "file-uuid-1")
    doc.add_file_ref("images", "header.jpg", "file-uuid-2")

    print("=== Document created ===")
    print(f"ID: {doc.id}")
    print(f"Status: {doc.status}")
    print(f"Tags: {doc.tags}")
    print(f"SEO Keywords: {doc.seo_keywords}")
    print(f"URL: {doc.url}")
    print(f"Priority: {doc.priority}")
    print(f"Author: {doc.author}")
    print(f"File refs: {len(doc.file_refs)}")
    print()

    # Get stage definitions
    stage_definitions = get_stage_definitions()

    # Test the research_blog_post_ideas stage
    print("=== Testing research_blog_post_ideas stage ===")
    stage_def = stage_definitions.get_definition("research_blog_post_ideas")
    if stage_def:
        print(f"Stage name: {stage_def.name}")
        print(f"Active: {stage_def.active}")
        print(f"Multiple callable: {stage_def.multiple_callable}")

        if stage_def.requirements:
            print("\nRequirements:")
            if stage_def.requirements.file_presence:
                fp = stage_def.requirements.file_presence
                print(f"  File presence: {fp.key} {fp.count_operator} {fp.count}")

            if stage_def.requirements.list_checks:
                print("  List checks:")
                for lc in stage_def.requirements.list_checks:
                    print(f"    {lc.attribute} {lc.operator} '{lc.value}' (case_sensitive: {lc.case_sensitive})")

        # Check if requirements are met
        requirements_met = stage_def.check_requirements(doc)
        print(f"\nRequirements met: {requirements_met}")

        if requirements_met:
            print("✅ Stage can be triggered!")
        else:
            print("❌ Stage requirements not met")
    else:
        print("❌ Stage definition not found")

    print("\n" + "="*50)

    # Demonstrate different requirement types
    print("=== Example requirement configurations ===")

    print("\n1. Attribute checks:")
    print("   - seo_keywords EQ 'research, blog, ideas'")
    print("   - priority GT 3")
    print("   - author NE 'Jane Doe'")
    print("   - url IS_NOT null")
    print("   - filename CP 'blog_*.md'  (Glob pattern)")
    print("   - title REGEX '^How to.*'  (Regex pattern)")

    print("\n2. List checks:")
    print("   - tags HAS 'blog_post_ideas'")
    print("   - tags CONTAINS 'research'")
    print("   - tags NOT_HAS 'draft'")

    print("\n3. File presence checks:")
    print("   - content files >= 1")
    print("   - images files == 2")

    print("\n4. Stage requirements:")
    print("   - previous_stage status == 'done'")

    print("\n=== YAML Configuration Example ===")
    print("""
requirements:
  file_presence:
    key: content
    count: 1
    count_operator: '>='

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
    - attribute: filename
      operator: CP
      value: 'blog_*.md'
      case_sensitive: false
    - attribute: title
      operator: REGEX
      value: '^How to.*'
      case_sensitive: false
    - attribute: url
      operator: NOT_REGEX
      value: '.*draft.*'
      case_sensitive: false

  list_checks:
    - attribute: tags
      operator: HAS
      value: 'blog_post_ideas'
      case_sensitive: false
    - attribute: tags
      operator: CONTAINS
      value: 'research'
      case_sensitive: false

  stages:
    previous_stage:
      status: 'done'
""")

if __name__ == "__main__":
    main()
