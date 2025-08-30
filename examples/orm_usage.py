#!/usr/bin/env python3
"""
Example script demonstrating the new Document ORM system.

This script shows how to:
- Create documents with the ORM
- Add document references and file references
- Create stages within documents
- Use lifecycle hooks
- Query documents
"""

import sys
from pathlib import Path

# Add the idflow package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from idflow.core.fs_markdown import FSMarkdownDocument, Stage

def example_lifecycle_hooks():
    """Example of using lifecycle hooks."""

    class MyDocument(FSMarkdownDocument):
        def before_create(self):
            print(f"About to create document {self.id}")
            # You could add validation, logging, etc.

        def after_create(self):
            print(f"Successfully created document {self.id}")
            # You could send notifications, update indexes, etc.

        def before_save(self):
            print(f"About to save document {self.id}")
            # You could add timestamps, validation, etc.

    # Create a document with custom hooks
    doc = MyDocument(
        title="Example with Hooks",
        description="This document demonstrates lifecycle hooks"
    )

    # The hooks will be called automatically
    doc.create()

    # Modify and save
    doc.description = "Updated description"
    doc.save()

    return doc

def example_document_relations():
    """Example of working with document references and file references."""

    # Create a main document
    main_doc = FSMarkdownDocument(
        title="Main Document",
        status="active"
    )

    # Add document references
    main_doc.add_doc_ref("related", "123e4567-e89b-12d3-a456-426614174000")
    main_doc.add_doc_ref("parent", "987fcdeb-51a2-43d1-9f12-345678901234")

    # Add file references (files will be copied to the document directory)
    if Path("examples/test_file.txt").exists():
        file_ref = main_doc.copy_file(Path("examples/test_file.txt"), "example_file")
        file_ref.data = {"description": "An example file", "type": "text"}

    # Create the document
    main_doc.create()

    return main_doc

def example_stages():
    """Example of working with stages."""

    # Create a document
    doc = FSMarkdownDocument(
        title="Project Document",
        status="active"
    )

    # Add stages
    planning_stage = doc.add_stage("planning", status="done")
    planning_stage.body = "Planning phase completed"
    planning_stage.set("start_date", "2024-01-01")
    planning_stage.set("end_date", "2024-01-15")

    development_stage = doc.add_stage("development", status="active")
    development_stage.body = "Development in progress"
    development_stage.set("start_date", "2024-01-16")

    # Add files to stages
    if Path("examples/plan.txt").exists():
        planning_stage.copy_file(Path("examples/plan.txt"), "plan")

    # Create the document (stages will be created automatically)
    doc.create()

    return doc

def example_queries():
    """Example of querying documents."""

    # Find a specific document by UUID
    # doc = FSMarkdownDocument.find("some-uuid-here")

    # Find documents by status
    active_docs = FSMarkdownDocument.where(status="active")
    print(f"Found {len(active_docs)} active documents")

    # Find documents with specific document references
    docs_with_refs = FSMarkdownDocument.where(doc_ref="related")
    print(f"Found {len(docs_with_refs)} documents with 'related' references")

    # Find documents with specific file references
    docs_with_files = FSMarkdownDocument.where(file_ref="example_file")
    print(f"Found {len(docs_with_files)} documents with 'example_file'")

    # Find documents where a property exists
    docs_with_title = FSMarkdownDocument.where(exists="title")
    print(f"Found {len(docs_with_title)} documents with titles")

    return active_docs

def main():
    """Main function demonstrating the ORM features."""

    print("=== Document ORM Examples ===\n")

    print("1. Creating documents with lifecycle hooks:")
    doc1 = example_lifecycle_hooks()
    print(f"   Created document: {doc1.id}\n")

    print("2. Working with document relations:")
    doc2 = example_document_relations()
    print(f"   Created document with relations: {doc2.id}")
    print(f"   Document references: {len(doc2.doc_refs)}")
    print(f"   File references: {len(doc2.file_refs)}\n")

    print("3. Working with stages:")
    doc3 = example_stages()
    print(f"   Created document with stages: {doc3.id}")
    print(f"   Stages: {[stage.name for stage in doc3.stages]}\n")

    print("4. Querying documents:")
    example_queries()
    print()

    print("=== ORM Examples Completed ===")
    print(f"Check the data directory for created documents")

if __name__ == "__main__":
    main()
