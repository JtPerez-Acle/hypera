# src/metadata/__init__.py
"""
Metadata extraction and management for code analysis.
"""

from .core.metadata import CodeMetadata
from .manager import process_code_chunk, CodeChunk
from .language.support import get_parser, SUPPORTED_LANGUAGES

__all__ = [
    'CodeMetadata',
    'CodeChunk',
    'process_code_chunk',
    'get_parser',
    'SUPPORTED_LANGUAGES'
]