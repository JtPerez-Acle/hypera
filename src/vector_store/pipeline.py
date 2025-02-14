"""
High-level interface for the vector storage pipeline.

This module provides a simple interface for processing code files
and storing their embeddings in the vector database.
"""

import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path
from qdrant_client.http.models import PointStruct
from .client import get_qdrant_client
from .collections import ensure_collections, COLLECTIONS_CONFIG
from .schema import CodeChunkPayload, Language
from .chunking import chunk_python_file, detect_language
from .embeddings import initialize_openai, process_chunks_batch

class Pipeline:
    """
    Main pipeline for processing code files and storing embeddings.
    
    This class handles the entire process from code chunking to
    embedding generation (via OpenAI) and storage in Qdrant.
    The stored embeddings will be used by Gemini 1.5 Pro for
    retrieval and context holding.
    
    Metadata:
        - Dependencies: All vector_store modules
        - Performance: Async batch processing
        - Error Handling: Comprehensive error states
    """
    
    def __init__(self):
        """Initialize the pipeline and ensure collections exist."""
        self.qdrant = get_qdrant_client()
        initialize_openai()
        ensure_collections()
    
    async def process_file(self, file_path: str) -> List[str]:
        """
        Process a single file and store its embeddings.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            List[str]: IDs of the stored points
            
        Metadata:
            - Dependencies: chunking, embeddings modules
            - Performance: Async processing
            - Error Handling: File access, processing errors
        """
        language = detect_language(file_path)
        chunks: List[CodeChunkPayload] = []
        
        # Generate chunks based on language
        if language == Language.PYTHON:
            chunks.extend(chunk_python_file(file_path))
        else:
            # TODO: Implement chunking for other languages
            raise NotImplementedError(f"Language {language} not yet supported")
        
        # Process chunks in batches
        processed_chunks = await process_chunks_batch(chunks)
        
        # Store in Qdrant
        points = []
        for chunk in processed_chunks:
            point_id = f"{chunk.metadata.file_path}:{chunk.metadata.start_line}"
            point = PointStruct(
                id=point_id,
                vector=chunk.embedding,
                payload={
                    "content": chunk.content,
                    **chunk.metadata.dict()
                }
            )
            points.append(point)
        
        # Upload points in batches
        if points:
            self.qdrant.upsert(
                collection_name="code_chunks",
                points=points
            )
        
        return [p.id for p in points]
    
    async def process_directory(self, directory: str, recursive: bool = True) -> Dict[str, List[str]]:
        """
        Process all supported files in a directory.
        
        Args:
            directory: Directory to process
            recursive: Whether to process subdirectories
            
        Returns:
            Dict[str, List[str]]: Mapping of files to their stored point IDs
            
        Metadata:
            - Dependencies: process_file
            - Performance: Parallel async processing
            - Error Handling: Directory traversal, file errors
        """
        results = {}
        path = Path(directory)
        
        pattern = '**/*' if recursive else '*'
        for file_path in path.glob(pattern):
            if file_path.is_file() and detect_language(str(file_path)) != Language.UNKNOWN:
                try:
                    point_ids = await self.process_file(str(file_path))
                    results[str(file_path)] = point_ids
                except Exception as e:
                    # Log error and continue with other files
                    print(f"Error processing {file_path}: {e}")
        
        return results
