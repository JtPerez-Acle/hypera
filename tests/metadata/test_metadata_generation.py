"""Unit tests for metadata generation agent."""

import pytest
from src.metadata.metadata_manager import MetadataGenerationAgent
from src.metadata.types import MetadataRequest, MetadataExtractionLevel


@pytest.fixture
def agent():
    """Create a metadata generation agent for testing."""
    return MetadataGenerationAgent()


@pytest.fixture
def sample_code():
    """Sample code for testing."""
    return """
import os
from typing import List, Optional
from pathlib import Path

def process_files(
    paths: List[Path],
    pattern: Optional[str] = None
) -> List[str]:
    \"\"\"Process files matching a pattern.
    
    Args:
        paths: List of paths to search
        pattern: Optional glob pattern
        
    Returns:
        List of processed file names
    \"\"\"
    results = []
    for path in paths:
        if pattern and not path.match(pattern):
            continue
        results.append(path.name)
    return results

class FileProcessor:
    \"\"\"Process files in a directory.\"\"\"
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        
    async def scan(self, recursive: bool = False) -> List[Path]:
        \"\"\"Scan for files.
        
        Args:
            recursive: Whether to scan subdirectories
            
        Returns:
            List of found files
        \"\"\"
        pattern = "**/*" if recursive else "*"
        return list(self.base_dir.glob(pattern))
"""


@pytest.mark.asyncio
async def test_extract_metadata_basic(agent, sample_code):
    """Test basic metadata extraction."""
    request = MetadataRequest(
        code=sample_code,
        extraction_level=MetadataExtractionLevel.MINIMAL,
        include_types=True,
        include_dependencies=False,
        max_dependency_depth=1,
        include_docstrings=True,
        include_comments=False
    )
    
    metadata = await agent.extract_metadata(
        sample_code,
        "python",
        request
    )
    
    # Test imports
    assert "os" in metadata.imports
    assert "typing.List" in metadata.imports
    assert "typing.Optional" in metadata.imports
    assert "pathlib.Path" in metadata.imports
    
    # Test functions
    functions = {f["name"]: f for f in metadata.functions}
    assert "process_files" in functions
    
    process_files = functions["process_files"]
    assert process_files["params"] == ["paths", "pattern"]
    assert process_files["return_type"] == "List[str]"
    
    # Test classes
    assert len(metadata.classes) == 1
    file_processor = metadata.classes[0]
    assert file_processor["name"] == "FileProcessor"
    assert sorted(file_processor["methods"]) == ["__init__", "scan"]
    
    # Test types
    assert metadata.types["base_dir"] == "Path"
    assert metadata.types["recursive"] == "bool"


@pytest.mark.asyncio
async def test_extract_metadata_with_invalid_code(agent):
    """Test metadata extraction with invalid code."""
    # Test with syntax error
    invalid_code = """
def invalid_function(
    missing_parenthesis:
"""
    
    request = MetadataRequest(
        code=invalid_code,
        extraction_level=MetadataExtractionLevel.MINIMAL
    )
    
    metadata = await agent.extract_metadata(
        invalid_code,
        "python",
        request
    )
    
    assert not metadata.success
    assert metadata.error is not None
    assert "SyntaxError" in metadata.error
    
    # Test with empty code
    empty_request = MetadataRequest(
        code="",
        extraction_level=MetadataExtractionLevel.MINIMAL
    )
    
    empty_metadata = await agent.extract_metadata(
        "",
        "python",
        empty_request
    )
    
    assert empty_metadata.success
    assert empty_metadata.imports == []
    assert empty_metadata.functions == []
    assert empty_metadata.classes == []


@pytest.mark.asyncio
async def test_extract_metadata_with_different_levels(agent, sample_code):
    """Test metadata extraction with different levels."""
    # Test MINIMAL level
    minimal_request = MetadataRequest(
        code=sample_code,
        extraction_level=MetadataExtractionLevel.MINIMAL
    )
    minimal_metadata = await agent.extract_metadata(
        sample_code,
        "python",
        minimal_request
    )
    assert minimal_metadata.success
    assert minimal_metadata.imports
    assert minimal_metadata.functions
    assert minimal_metadata.classes
    
    # Test STANDARD level
    standard_request = MetadataRequest(
        code=sample_code,
        extraction_level=MetadataExtractionLevel.STANDARD,
        include_types=True
    )
    standard_metadata = await agent.extract_metadata(
        sample_code,
        "python",
        standard_request
    )
    assert standard_metadata.success
    assert standard_metadata.types
    
    # Test DEEP level
    deep_request = MetadataRequest(
        code=sample_code,
        extraction_level=MetadataExtractionLevel.DEEP,
        include_dependencies=True
    )
    deep_metadata = await agent.extract_metadata(
        sample_code,
        "python",
        deep_request
    )
    assert deep_metadata.success
    assert deep_metadata.dependencies is not None
