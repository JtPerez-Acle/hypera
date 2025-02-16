"""
Tests for advanced metadata extraction functionality.
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
def complex_code_sample():
    """Complex code sample for testing advanced features."""
    return dedent("""
    from typing import List, Dict, Optional, Any
    from dataclasses import dataclass
    from pathlib import Path
    import json

    @dataclass
    class DataProcessor:
        name: str
        config: Dict[str, Any]

        def process(self, data: List[dict]) -> Optional[dict]:
            if not data:
                return None
            self.processed += 1
            return {"processed": True, **data}
    """)

class TestAdvancedExtraction:
    """Test advanced metadata extraction capabilities."""

    def test_standard_extraction(self, extractor, complex_code_sample):
        """Test standard metadata extraction level."""
        request = MetadataRequest(
            extraction_level=MetadataExtractionLevel.STANDARD,
            include_types=True
        )

        metadata = extractor.extract(complex_code_sample, "python", request)

        assert metadata.success
        assert metadata.types is not None
        assert len(metadata.functions) > 0

    def test_deep_extraction(self, extractor, complex_code_sample):
        """Test deep metadata extraction level."""
        request = MetadataRequest(
            extraction_level=MetadataExtractionLevel.DEEP,
            include_control_flow=True
        )

        metadata = extractor.extract(complex_code_sample, "python", request)

        assert metadata.success
        assert metadata.control_flow is not None

    def test_comprehensive_extraction(self, extractor, complex_code_sample):
        """Test comprehensive metadata extraction level."""
        request = MetadataRequest(
            extraction_level=MetadataExtractionLevel.COMPREHENSIVE,
            include_cross_file_refs=True
        )

        metadata = extractor.extract(complex_code_sample, "python", request)

        assert metadata.success
        assert metadata.cross_file_refs is not None

    def test_custom_dependency_depth(self, extractor, complex_code_sample):
        """Test custom dependency depth configuration."""
        request = MetadataRequest(
            extraction_level=MetadataExtractionLevel.STANDARD,
            include_dependencies=True,
            max_dependency_depth=2
        )

        metadata = extractor.extract(complex_code_sample, "python", request)

        assert metadata.success
        assert metadata.dependency_depth <= 2

    def test_type_exclusion(self, extractor, complex_code_sample):
        """Test excluding specific types."""
        request = MetadataRequest(
            extraction_level=MetadataExtractionLevel.STANDARD,
            include_types=True,
            exclude_types=["Any"]
        )

        metadata = extractor.extract(complex_code_sample, "python", request)

        assert metadata.success
