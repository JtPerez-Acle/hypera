"""
Metadata extraction from code.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

from ..core.metadata import CodeMetadata
from ..language.support import get_parser
from .types import MetadataExtractionLevel

@dataclass
class MetadataRequest:
    """Configuration for metadata extraction."""
    extraction_level: MetadataExtractionLevel = MetadataExtractionLevel.MINIMAL
    include_types: bool = False
    exclude_types: List[str] = field(default_factory=list)
    include_dependencies: bool = False
    max_dependency_depth: Optional[int] = None
    include_docstrings: bool = False
    include_control_flow: bool = False
    include_data_flow: bool = False
    include_cross_file_refs: bool = False

@dataclass
class MetadataExtractor:
    """Extract metadata from code."""

    def extract(self, code: str, language: str, request: MetadataRequest) -> CodeMetadata:
        """Extract metadata from code according to request configuration."""
        try:
            # Handle empty code case
            if not code.strip():
                return CodeMetadata(
                    imports=[],
                    functions=[],
                    classes=[],
                    success=True
                )

            parser = get_parser(language)()
            metadata = parser.parse_code(code)

            if not metadata.success:
                return metadata

            # Apply extraction level settings
            if request.extraction_level == MetadataExtractionLevel.STANDARD:
                if request.include_types:
                    metadata.types = []  # List of type annotations
                if request.include_dependencies:
                    metadata.dependencies = []  # List of dependencies
                    metadata.dependency_depth = 0  # Start at depth 0

            elif request.extraction_level == MetadataExtractionLevel.DEEP:
                if request.include_control_flow:
                    metadata.control_flow = []  # List of control flow nodes
                if request.include_data_flow:
                    metadata.data_flow = []  # List of data flow edges

            elif request.extraction_level == MetadataExtractionLevel.COMPREHENSIVE:
                if request.include_cross_file_refs:
                    metadata.cross_file_refs = []  # List of cross-file references

            return metadata
        except Exception as e:
            return CodeMetadata(
                success=False,
                error=f"Error extracting metadata: {str(e)}"
            )
