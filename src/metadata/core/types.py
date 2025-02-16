"""
Type definitions for metadata extraction.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from dataclasses import dataclass, field


class MetadataExtractionLevel(Enum):
    """Levels of metadata extraction depth."""
    
    MINIMAL = "minimal"  # Basic imports and signatures only
    STANDARD = "standard"  # + types and direct dependencies
    DEEP = "deep"  # + control flow and data flow
    COMPREHENSIVE = "comprehensive"  # + cross-file analysis


class MetadataRequest(BaseModel):
    """Configuration for metadata extraction."""
    
    model_config = ConfigDict(frozen=True)
    
    extraction_level: MetadataExtractionLevel = MetadataExtractionLevel.STANDARD
    include_types: bool = True
    include_dependencies: bool = True
    max_dependency_depth: Optional[int] = None
    include_docstrings: bool = True
    include_comments: bool = False


@dataclass
class CodeMetadata:
    """Metadata extracted from code."""
    imports: List[str] = field(default_factory=list)
    functions: List[Dict[str, Any]] = field(default_factory=list)
    classes: List[Dict[str, Any]] = field(default_factory=list)
    types: Optional[Dict[str, str]] = None
    dependencies: Optional[Dict[str, List[str]]] = None
    dependency_depth: Optional[int] = None
    docstrings: Optional[Dict[str, str]] = None
    comments: Optional[List[str]] = None
    control_flow: Optional[Dict[str, List[str]]] = None
    data_flow: Optional[Dict[str, List[str]]] = None
    cross_file_refs: Optional[Dict[str, List[str]]] = None
    success: bool = True
    error: Optional[str] = None


class CodeChunk(BaseModel):
    """A chunk of code with its metadata."""
    
    model_config = ConfigDict(frozen=True)
    
    code: str
    language: str
    file_path: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    metadata: Optional[CodeMetadata] = None
