"""Tests for the reasoning module."""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.reasoning.agents import (
    BehavioralAnalyzer,
    SecurityAnalyzer,
    PatternAnalyzer,
    MetricsAnalyzer,
    DependencyAnalyzer,
    ReasoningSystem,
)
from src.reasoning.types import (
    AgentAnalysis,
    CodeContext,
    SecurityIssue,
    DesignPattern,
    CodeMetrics,
    DependencyInfo,
)
from src.metadata.extractor import MetadataExtractor
from src.retrieval.gemini import GeminiRetriever


@pytest.fixture
def code_context():
    """Sample code context for testing."""
    return CodeContext(
        code_snippet="""
def process_data(data: dict) -> dict:
    result = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = value.strip()
        elif isinstance(value, (int, float)):
            result[key] = value * 2
    return result
""",
        language="python",
        imports=[],
        dependencies=[]
    )


@pytest.fixture
def mock_metadata_extractor():
    """Mock metadata extractor."""
    extractor = AsyncMock(spec=MetadataExtractor)
    extractor.extract.return_value = {
        "imports": ["from typing import Dict"],
        "dependencies": ["typing"],
    }
    return extractor


@pytest.fixture
def mock_gemini_retriever():
    """Mock Gemini retriever."""
    retriever = AsyncMock(spec=GeminiRetriever)
    retriever.retrieve.return_value = {
        "similar_code": ["def similar_function(data): ..."],
        "context": "This function processes dictionary data",
    }
    retriever.generate_summary.return_value = "A comprehensive analysis..."
    retriever.generate_recommendations.return_value = ["Improve error handling"]
    return retriever


@pytest.mark.asyncio
async def test_behavioral_analyzer(code_context, mock_metadata_extractor, mock_gemini_retriever):
    """Test behavioral analyzer."""
    analyzer = BehavioralAnalyzer(
        metadata_extractor=mock_metadata_extractor,
        gemini_retriever=mock_gemini_retriever
    )
    
    # Mock the agent run
    analyzer.agent.run = AsyncMock()
    analyzer.agent.run.return_value.data = AgentAnalysis(
        findings={
            "behavior": "Function mutates input data",
            "side_effects": ["Data transformation"],
        }
    )
    
    # Run analysis
    result = await analyzer.analyze(code_context)
    
    # Verify metadata extraction and Gemini retrieval were called
    mock_metadata_extractor.extract.assert_called_once()
    mock_gemini_retriever.retrieve.assert_called_once()
    
    # Verify analysis results
    assert "behavior" in result.findings
    assert "side_effects" in result.findings
    assert result.findings["behavior"] == "Function mutates input data"


@pytest.mark.asyncio
async def test_security_analyzer(code_context, mock_metadata_extractor, mock_gemini_retriever):
    """Test security analyzer."""
    analyzer = SecurityAnalyzer(
        metadata_extractor=mock_metadata_extractor,
        gemini_retriever=mock_gemini_retriever
    )
    
    # Mock the agent run
    analyzer.agent.run = AsyncMock()
    analyzer.agent.run.return_value.data = AgentAnalysis(
        findings={
            "issues": [
                {
                    "severity": "medium",
                    "description": "No input validation",
                    "recommendation": "Add type checking",
                }
            ]
        }
    )
    
    # Run analysis
    result = await analyzer.analyze(code_context)
    
    # Verify results
    assert len(result) == 1
    assert result[0].severity == "medium"
    assert "input validation" in result[0].description.lower()


@pytest.mark.asyncio
async def test_pattern_analyzer(code_context, mock_metadata_extractor, mock_gemini_retriever):
    """Test pattern analyzer."""
    analyzer = PatternAnalyzer(
        metadata_extractor=mock_metadata_extractor,
        gemini_retriever=mock_gemini_retriever
    )
    
    # Mock the agent run
    analyzer.agent.run = AsyncMock()
    analyzer.agent.run.return_value.data = AgentAnalysis(
        findings={
            "patterns": [
                {
                    "name": "Iterator",
                    "confidence": 0.9,
                    "description": "Uses dictionary iteration",
                }
            ]
        }
    )
    
    # Run analysis
    result = await analyzer.analyze(code_context)
    
    # Verify results
    assert len(result) == 1
    assert result[0].name == "Iterator"
    assert result[0].confidence == 0.9


@pytest.mark.asyncio
async def test_metrics_analyzer(code_context, mock_metadata_extractor, mock_gemini_retriever):
    """Test metrics analyzer."""
    analyzer = MetricsAnalyzer(
        metadata_extractor=mock_metadata_extractor,
        gemini_retriever=mock_gemini_retriever
    )
    
    # Mock the agent run
    analyzer.agent.run = AsyncMock()
    analyzer.agent.run.return_value.data = AgentAnalysis(
        findings={
            "metrics": {
                "complexity": 3,
                "maintainability": 85,
                "comment_ratio": 0.1,
            }
        }
    )
    
    # Run analysis
    result = await analyzer.analyze(code_context)
    
    # Verify results
    assert result.complexity == 3
    assert result.maintainability == 85
    assert result.comment_ratio == 0.1


@pytest.mark.asyncio
async def test_dependency_analyzer(code_context, mock_metadata_extractor, mock_gemini_retriever):
    """Test dependency analyzer."""
    analyzer = DependencyAnalyzer(
        metadata_extractor=mock_metadata_extractor,
        gemini_retriever=mock_gemini_retriever
    )
    
    # Mock the agent run
    analyzer.agent.run = AsyncMock()
    analyzer.agent.run.return_value.data = AgentAnalysis(
        findings={
            "dependencies": {
                "direct_deps": ["typing"],
                "indirect_deps": [],
                "external_deps": [],
            }
        }
    )
    
    # Run analysis
    result = await analyzer.analyze(code_context)
    
    # Verify results
    assert "typing" in result.direct_deps
    assert len(result.indirect_deps) == 0
    assert len(result.external_deps) == 0


@pytest.mark.asyncio
async def test_reasoning_system(code_context, mock_metadata_extractor, mock_gemini_retriever):
    """Test the complete reasoning system."""
    system = ReasoningSystem(
        metadata_extractor=mock_metadata_extractor,
        gemini_retriever=mock_gemini_retriever
    )
    
    # Mock all agent analyses
    system.agents["behavioral"].analyze = AsyncMock(return_value=AgentAnalysis(
        findings={"behavior": "Function processes dictionary data"}
    ))
    system.agents["security"].analyze = AsyncMock(return_value=[
        SecurityIssue(severity="low", description="Minor issue", recommendation="Fix it")
    ])
    system.agents["patterns"].analyze = AsyncMock(return_value=[
        DesignPattern(name="Iterator", confidence=0.9, description="Uses iteration")
    ])
    system.agents["metrics"].analyze = AsyncMock(return_value=CodeMetrics(
        complexity=3,
        maintainability=85,
        comment_ratio=0.1
    ))
    system.agents["dependencies"].analyze = AsyncMock(return_value=DependencyInfo(
        direct_deps=["typing"],
        indirect_deps=[],
        external_deps=[]
    ))
    
    # Run complete analysis
    result = await system.analyze("Analyze this code", code_context)
    
    # Verify comprehensive results
    assert result.query == "Analyze this code"
    assert len(result.agent_analyses) == 1
    assert len(result.security_issues) == 1
    assert len(result.design_patterns) == 1
    assert result.metrics.complexity == 3
    assert "typing" in result.dependencies.direct_deps
    assert result.summary == "A comprehensive analysis..."
    assert result.recommendations == ["Improve error handling"]
