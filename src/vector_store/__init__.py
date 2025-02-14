"""
Vector storage module for HyperA.

This module handles all vector storage operations using Qdrant, including:
- Schema definition
- Collection management
- Embedding generation and storage
- Vector search and retrieval
"""

from .client import get_qdrant_client
from .schema import CodeChunkPayload, CodeChunkMetadata
from .collections import ensure_collections

__all__ = [
    'get_qdrant_client',
    'CodeChunkPayload',
    'CodeChunkMetadata',
    'ensure_collections'
]
