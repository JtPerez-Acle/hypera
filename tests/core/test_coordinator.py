"""Tests for the system coordinator."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json
from datetime import datetime

from src.core.coordinator import SystemCoordinator
from src.config import ResourceConfig
from src.core.metrics import AgentMetrics, SystemMetrics
from src.reasoning.types import (
    CodeContext,
    ComprehensiveAnalysis,
    AgentAnalysis,
    CodeUnderstandingLevel,
    AnalysisType,
    Severity
)

@pytest.fixture
def test_code_context():
    """Create a test code context."""
    return CodeContext(
        code_snippet="def test(): pass",
        file_path="test.py",
        start_line=1,
        end_line=1,
        language="python",
        chunk_type="function",
        understanding_level=CodeUnderstandingLevel.BEHAVIORAL
    )

@pytest.fixture
def test_analysis():
    """Create a test analysis result."""
    return ComprehensiveAnalysis(
        query="Test analysis",
        code_context=CodeContext(
            code_snippet="def test(): pass",
            file_path="test.py",
            start_line=1,
            end_line=1,
            language="python",
            chunk_type="function",
            understanding_level=CodeUnderstandingLevel.BEHAVIORAL
        ),
        agent_analyses=[
            AgentAnalysis(
                agent_name="test_agent",
                analysis_type=AnalysisType.METADATA,
                severity=Severity.INFO,
                findings={
                    "token_usage": {
                        "gemini": 100,
                        "gpt4_mini": 50
                    }
                },
                supporting_evidence=["Test evidence"],
                confidence=0.95,
                success=True
            )
        ],
        metadata=None,
        summary="Test summary",
        recommendations=["Test recommendation"],
        success=True
    )

@pytest.fixture
def config():
    """Create a test configuration."""
    return ResourceConfig(
        gemini_max_tokens=1000,
        gpt4_mini_max_tokens=500,
        max_parallel_agents=2,
        cache_size_mb=100,
        enable_retrieval_cache=True
    )

@pytest.fixture
def coordinator(config):
    """Create a test coordinator instance."""
    return SystemCoordinator(
        gpt4_mini_key="test_key",
        gemini_key="test_key",
        config=config
    )

@pytest.mark.asyncio
async def test_coordinator_initialization(coordinator, config):
    """Test coordinator initialization."""
    assert coordinator.config == config
    assert coordinator.gemini is not None
    assert coordinator.gpt4_mini is not None
    assert coordinator.reasoning is not None
    assert isinstance(coordinator.agent_metrics, dict)
    assert isinstance(coordinator.system_metrics, SystemMetrics)
    assert isinstance(coordinator.cache, dict)

@pytest.mark.asyncio
async def test_analyze_code(coordinator, test_code_context, test_analysis):
    """Test code analysis."""
    with patch.object(coordinator.reasoning, 'analyze', return_value=test_analysis):
        result = await coordinator.analyze_code(test_code_context)
        assert result == test_analysis
        assert coordinator.system_metrics.total_analyses == 1
        assert coordinator.system_metrics.cache_misses == 1

@pytest.mark.asyncio
async def test_batch_analyze(coordinator, test_code_context, test_analysis):
    """Test batch analysis."""
    contexts = [test_code_context] * 3
    with patch.object(coordinator.reasoning, 'analyze', return_value=test_analysis):
        results = await coordinator.batch_analyze(contexts)
        assert len(results) == 3
        assert all(r == test_analysis for r in results)
        assert coordinator.system_metrics.total_analyses == 3

@pytest.mark.asyncio
async def test_error_handling(coordinator, test_code_context):
    """Test error handling."""
    error = Exception("Test error")
    with patch.object(coordinator.reasoning, 'analyze', side_effect=error):
        with pytest.raises(Exception) as exc_info:
            await coordinator.analyze_code(test_code_context)
        assert str(exc_info.value) == "Test error"

@pytest.mark.asyncio
async def test_metrics_tracking(coordinator, test_code_context, test_analysis):
    """Test metrics tracking."""
    with patch.object(coordinator.reasoning, 'analyze', return_value=test_analysis):
        await coordinator.analyze_code(test_code_context)
        metrics = coordinator.get_metrics()
        assert "test_agent" in metrics
        assert isinstance(metrics["test_agent"], AgentMetrics)
        assert metrics["test_agent"].success_rate == 1.0
        assert metrics["test_agent"].token_usage == {
            "gemini": 100,
            "gpt4_mini": 50
        }

@pytest.mark.asyncio
async def test_cache_management(coordinator, test_analysis):
    """Test cache management."""
    cache_key = "test_key"
    coordinator.cache[cache_key] = test_analysis
    assert coordinator.cache[cache_key] == test_analysis
    coordinator.clear_cache()
    assert len(coordinator.cache) == 0
