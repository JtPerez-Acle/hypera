"""
Types and enums for metadata parsing.
"""
from enum import Enum

class MetadataExtractionLevel(Enum):
    """Levels of metadata extraction."""
    MINIMAL = "MINIMAL"
    STANDARD = "STANDARD"
    DEEP = "DEEP"
    COMPREHENSIVE = "COMPREHENSIVE"
