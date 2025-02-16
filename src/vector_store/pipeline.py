"""
High-level interface for the vector storage pipeline.

This module provides a simple interface for processing code files
and storing their embeddings in the vector database.
"""

import asyncio
from typing import List, Optional, Dict
from pathlib import Path
from .schema import CodeChunkPayload, Language
from .chunking import chunk_python_file, detect_language
from .llm_metadata import LLMMetadataGenerator
from .client import get_qdrant_client
from .collections import ensure_collections, COLLECTIONS_CONFIG

class Pipeline:
    """
    Main pipeline for processing code files with LLM-based analysis.
    
    This class handles the process from basic code chunking to
    LLM-based metadata generation and storage in Qdrant.
    """
    
    def __init__(self, gemini_api_key: str):
        """Initialize the pipeline components."""
        self.qdrant = get_qdrant_client()
        self.llm_generator = LLMMetadataGenerator(gemini_api_key)
        ensure_collections()
    
    async def process_file(self, file_path: str) -> List[str]:
        """
        Process a single file with LLM-enhanced analysis.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            List[str]: IDs of the stored points
        """
        language = detect_language(file_path)
        chunks: List[CodeChunkPayload] = []
        
        # Basic structural chunking
        if language == Language.PYTHON:
            chunks.extend(chunk_python_file(file_path))
        else:
            raise NotImplementedError(f"Language {language} not yet supported")
        
        if not chunks:
            return []
        
        # Enrich with LLM-generated metadata
        enriched_chunks = await self.llm_generator.analyze_chunks(chunks)
        
        # Store in Qdrant
        points = []
        for chunk in enriched_chunks:
            points.append({
                "id": f"{file_path}:{chunk.metadata.start_line}",
                "payload": chunk.dict(),
                "vector": chunk.embedding if chunk.embedding else []
            })
        
        collection = self.qdrant.get_collection("code_chunks")
        result = await collection.upsert(points=points)
        return [str(p.id) for p in result.points]
    
    async def process_directory(
        self,
        directory: str,
        recursive: bool = True
    ) -> Dict[str, List[str]]:
        """
        Process all supported files in a directory.
        
        Args:
            directory: Directory to process
            recursive: Whether to process subdirectories
            
        Returns:
            Dict[str, List[str]]: Mapping of files to their stored point IDs
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
                    print(f"Error processing {file_path}: {e}")
        
        return results
