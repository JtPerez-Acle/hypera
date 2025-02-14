"""
Collection management for vector storage.

This module handles the creation and management of Qdrant collections
for storing code embeddings.
"""

from typing import Dict, Any
from qdrant_client.http.models import Distance, VectorParams, CollectionStatus
from qdrant_client.http.exceptions import UnexpectedResponse
from .client import get_qdrant_client
from .schema import CodeChunkMetadata

# Configuration for our collections
COLLECTIONS_CONFIG = {
    "code_chunks": {
        "size": 1536,  # Dimension size for code embeddings
        "distance": Distance.COSINE,
        "metadata_schema": {
            "chunk_type": "keyword",
            "language": "keyword",
            "file_path": "keyword",
            "start_line": "integer",
            "end_line": "integer",
            "dependencies": "keyword[]",
            "imports": "keyword[]",
            "created_at": "datetime",
            "updated_at": "datetime"
        }
    }
}

def ensure_collections() -> None:
    """
    Ensures all required collections exist with proper configuration.
    Creates collections if they don't exist, validates if they do.
    
    Raises:
        RuntimeError: If collection validation fails
    
    Metadata:
        - Error Handling: Collection validation
        - State Management: Idempotent operation
        - Performance: One-time setup
    """
    client = get_qdrant_client()
    
    for name, config in COLLECTIONS_CONFIG.items():
        try:
            # Check if collection exists
            collection_info = client.get_collection(name)
            
            # Validate existing collection
            if collection_info.status != CollectionStatus.GREEN:
                raise RuntimeError(f"Collection {name} exists but is not healthy")
                
            # TODO: Add more validation of collection config
            
        except UnexpectedResponse:
            # Collection doesn't exist, create it
            client.create_collection(
                name=name,
                vectors_config=VectorParams(
                    size=config["size"],
                    distance=config["distance"]
                ),
                # TODO: Add proper optimization parameters based on expected load
                # optimizers_config=None,
                # hnsw_config=None,
            )
            
            # Create field indices for efficient filtering
            for field_name, field_type in config["metadata_schema"].items():
                client.create_payload_index(
                    collection_name=name,
                    field_name=field_name,
                    field_schema=field_type
                )
