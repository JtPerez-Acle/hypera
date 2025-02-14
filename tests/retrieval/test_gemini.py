"""
Tests for the Gemini-powered retrieval system.

This module tests the retrieval functionality, ensuring proper
integration with Gemini 1.5 Pro and correct context handling.
"""

import pytest
from datetime import datetime
from typing import List, Dict, Any
from src.retrieval.types import (
    RetrievalQuery,
    RetrievalFilter,
    QueryType,
    CodeContext
)
from src.retrieval.gemini import GeminiRetriever

@pytest.mark.asyncio
async def test_retrieval_basic(mock_gemini_client, mock_qdrant_client):
    """Test basic retrieval functionality."""
    # Initialize retriever
    retriever = GeminiRetriever()
    retriever.qdrant = mock_qdrant_client
    
    # Create test query
    query = RetrievalQuery(
        query="test function implementation",
        query_type=QueryType.CODE_SEARCH,
        max_results=5
    )
    
    # Perform retrieval
    result = await retriever.retrieve(query)
    
    # Verify result structure
    assert result.chunks is not None
    assert len(result.chunks) > 0
    assert result.similarity_scores is not None
    assert result.execution_time > 0
    assert result.query == query

@pytest.mark.asyncio
async def test_retrieval_with_filters(mock_gemini_client, mock_qdrant_client):
    """Test retrieval with various filters."""
    retriever = GeminiRetriever()
    retriever.qdrant = mock_qdrant_client
    
    # Create query with filters
    query = RetrievalQuery(
        query="test implementation",
        query_type=QueryType.CODE_SEARCH,
        filters=RetrievalFilter(
            languages=["python"],
            chunk_types=["function"],
            min_similarity=0.8
        )
    )
    
    # Verify filter construction
    search_filter = retriever._build_qdrant_filter(query)
    assert search_filter is not None
    
    # Perform retrieval
    result = await retriever.retrieve(query)
    
    # Verify filtered results
    assert all(chunk["language"] == "python" for chunk in result.chunks)
    assert all(chunk["chunk_type"] == "function" for chunk in result.chunks)
    assert all(score >= 0.8 for score in result.similarity_scores)

@pytest.mark.asyncio
async def test_context_enrichment(mock_gemini_client, mock_qdrant_client):
    """Test context enrichment using Gemini."""
    retriever = GeminiRetriever()
    retriever.qdrant = mock_qdrant_client
    
    # Create test chunks
    chunks = [
        {
            "file_path": "/test/file1.py",
            "chunk_type": "function",
            "content": "def test1(): pass"
        },
        {
            "file_path": "/test/file2.py",
            "chunk_type": "class",
            "content": "class TestClass: pass"
        }
    ]
    
    # Enrich context
    context = await retriever._enrich_context(chunks)
    
    # Verify context structure
    assert isinstance(context, CodeContext)
    assert context.dependencies is not None
    assert context.callers is not None
    assert context.related_files is not None
    assert context.documentation is not None

@pytest.mark.asyncio
async def test_retrieval_error_handling(mock_gemini_client, mock_qdrant_client):
    """Test error handling in retrieval."""
    retriever = GeminiRetriever()
    retriever.qdrant = mock_qdrant_client
    
    # Simulate Qdrant error
    mock_qdrant_client.search.side_effect = Exception("Search failed")
    
    # Create test query
    query = RetrievalQuery(
        query="test implementation",
        query_type=QueryType.CODE_SEARCH
    )
    
    # Verify error handling
    with pytest.raises(Exception):
        await retriever.retrieve(query)

@pytest.mark.asyncio
async def test_query_types(mock_gemini_client, mock_qdrant_client):
    """Test different query types."""
    retriever = GeminiRetriever()
    retriever.qdrant = mock_qdrant_client
    
    # Test each query type
    for query_type in QueryType:
        query = RetrievalQuery(
            query="test implementation",
            query_type=query_type
        )
        
        result = await retriever.retrieve(query)
        assert result.query.query_type == query_type

@pytest.mark.asyncio
async def test_large_context_handling(mock_gemini_client, mock_qdrant_client):
    """Test handling of large context windows."""
    retriever = GeminiRetriever()
    retriever.qdrant = mock_qdrant_client
    
    # Create a query that would result in large context
    query = RetrievalQuery(
        query="test implementation",
        query_type=QueryType.CODE_SEARCH,
        max_results=100  # Request many results
    )
    
    # Mock Qdrant to return many results
    mock_qdrant_client.search.return_value = [
        mock_qdrant_client.search.return_value[0]
        for _ in range(100)
    ]
    
    # Verify handling of large result set
    result = await retriever.retrieve(query)
    assert len(result.chunks) == 100
    assert result.context is not None  # Context should still be generated

def test_filter_validation():
    """Test validation of retrieval filters."""
    # Test valid filter
    valid_filter = RetrievalFilter(
        languages=["python", "rust"],
        chunk_types=["function", "class"],
        min_similarity=0.8
    )
    assert valid_filter.min_similarity >= 0
    assert valid_filter.min_similarity <= 1
    
    # Test invalid similarity
    with pytest.raises(ValueError):
        RetrievalFilter(min_similarity=1.5)
    
    # Test invalid date range
    with pytest.raises(ValueError):
        RetrievalFilter(
            date_range=(
                datetime(2025, 1, 1),
                datetime(2024, 1, 1)  # End before start
            )
        )
