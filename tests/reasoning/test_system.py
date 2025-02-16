"""Tests for the reasoning system."""

import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

import pytest
from pydantic import BaseModel

from src.retrieval.gemini import GeminiRetriever
from src.retrieval.types import GeminiConfig
from src.reasoning.agents.system import ReasoningSystem
from src.reasoning.agents.metadata_agent import MetadataGenerationAgent
from src.reasoning.agents.base import ResponseDataDict
from src.reasoning.types import (
    CodeContext,
    AgentAnalysis,
    GPT4MiniModel,
    CodeUnderstandingLevel,
    ComprehensiveAnalysis
)

@pytest.fixture
def mock_gemini_retriever():
    """Create mock Gemini retriever."""
    mock = MagicMock(spec=GeminiRetriever)
    mock.get_context = AsyncMock(return_value={
        "imports": ["pandas", "numpy"],
        "functions": [{
            "name": "process_data",
            "params": ["df"],
            "return_type": "DataFrame"
        }],
        "classes": [{
            "name": "DataProcessor",
            "methods": ["process_data"]
        }]
    })
    return mock

@pytest.fixture
def mock_gpt4_mini():
    """Create mock GPT4Mini model."""
    mock = MagicMock(spec=GPT4MiniModel)
    mock.generate = AsyncMock(return_value={
        "token_usage": {"prompt": 150, "completion": 100},
        "completion": "Identified key patterns: data processing pipeline"
    })
    return mock

@pytest.fixture
def mock_agent_response() -> ResponseDataDict:
    """Create mock agent response."""
    return {
        "agent_name": "test_agent",
        "understanding_level": "behavioral",
        "findings": {
            "patterns": ["data processing"],
            "complexity": "low"
        },
        "confidence": 0.95,
        "supporting_evidence": ["clear data flow", "well-documented"],
        "warnings": None
    }

@pytest.fixture
def metadata_agent(mock_gemini_retriever, mock_gpt4_mini, mock_agent_response):
    """Create metadata agent."""
    agent = MetadataGenerationAgent(
        model=mock_gpt4_mini,
        gemini_retriever=mock_gemini_retriever
    )
    
    # Mock the agent's analyze method
    agent.agent.run = AsyncMock(return_value=mock_agent_response)
    return agent

@pytest.fixture
def test_code_context():
    """Create a test code context."""
    return CodeContext(
        code_snippet="""
import pandas as pd
import numpy as np

class DataProcessor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
    def process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        # Apply transformations based on config
        if self.config.get('normalize'):
            df = (df - df.mean()) / df.std()
        return df
""",
        file_path="src/processor.py",
        start_line=1,
        end_line=12,
        language="python",
        imports=["pandas", "numpy"],
        dependencies=[],
        metadata=None
    )


@pytest.mark.asyncio
async def test_system_initialization(metadata_agent, mock_gemini_retriever, mock_gpt4_mini):
    """Test ReasoningSystem initialization."""
    system = ReasoningSystem(
        metadata_extractor=metadata_agent,
        gemini_retriever=mock_gemini_retriever,
        model=mock_gpt4_mini
    )
    
    assert system.metadata_extractor == metadata_agent
    assert system.gemini_retriever == mock_gemini_retriever
    assert system.model == mock_gpt4_mini

@pytest.mark.asyncio
async def test_comprehensive_analysis(metadata_agent, mock_gemini_retriever, mock_gpt4_mini):
    """Test comprehensive code analysis."""
    system = ReasoningSystem(
        metadata_extractor=metadata_agent,
        gemini_retriever=mock_gemini_retriever,
        model=mock_gpt4_mini
    )
    
    code_context = CodeContext(
        code_snippet="def process_data(df):\n    return df.mean()",
        file_path="test.py",
        start_line=1,
        end_line=2,
        language="python",
        understanding_level=CodeUnderstandingLevel.BEHAVIORAL
    )
    
    analysis = await system.analyze(code_context)
    
    assert isinstance(analysis, ComprehensiveAnalysis)
    assert analysis.code_context == code_context
    assert len(analysis.agent_analyses) > 0

@pytest.mark.asyncio
async def test_parallel_agent_execution(metadata_agent, mock_gemini_retriever, mock_gpt4_mini):
    """Test parallel execution of analysis agents."""
    system = ReasoningSystem(
        metadata_extractor=metadata_agent,
        gemini_retriever=mock_gemini_retriever,
        model=mock_gpt4_mini
    )
    
    code_context = CodeContext(
        code_snippet="def process_data(df):\n    return df.mean()",
        file_path="test.py",
        start_line=1,
        end_line=2,
        language="python",
        understanding_level=CodeUnderstandingLevel.BEHAVIORAL
    )
    
    analysis = await system.analyze(code_context)
    
    assert isinstance(analysis, ComprehensiveAnalysis)
    assert len(analysis.agent_analyses) > 0

@pytest.mark.asyncio
async def test_error_handling(metadata_agent, mock_gemini_retriever, mock_gpt4_mini):
    """Test error handling in ReasoningSystem."""
    system = ReasoningSystem(
        metadata_extractor=metadata_agent,
        gemini_retriever=mock_gemini_retriever,
        model=mock_gpt4_mini
    )
    
    # Test with invalid code context
    code_context = CodeContext(
        code_snippet="invalid python code @@@@",
        file_path="test.py",
        start_line=1,
        end_line=1,
        language="python",
        understanding_level=CodeUnderstandingLevel.BEHAVIORAL
    )
    
    analysis = await system.analyze(code_context)
    
    assert isinstance(analysis, ComprehensiveAnalysis)
    assert len(analysis.warnings) > 0
