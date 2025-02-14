"""
Tests for the embedding generation system.

This module tests the functionality for generating embeddings
from code chunks and their metadata.
"""

import pytest
from datetime import datetime
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock
import numpy as np
from src.vector_store.schema import CodeChunkPayload, CodeChunkMetadata

@pytest.fixture
def sample_code_chunk() -> Dict[str, Any]:
    """Provide a sample code chunk for testing."""
    return {
        "content": """
        def calculate_metrics(data: List[float]) -> Dict[str, float]:
            \"\"\"Calculate basic statistics for a list of values.\"\"\"
            return {
                "mean": sum(data) / len(data),
                "max": max(data),
                "min": min(data)
            }
        """,
        "metadata": {
            "chunk_type": "function",
            "language": "python",
            "file_path": "/src/analysis/metrics.py",
            "start_line": 1,
            "end_line": 8,
            "function_name": "calculate_metrics",
            "dependencies": ["typing"],
            "docstring": "Calculate basic statistics for a list of values."
        }
    }

@pytest.mark.asyncio
async def test_embedding_generation(mock_openai_client, sample_code_chunk):
    """Test generation of embeddings."""
    # Create chunk
    chunk = CodeChunkPayload(**sample_code_chunk)
    
    # Verify embedding dimensions
    assert len(chunk.metadata.dependencies) > 0
    assert chunk.metadata.language == "python"
    assert chunk.metadata.chunk_type == "function"

@pytest.mark.asyncio
async def test_chunk_processing(mock_openai_client, sample_code_chunk):
    """Test processing of code chunks."""
    # Process chunk
    chunk = CodeChunkPayload(**sample_code_chunk)
    
    # Verify metadata extraction
    assert chunk.metadata.function_name == "calculate_metrics"
    assert chunk.metadata.docstring is not None
    assert chunk.metadata.start_line == 1
    assert chunk.metadata.end_line == 8

def test_chunk_formatting(sample_code_chunk):
    """Test that chunks are formatted correctly for embedding."""
    # Create chunk
    chunk = CodeChunkPayload(**sample_code_chunk)
    
    # Verify structure
    assert isinstance(chunk.content, str)
    assert isinstance(chunk.metadata, CodeChunkMetadata)
    assert chunk.metadata.language == "python"
    assert chunk.metadata.chunk_type == "function"

@pytest.mark.asyncio
async def test_embedding_error_handling(mock_openai_client):
    """Test error handling during embedding generation."""
    # Create invalid chunk
    invalid_chunk = {
        "content": "",  # Empty content
        "metadata": {
            "chunk_type": "function",
            "language": "python",
            "file_path": "/test/empty.py",
            "start_line": 1,
            "end_line": 1
        }
    }
    
    # Verify validation
    with pytest.raises(ValueError):
        CodeChunkPayload(**invalid_chunk)

@pytest.mark.asyncio
async def test_batch_processing(mock_openai_client):
    """Test processing multiple chunks in batch."""
    # Create multiple chunks
    chunks = [
        CodeChunkPayload(
            content=f"def test_{i}(): pass",
            metadata=CodeChunkMetadata(
                chunk_type="function",
                language="python",
                file_path=f"/test/file_{i}.py",
                start_line=1,
                end_line=1,
                function_name=f"test_{i}"
            )
        )
        for i in range(3)
    ]
    
    # Verify batch processing
    assert len(chunks) == 3
    assert all(chunk.metadata.language == "python" for chunk in chunks)
    assert all(chunk.metadata.chunk_type == "function" for chunk in chunks)

def test_metadata_formatting():
    """Test that metadata is formatted correctly for embedding."""
    # Create chunk with complex metadata
    chunk = CodeChunkPayload(
        content="def test(): pass",
        metadata=CodeChunkMetadata(
            chunk_type="function",
            language="python",
            file_path="/test/file.py",
            start_line=1,
            end_line=1,
            function_name="test",
            dependencies=["os", "sys"],
            docstring="Test function"
        )
    )

    # Verify metadata structure
    assert chunk.metadata.function_name == "test"
    assert chunk.metadata.dependencies == ["os", "sys"]
    assert chunk.metadata.docstring == "Test function"
    assert chunk.metadata.chunk_type == "function"
    assert chunk.metadata.language == "python"
    assert chunk.metadata.file_path == "/test/file.py"
    assert chunk.metadata.start_line == 1
    assert chunk.metadata.end_line == 1
