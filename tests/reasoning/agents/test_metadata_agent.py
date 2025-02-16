"""Tests for the metadata agent."""
import pytest
from unittest.mock import AsyncMock, MagicMock

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

@pytest.fixture
def mock_metadata():
    """Create mock metadata."""
    return CodeMetadata(
        imports=["import os", "from typing import List"],
        functions=[{
            "name": "process_data",
            "params": ["items"],
            "return_type": "None"
        }],
        classes=[],
        types={"process_data": "List[str] -> None"},
        dependencies={"os": [], "typing": ["List"]},
        docstrings={"process_data": "Process input data"},
        comments=["# Process data items"],
        success=True
    )

@pytest.fixture
def mock_metadata_extractor(mock_metadata):
    """Create a mock metadata extractor."""
    extractor = MagicMock(spec=MetadataGenerationAgent)
    extractor.extract_metadata = AsyncMock(return_value=mock_metadata)
    return extractor

@pytest.fixture
def code_context():
    """Create a test code context."""
    return CodeContext(
        code_snippet="""def process_data(items: List[str]) -> None:
    \"\"\"Process input data\"\"\"
    for item in items:
        print(item)""",
        file_path="test.py",
        start_line=1,
        end_line=5,
        language="python",
        chunk_type="function",
        understanding_level=CodeUnderstandingLevel.BEHAVIORAL
    )

@pytest.mark.asyncio
async def test_agent_initialization():
    """Test metadata agent initialization."""
    agent = MetadataGenerationAgent()
    assert agent is not None

@pytest.mark.asyncio
async def test_extract_metadata(code_context):
    """Test metadata extraction."""
    agent = MetadataGenerationAgent()
    request = MetadataRequest(
        extraction_level=MetadataExtractionLevel.COMPREHENSIVE,
        include_types=True,
        include_docstrings=True,
        include_dependencies=True,
        code=code_context.code_snippet
    )
    metadata = await agent.extract_metadata(
        code_context.code_snippet,
        code_context.language,
        request
    )
    assert isinstance(metadata, CodeMetadata)
    assert metadata.success
    assert len(metadata.functions) > 0

@pytest.mark.asyncio
async def test_metadata_requirements(code_context, mock_metadata_extractor):
    """Test metadata extraction requirements."""
    agent = MetadataGenerationAgent()
    for level in MetadataExtractionLevel:
        request = MetadataRequest(
            extraction_level=level,
            include_types=True,
            include_docstrings=True,
            include_dependencies=True,
            code=code_context.code_snippet
        )
        metadata = await agent.extract_metadata(
            code_context.code_snippet,
            code_context.language,
            request
        )
        assert metadata.success
        assert len(metadata.functions) > 0
        assert metadata.types is not None
        if level in (MetadataExtractionLevel.DEEP, MetadataExtractionLevel.COMPREHENSIVE):
            assert metadata.control_flow is not None

@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling."""
    agent = MetadataGenerationAgent()
    invalid_code = """def invalid_function(
    print("Missing closing parenthesis"
"""
    request = MetadataRequest(
        extraction_level=MetadataExtractionLevel.STANDARD,
        include_types=True,
        include_docstrings=True,
        include_dependencies=True,
        code=invalid_code
    )
    metadata = await agent.extract_metadata(
        invalid_code,
        "python",
        request
    )
    assert not metadata.success
    assert metadata.error is not None
    assert "SyntaxError" in metadata.error

@pytest.mark.asyncio
async def test_complex_code_analysis(mock_metadata_extractor):
    """Test analysis of complex code."""
    code = """from typing import Dict, List, Optional, Any

class DataProcessor:
    def __init__(self, data: List[Dict[str, Any]]):
        self.data = data
        self.processed = False
    
    def process(self) -> Optional[List[Dict[str, Any]]]:
        \"\"\"Process the data items.
        
        Returns:
            Optional[List[Dict[str, Any]]]: Processed data or None if empty
        \"\"\"
        if not self.data:
            return None
        
        result = []
        for item in self.data:
            if self._validate(item):
                result.append(self._transform(item))
        return result
    
    def _validate(self, item: Dict[str, Any]) -> bool:
        return all(k in item for k in ["id", "value"])
    
    def _transform(self, item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": item["id"],
            "processed_value": item["value"] * 2
        }"""
    request = MetadataRequest(
        extraction_level=MetadataExtractionLevel.COMPREHENSIVE,
        include_types=True,
        include_docstrings=True,
        include_dependencies=True,
        code=code
    )
    agent = MetadataGenerationAgent()
    metadata = await agent.extract_metadata(code, "python", request)
    assert isinstance(metadata, CodeMetadata)
    assert metadata.success
    assert len(metadata.classes) == 1
    # Methods are now stored in the class definition
    assert len(metadata.classes[0]["methods"]) >= 3  # __init__, process, _validate, _transform
    assert metadata.imports == ["typing.Dict", "typing.List", "typing.Optional", "typing.Any"]
    assert "process" in metadata.docstrings
    assert metadata.types is not None
