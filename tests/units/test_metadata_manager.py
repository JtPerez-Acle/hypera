"""Unit tests for metadata extraction and processing."""

import pytest
from src.metadata.metadata_manager import process_code_chunk, CodeChunk
from src.metadata.types import CodeMetadata, MetadataRequest, MetadataExtractionLevel

@pytest.fixture
def sample_code():
    """Sample code for testing."""
    return """
import pandas as pd
from typing import List, Optional

class Parent:
    def method(self) -> None:
        pass

class Child(Parent):
    def __init__(self, value: int = 0):
        self.value = value

    def process_items(self, items: List[int]) -> Optional[int]:
        if not items:
            return None
        return sum(items) + self.value
    """

@pytest.mark.asyncio
async def test_process_code_chunk(sample_code):
    """Test metadata extraction from code chunk."""
    metadata = await process_code_chunk(sample_code)

    # Test imports
    assert "pandas" in metadata.imports
    assert "typing.List" in metadata.imports
    assert "typing.Optional" in metadata.imports

    # Test classes
    assert len(metadata.classes) == 2
    class_names = [c["name"] for c in metadata.classes]
    assert "Parent" in class_names
    assert "Child" in class_names

    # Test methods
    parent_class = next(c for c in metadata.classes if c["name"] == "Parent")
    child_class = next(c for c in metadata.classes if c["name"] == "Child")
    
    assert "method" in parent_class["methods"]
    assert "__init__" in child_class["methods"]
    assert "process_items" in child_class["methods"]

    # Test inheritance
    assert child_class["base_classes"] == ["Parent"]

@pytest.mark.asyncio
async def test_process_code_chunk_with_empty_code():
    """Test metadata extraction from empty code."""
    metadata = await process_code_chunk("")

    assert isinstance(metadata, CodeMetadata)
    assert len(metadata.imports) == 0
    assert len(metadata.classes) == 0
    assert len(metadata.functions) == 0

@pytest.mark.asyncio
async def test_process_code_chunk_with_only_imports():
    """Test metadata extraction with only imports."""
    code = """
import os
from sys import path
from typing import Optional, List as TypeList
"""

    metadata = await process_code_chunk(code)

    assert set(metadata.imports) == {
        "os",
        "sys.path",
        "typing.Optional",
        "typing.List"
    }
    assert len(metadata.classes) == 0
    assert len(metadata.functions) == 0

@pytest.mark.asyncio
async def test_process_code_chunk_with_complex_types():
    """Test metadata extraction with complex type annotations."""
    code = """
from typing import Dict, List, Optional, Union, Any

class DataProcessor:
    def process_data(
        self,
        items: List[Dict[str, Any]],
        config: Optional[Dict[str, Union[str, int]]] = None
    ) -> List[str]:
        pass
"""

    metadata = await process_code_chunk(code)

    assert len(metadata.classes) == 1
    assert "DataProcessor" in [c["name"] for c in metadata.classes]
    
    processor_class = next(c for c in metadata.classes if c["name"] == "DataProcessor")
    assert "process_data" in processor_class["methods"]

    # Test type annotations
    assert "List[Dict[str, Any]]" in str(metadata.types.values())
    assert "Optional[Dict[str, Union[str, int]]]" in str(metadata.types.values())

@pytest.mark.asyncio
async def test_code_chunk_dataclass():
    """Test CodeChunk dataclass."""
    metadata = CodeMetadata(
        imports=["os"],
        functions=[],
        classes=[],
        types={},
        dependencies={}
    )

    chunk = CodeChunk(
        code="import os",
        metadata=metadata,
        start_line=1,
        end_line=1,
        file_path="test.py"
    )

    assert chunk.code == "import os"
    assert chunk.metadata == metadata
    assert chunk.start_line == 1
    assert chunk.end_line == 1
    assert chunk.file_path == "test.py"
