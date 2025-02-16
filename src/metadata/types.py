"""
Type definitions for LLM-based code analysis.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, Optional, List
from enum import Enum


class MetadataExtractionLevel(str, Enum):
    """Level of detail for metadata extraction."""
    MINIMAL = "minimal"  # Basic code structure (imports, functions, classes)
    STANDARD = "standard"  # + types and direct dependencies
    DEEP = "deep"  # + control flow and data flow
    COMPREHENSIVE = "comprehensive"  # + cross-file analysis


class MetadataRequest(BaseModel):
    """Request for metadata extraction."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "extraction_level": "standard",
                "include_types": True,
                "include_dependencies": True,
                "max_dependency_depth": 2,
                "include_docstrings": True,
                "include_comments": False,
                "code": "def process_data(): pass"
            }
        }
    )

    code: Optional[str] = Field(
        default=None,
        description="Code to extract metadata from"
    )
    extraction_level: MetadataExtractionLevel = Field(
        default=MetadataExtractionLevel.STANDARD,
        description="Level of detail for metadata extraction"
    )
    include_types: bool = Field(
        default=True,
        description="Whether to extract type information"
    )
    include_dependencies: bool = Field(
        default=True,
        description="Whether to extract dependencies"
    )
    max_dependency_depth: int = Field(
        default=2,
        description="Maximum depth for dependency analysis",
        ge=1
    )
    include_docstrings: bool = Field(
        default=True,
        description="Whether to extract docstrings"
    )
    include_comments: bool = Field(
        default=False,
        description="Whether to extract comments"
    )
    context: Optional[Dict[str, Any]] = None


class CodeMetadata(BaseModel):
    """Extracted code metadata."""
    model_config = ConfigDict(
        frozen=False,
        json_schema_extra={
            "example": {
                "imports": ["import os", "from typing import List"],
                "functions": [{"name": "process_data", "params": ["items"]}],
                "classes": [],
                "types": {"items": "List[dict]"},
                "dependencies": {"processor.py": ["database.py"]},
                "dependency_depth": 1,
                "docstrings": {"process_data": "Process a list of items"},
                "comments": ["# This is a comment"],
                "success": True,
                "error": None
            }
        }
    )

    imports: List[str] = Field(
        default_factory=list,
        description="Import statements"
    )
    functions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Function definitions"
    )
    classes: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Class definitions"
    )
    types: Optional[Dict[str, str]] = Field(
        None,
        description="Type annotations"
    )
    dependencies: Optional[Dict[str, Any]] = Field(
        None,
        description="Dependencies"
    )
    dependency_depth: Optional[int] = Field(
        None,
        description="Depth of dependency analysis"
    )
    docstrings: Optional[Dict[str, str]] = Field(
        None,
        description="Docstrings"
    )
    comments: Optional[List[str]] = Field(
        None,
        description="Comments"
    )
    control_flow: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Control flow analysis"
    )
    data_flow: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Data flow analysis"
    )
    cross_file_refs: Optional[Dict[str, List[str]]] = Field(
        None,
        description="Cross-file references"
    )
    patterns: Optional[List[str]] = Field(
        None,
        description="Identified patterns"
    )
    security_issues: Optional[List[Dict[str, str]]] = Field(
        None,
        description="Security issues"
    )
    performance_notes: Optional[List[str]] = Field(
        None,
        description="Performance notes"
    )
    token_usage: Optional[Dict[str, int]] = Field(
        None,
        description="Token usage statistics"
    )
    success: bool = Field(
        default=True,
        description="Whether metadata extraction succeeded"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if extraction failed"
    )


class CodeContext(BaseModel):
    """Context information for code analysis."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_path": "src/processor.py",
                "language": "python",
                "chunk_type": "function",
                "start_line": 10,
                "end_line": 20,
                "repository_root": "/path/to/repo",
                "branch": "main"
            }
        }
    )

    file_path: str = Field(description="Path to the file")
    language: str = Field(description="Programming language")
    chunk_type: str = Field(description="Type of code chunk (function, class, etc.)")
    start_line: int = Field(description="Starting line number")
    end_line: int = Field(description="Ending line number")
    repository_root: Optional[str] = Field(None, description="Root of the repository")
    branch: Optional[str] = Field(None, description="Current branch")


class AnalysisResult(BaseModel):
    """Result of LLM-based code analysis."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "metadata": {
                    "imports": ["import os"],
                    "functions": ["process"],
                    "classes": [],
                    "success": True
                },
                "confidence_score": 0.95
            }
        }
    )

    metadata: CodeMetadata = Field(description="Extracted metadata")
    confidence_score: float = Field(
        default=1.0,
        description="Confidence score for the analysis",
        ge=0.0,
        le=1.0
    )
