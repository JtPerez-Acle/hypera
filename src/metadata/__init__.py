# src/metadata/__init__.py
"""Metadata management package for code analysis"""
from .metadata_manager import CodeChunk, CodeMetadata, process_code_chunk

__all__ = ["CodeChunk", "CodeMetadata", "process_code_chunk"]