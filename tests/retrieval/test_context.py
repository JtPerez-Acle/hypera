"""
Tests for the context management system.

This module tests the context window management and optimization
strategies for Gemini's 2-million token context window.
"""

import pytest
from datetime import datetime
from typing import List, Dict, Any
from src.retrieval.types import (
    RetrievalQuery,
    RetrievalResult,
    QueryType,
    CodeContext
)
from src.retrieval.context import (
    ContextWindow,
    ContextManager
)

def create_test_result(content: str, score: float = 0.9) -> RetrievalResult:
    """Helper to create test retrieval results."""
    return RetrievalResult(
        query=RetrievalQuery(
            query="test query",
            query_type=QueryType.CODE_SEARCH
        ),
        chunks=[{
            "content": content,
            "file_path": "/test/file.py",
            "chunk_type": "function"
        }],
        similarity_scores=[score],
        execution_time=0.1,
        total_chunks_searched=1
    )

def test_context_window_initialization():
    """Test context window initialization."""
    window = ContextWindow()
    assert window.max_tokens == 2_000_000  # Gemini's context size
    assert window.current_tokens == 0
    assert window.contents == []

def test_context_window_capacity():
    """Test context window capacity management."""
    window = ContextWindow()
    
    # Test adding content within capacity
    assert window.can_add(1_000_000)
    assert window.add_content({"test": "content"}, 1_000_000)
    
    # Test exceeding capacity
    assert not window.can_add(1_500_000)
    assert not window.add_content({"test": "more"}, 1_500_000)
    
    # Test exact capacity
    remaining = window.max_tokens - window.current_tokens
    assert window.can_add(remaining)
    assert not window.can_add(remaining + 1)

def test_context_window_clearing():
    """Test context window clearing."""
    window = ContextWindow()
    window.add_content({"test": "content"}, 1000)
    assert window.current_tokens > 0
    
    window.clear()
    assert window.current_tokens == 0
    assert window.contents == []

@pytest.mark.asyncio
async def test_context_manager_basic():
    """Test basic context manager functionality."""
    manager = ContextManager()
    
    # Add a result
    result = create_test_result("def test(): pass")
    success = manager.add_result(result)
    
    assert success
    assert len(manager.get_current_context()) == 1
    assert manager.context_history == [result]

def test_context_manager_token_estimation():
    """Test token estimation logic."""
    manager = ContextManager()
    
    # Test various content types
    assert manager._estimate_tokens("short text") < manager._estimate_tokens("longer text content")
    assert manager._estimate_tokens("") == 0
    
    # Test code content
    code = """
    def complex_function():
        \"\"\"This is a docstring.\"\"\"
        return 42
    """
    assert manager._estimate_tokens(code) > manager._estimate_tokens("simple text")

def test_context_relevance_calculation():
    """Test relevance score calculation."""
    manager = ContextManager()
    
    # Test high relevance
    high_result = create_test_result("test", score=0.95)
    assert manager._calculate_relevance(high_result) > 0.9
    
    # Test low relevance
    low_result = create_test_result("test", score=0.5)
    assert manager._calculate_relevance(low_result) < 0.6
    
    # Test no scores
    no_scores = create_test_result("test")
    no_scores.similarity_scores = []
    assert manager._calculate_relevance(no_scores) == 0.0

def test_context_optimization():
    """Test context optimization strategies."""
    manager = ContextManager()
    
    # Fill context with varying relevance
    results = [
        create_test_result("high", score=0.9),
        create_test_result("medium", score=0.7),
        create_test_result("low", score=0.5)
    ]
    
    for result in results:
        manager.add_result(result)
    
    # Try to add new high-relevance content
    new_result = create_test_result("new high", score=0.95)
    
    # Force optimization by simulating full context
    manager.window.max_tokens = 100  # Small window for testing
    success = manager._optimize_window(new_result, 50)
    
    # Verify optimization preserved most relevant content
    context = manager.get_current_context()
    if context:
        scores = [manager._calculate_relevance(r) for r in context]
        assert all(score >= 0.7 for score in scores)  # Lower relevance content removed

def test_context_history():
    """Test context history management."""
    manager = ContextManager()
    
    # Add several results
    results = [
        create_test_result(f"test_{i}")
        for i in range(3)
    ]
    
    for result in results:
        manager.add_result(result)
    
    # Verify history
    assert len(manager.context_history) == 3
    assert manager.context_history == results
    
    # Clear context
    manager.clear_context()
    assert len(manager.context_history) == 0
    assert len(manager.get_current_context()) == 0

@pytest.mark.asyncio
async def test_large_context_optimization():
    """Test optimization with large context windows."""
    manager = ContextManager()
    
    # Create many results
    results = [
        create_test_result(
            f"def test_{i}(): pass",
            score=0.5 + (i / 20)  # Varying relevance
        )
        for i in range(10)
    ]
    
    # Add all results
    for result in results:
        manager.add_result(result)
    
    # Force optimization
    manager.window.max_tokens = 1000  # Small window for testing
    new_result = create_test_result("important new content", score=0.98)
    
    success = manager._optimize_window(new_result, 200)
    
    # Verify most relevant content was kept
    context = manager.get_current_context()
    if context:
        scores = [manager._calculate_relevance(r) for r in context]
        assert all(score >= 0.8 for score in scores)  # Only high relevance kept
