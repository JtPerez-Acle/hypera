"""
Tests for basic metadata extraction functionality.
"""
from textwrap import dedent
import pytest

from src.metadata.parsing.extractors import MetadataExtractor, MetadataRequest
from src.metadata.parsing.types import MetadataExtractionLevel

@pytest.fixture
def extractor():
    """Create a metadata extractor instance."""
    return MetadataExtractor()

@pytest.fixture
def basic_code_sample():
    """Basic code sample for testing."""
    return dedent("""
    from typing import List, Optional
    
    def process_items(items: List[str]) -> Optional[dict]:
        if not items:
            return None
        return {"count": len(items)}
    """)

class TestBasicExtraction:
    """Test basic metadata extraction capabilities."""

    def test_minimal_extraction(self, extractor, basic_code_sample):
        """Test minimal metadata extraction level."""
        request = MetadataRequest(
            extraction_level=MetadataExtractionLevel.MINIMAL
        )

        metadata = extractor.extract(basic_code_sample, "python", request)

        assert metadata.success
        assert "typing.List" in metadata.imports
        assert len(metadata.functions) == 1
        assert metadata.functions[0]["name"] == "process_items"

    def test_error_handling(self, extractor):
        """Test handling of invalid code."""
        invalid_code = "def invalid_python( syntax error"
        request = MetadataRequest()

        metadata = extractor.extract(invalid_code, "python", request)

        assert not metadata.success
        assert metadata.error is not None

    def test_empty_code(self, extractor):
        """Test handling of empty code."""
        request = MetadataRequest()

        metadata = extractor.extract("", "python", request)

        assert metadata.success
        assert len(metadata.imports) == 0
        assert len(metadata.functions) == 0
        assert len(metadata.classes) == 0

    def test_basic_type_handling(self, extractor):
        """Test basic type handling."""
        code = dedent("""
        def func(x: int, y: str = "") -> bool:
            return bool(x) and bool(y)
        """)
        request = MetadataRequest(
            extraction_level=MetadataExtractionLevel.MINIMAL
        )

        metadata = extractor.extract(code, "python", request)

        assert metadata.success
        assert len(metadata.functions) == 1
        func = metadata.functions[0]
        assert func["parameters"][0]["type"] == "int"
        assert func["parameters"][1]["type"] == "str"
        assert func["return_type"] == "bool"
