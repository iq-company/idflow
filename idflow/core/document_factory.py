from __future__ import annotations
from typing import Type
from .config import config
from .document import Document


def get_document_class() -> Type[Document]:
    """
    Get the appropriate Document class based on configuration.

    Returns:
        The Document class to use for document operations.

    Raises:
        ImportError: If the configured implementation cannot be imported.
        ValueError: If the configured implementation is not valid.
    """
    implementation = config.document_implementation

    if implementation == "fs_markdown":
        try:
            from .fs_markdown import FSMarkdownDocument
            return FSMarkdownDocument
        except ImportError as e:
            raise ImportError(f"Could not import FSMarkdownDocument: {e}")

    elif implementation == "database":
        try:
            from .database_document import DatabaseDocument
            return DatabaseDocument
        except ImportError as e:
            raise ImportError(f"Could not import DatabaseDocument: {e}")

    else:
        raise ValueError(f"Unknown document implementation: {implementation}. "
                        f"Supported implementations: fs_markdown, database")


def create_document(**kwargs) -> Document:
    """
    Create a new document instance using the configured implementation.

    Args:
        **kwargs: Arguments to pass to the document constructor.

    Returns:
        A new document instance.
    """
    document_class = get_document_class()
    return document_class(**kwargs)
