"""Tests for the reasoning module."""

from typing import Dict, List, Optional, Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.metadata.metadata_manager import MetadataGenerationAgent
from src.metadata.types import (
    CodeMetadata,
    MetadataRequest,
    MetadataExtractionLevel
)
from src.reasoning.types import (
    AgentAnalysis,
    AnalysisType,
    Severity,
    CodeContext,
    CodeUnderstandingLevel
)

from src.reasoning.agents import (
    BehavioralAnalyzer,
    SecurityAnalyzer,
    PatternAnalyzer,
    MetricsAnalyzer,
    DependencyAnalyzer,
    ReasoningSystem,
)
from src.retrieval.gemini import GeminiRetriever, RetrievalResult, RetrievalQuery


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
        dependencies=[],
        file_path="test.py",
        start_line=1,
        end_line=10
    )


@pytest.fixture
def mock_metadata_extractor():
    """Mock metadata extractor."""
    extractor = AsyncMock()
    metadata = CodeMetadata(
        imports=["from typing import Dict"],
        dependencies={
            "typing": ["Dict"],
            "external_lib": ["ExternalClass"],
            "utils": ["helper_function"]
        },
        file_path="test.py",
        start_line=1,
        end_line=10,
        language="python"
    )
    extractor.extract_metadata.return_value = metadata
    extractor.analyze.return_value = metadata
    return extractor


@pytest.fixture
def mock_gemini_retriever():
    """Mock Gemini retriever."""
    retriever = AsyncMock(spec=GeminiRetriever)
    retriever.retrieve.return_value = RetrievalResult(
        query=RetrievalQuery(query="test query"),
        chunks=[{"content": "def similar_function(data): ...", "file": "test.py"}],
        similarity_scores=[0.95],
        execution_time=0.5,
        total_chunks_searched=10,
        context={
            "code_snippet": "def similar_function(data): ...",
            "file_path": "test.py",
            "start_line": 1,
            "end_line": 3,
            "language": "python",
            "dependencies": ["test_dep"],
            "callers": ["test_caller"],
            "related_files": ["test.py"],
            "documentation": "This function processes dictionary data",
            "metadata": {}
        }
    )
    return retriever


@pytest.fixture
def metadata_agent():
    """Create a metadata agent for testing."""
    return MetadataGenerationAgent()


@pytest.fixture
def mock_agent_analysis():
    """Create a mock agent analysis."""
    return AgentAnalysis(
        agent_name="test_agent",
        findings={"test": "value"},
        supporting_evidence=["test evidence"],
        confidence=0.8,
        analysis_type=AnalysisType.BEHAVIORAL,
        severity=Severity.INFO
    )


@pytest.mark.asyncio
async def test_behavioral_analyzer(code_context, mock_metadata_extractor):
    """Test behavioral analysis."""
    analyzer = BehavioralAnalyzer(metadata_extractor=mock_metadata_extractor)
    
    analysis = await analyzer.analyze(code_context)
    
    assert isinstance(analysis, AgentAnalysis)
    assert analysis.agent_name == "behavioral_agent"
    assert analysis.analysis_type == AnalysisType.BEHAVIORAL
    assert analysis.severity in [Severity.INFO, Severity.WARNING, Severity.ERROR]
    assert len(analysis.supporting_evidence) > 0


@pytest.mark.asyncio
async def test_security_analyzer(code_context, mock_metadata_extractor):
    """Test security analysis."""
    analyzer = SecurityAnalyzer(metadata_extractor=mock_metadata_extractor)
    
    analysis = await analyzer.analyze(code_context)
    
    assert isinstance(analysis, AgentAnalysis)
    assert analysis.agent_name == "security_agent"
    assert analysis.analysis_type == AnalysisType.SECURITY
    assert analysis.severity in [Severity.INFO, Severity.WARNING, Severity.ERROR]
    assert len(analysis.supporting_evidence) > 0


@pytest.mark.asyncio
async def test_pattern_analyzer(code_context, mock_metadata_extractor):
    """Test pattern analysis."""
    analyzer = PatternAnalyzer(metadata_extractor=mock_metadata_extractor)
    
    analysis = await analyzer.analyze(code_context)
    
    assert isinstance(analysis, AgentAnalysis)
    assert analysis.agent_name == "pattern_agent"
    assert analysis.analysis_type == AnalysisType.PATTERNS
    assert analysis.severity in [Severity.INFO, Severity.WARNING, Severity.ERROR]
    assert len(analysis.supporting_evidence) > 0


@pytest.mark.asyncio
async def test_metrics_analyzer(code_context, mock_metadata_extractor):
    """Test metrics analysis."""
    analyzer = MetricsAnalyzer(metadata_extractor=mock_metadata_extractor)
    
    analysis = await analyzer.analyze(code_context)
    
    assert isinstance(analysis, AgentAnalysis)
    assert analysis.agent_name == "metrics_agent"
    assert analysis.analysis_type == AnalysisType.METRICS
    assert analysis.severity in [Severity.INFO, Severity.WARNING, Severity.ERROR]
    assert len(analysis.supporting_evidence) > 0


@pytest.mark.asyncio
async def test_dependency_analyzer(code_context, mock_metadata_extractor):
    """Test dependency analysis."""
    analyzer = DependencyAnalyzer(metadata_extractor=mock_metadata_extractor)
    
    analysis = await analyzer.analyze(code_context)
    
    assert isinstance(analysis, AgentAnalysis)
    assert analysis.agent_name == "dependency_agent"
    assert analysis.analysis_type == AnalysisType.DEPENDENCIES
    assert analysis.severity in [Severity.INFO, Severity.WARNING, Severity.ERROR]
    assert len(analysis.supporting_evidence) > 0


@pytest.mark.asyncio
async def test_reasoning_system(code_context, mock_metadata_extractor, mock_gemini_retriever):
    """Test the complete reasoning system."""
    system = ReasoningSystem(
        metadata_extractor=mock_metadata_extractor,
        gemini_retriever=mock_gemini_retriever
    )
    
    # Mock all agent analyses
    system.agents["behavioral"].analyze = AsyncMock(return_value=AgentAnalysis(
        agent_name="behavioral_agent",
        findings={"behavior": "Function processes dictionary data"},
        supporting_evidence=["Test evidence"],
        confidence=0.8,
        analysis_type=AnalysisType.BEHAVIORAL,
        severity=Severity.INFO
    ))
    
    system.agents["security"].analyze = AsyncMock(return_value=AgentAnalysis(
        agent_name="security_agent",
        findings={"security": "No major issues found"},
        supporting_evidence=["Test evidence"],
        confidence=0.9,
        analysis_type=AnalysisType.SECURITY,
        severity=Severity.INFO
    ))
    
    system.agents["patterns"].analyze = AsyncMock(return_value=AgentAnalysis(
        agent_name="pattern_agent",
        findings={"patterns": "Common data processing pattern"},
        supporting_evidence=["Test evidence"],
        confidence=0.7,
        analysis_type=AnalysisType.PATTERNS,
        severity=Severity.INFO
    ))
    
    analysis = await system.analyze(code_context)
    
    assert isinstance(analysis, ComprehensiveAnalysis)
    assert len(analysis.agent_analyses) > 0
    assert analysis.code_context == code_context
    assert analysis.summary
    assert isinstance(analysis.recommendations, list)


@pytest.mark.asyncio
async def test_basic_metadata_extraction(metadata_agent):
    """Test basic metadata extraction from simple code."""
    code = """
import os
from typing import List

def process_data(items: List[str]) -> None:
    \"\"\"Process a list of items.\"\"\"
    for item in items:
        print(item)
    """
    
    request = MetadataRequest(
        extraction_level=MetadataExtractionLevel.MINIMAL,
        include_types=True,
        include_docstrings=True
    )
    
    metadata = await metadata_agent.extract_metadata(code, "python", request)
    
    assert metadata.success
    assert len(metadata.imports) == 2
    assert "import os" in metadata.imports
    assert "from typing import List" in metadata.imports
    assert len(metadata.functions) == 1
    assert "process_data" in metadata.functions[0]
    assert metadata.docstrings
    assert "Process a list of items" in metadata.docstrings["process_data"]


@pytest.mark.asyncio
async def test_deep_metadata_extraction(metadata_agent):
    """Test deep metadata extraction with control and data flow analysis."""
    code = """
class DataProcessor:
    def __init__(self, data: List[str]):
        self.data = data
        self.processed = False
    
    def process(self) -> None:
        \"\"\"Process the data items.\"\"\"
        if not self.processed:
            for item in self.data:
                self._transform(item)
            self.processed = True
    
    def _transform(self, item: str) -> str:
        return item.upper()
"""
    
    request = MetadataRequest(
        extraction_level=MetadataExtractionLevel.MINIMAL,
        include_types=True,
        include_docstrings=True,
        include_dependencies=True
    )
    
    metadata = await metadata_agent.extract_metadata(code, "python", request)
    
    assert metadata.success
    assert len(metadata.classes) == 1
    assert metadata.classes[0]["name"] == "DataProcessor"
    assert len(metadata.functions) == 3
    assert metadata.control_flow is not None
    assert metadata.data_flow is not None
    assert metadata.docstrings
    assert "Process the data items" in metadata.docstrings["process"]


@pytest.mark.asyncio
async def test_comprehensive_metadata_extraction(metadata_agent):
    """Test comprehensive metadata extraction with cross-file references."""
    code = """
from external_lib import ExternalClass
from .utils import helper_function

class AdvancedProcessor(ExternalClass):
    def __init__(self):
        super().__init__()
        self.helper = helper_function
    
    def process(self, data: Dict[str, Any]) -> Optional[List[str]]:
        \"\"\"Process data using external dependencies.\"\"\"
        if not data:
            return None
        return self.helper(data)
"""
    
    request = MetadataRequest(
        extraction_level=MetadataExtractionLevel.COMPREHENSIVE,
        include_types=True,
        include_docstrings=True,
        include_dependencies=True,
        max_dependency_depth=2
    )
    
    metadata = await metadata_agent.extract_metadata(code, "python", request)
    
    assert metadata.success
    assert len(metadata.imports) == 2
    assert metadata.dependencies
    assert "external_lib" in str(metadata.dependencies)
    assert metadata.cross_file_refs is not None
    assert metadata.dependency_depth == 2


@pytest.mark.asyncio
async def test_error_handling(metadata_agent):
    """Test error handling in metadata extraction."""
    # Test with invalid syntax
    code = """
def invalid_function(
    print("Missing closing parenthesis"
"""
    
    request = MetadataRequest(extraction_level=MetadataExtractionLevel.MINIMAL)
    metadata = await metadata_agent.extract_metadata(code, "python", request)
    
    assert not metadata.success
    assert metadata.error is not None
    assert "SyntaxError" in metadata.error
    
    # Test with runtime error
    code = """
def function():
    undefined_variable + 1
"""
    
    metadata = await metadata_agent.extract_metadata(code, "python", request)
    assert metadata.success  # Should still parse successfully
    assert len(metadata.functions) == 1


@pytest.mark.asyncio
async def test_type_extraction(metadata_agent):
    """Test extraction of type information."""
    code = """
from typing import List, Dict, Optional

class TypedClass:
    def __init__(self, items: List[str]):
        self.items: List[str] = items
        self.counts: Dict[str, int] = {}
    
    def process(self) -> Optional[Dict[str, int]]:
        if not self.items:
            return None
        for item in self.items:
            self.counts[item] = self.counts.get(item, 0) + 1
        return self.counts
"""
    
    request = MetadataRequest(
        extraction_level=MetadataExtractionLevel.DEEP,
        include_types=True
    )
    
    metadata = await metadata_agent.extract_metadata(code, "python", request)
    
    assert metadata.success
    assert metadata.types
    assert "List[str]" in str(metadata.types)
    assert "Dict[str, int]" in str(metadata.types)
    assert "Optional[Dict[str, int]]" in str(metadata.types)
