"""
Type definitions for the retrieval system.

This module defines the core data structures used in the retrieval process,
ensuring type safety and clear interfaces.
"""

from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict

class QueryType(str, Enum):
    """Types of retrieval queries."""
    CODE_SEARCH = "code_search"
    SEMANTIC_SEARCH = "semantic_search"
    DEPENDENCY_SEARCH = "dependency_search"
    CONTEXT_SEARCH = "context_search"

class RetrievalFilter(BaseModel):
    """Filter criteria for retrieval queries."""
    languages: Optional[List[str]] = None
    chunk_types: Optional[List[str]] = None
    min_similarity: float = Field(default=0.7, ge=0.0, le=1.0)
    max_results: int = Field(default=10, gt=0)
    date_range: Optional[tuple[datetime, datetime]] = None
    file_patterns: Optional[List[str]] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "json_encoders": {datetime: lambda v: v.isoformat()}
        }
    )

    @field_validator("date_range")
    @classmethod
    def validate_date_range(cls, v: Optional[tuple[datetime, datetime]]) -> Optional[tuple[datetime, datetime]]:
        """Validate that start date is before end date."""
        if v is not None:
            start, end = v
            if start >= end:
                raise ValueError("Start date must be before end date")
        return v

class CodeContext(BaseModel):
    """Context information for code."""
    code_snippet: str
    file_path: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    language: str = "python"
    imports: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    callers: List[str] = Field(default_factory=list)
    related_files: List[str] = Field(default_factory=list)
    documentation: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        json_schema_extra={
            "json_encoders": {datetime: lambda v: v.isoformat()}
        }
    )

    @property
    def code(self) -> str:
        """Alias for code_snippet for backward compatibility."""
        return self.code_snippet

class RetrievalQuery(BaseModel):
    """A query for code retrieval."""
    query: str
    query_type: QueryType = Field(default=QueryType.CODE_SEARCH)
    filters: Optional[RetrievalFilter] = Field(default_factory=lambda: RetrievalFilter())
    context: Optional[CodeContext] = None
    max_results: int = Field(default=10, gt=0)
    min_similarity: float = Field(default=0.7, ge=0.0, le=1.0)
    include_context: bool = Field(default=True)

    model_config = ConfigDict(
        json_schema_extra={
            "json_encoders": {datetime: lambda v: v.isoformat()}
        }
    )

class GeminiConfig(BaseModel):
    """Configuration for Gemini retriever."""
    
    api_key: str
    model: str = Field(default="gemini-1.5-pro", description="Gemini model to use, defaults to Gemini 1.5 Pro")
    max_tokens: int = Field(default=2000000, description="Maximum tokens to use for context window, defaults to 2M for Gemini 1.5 Pro")

class RetrievalResult(BaseModel):
    """Result of a code retrieval operation."""
    query: RetrievalQuery
    chunks: List[Dict[str, Any]]
    similarity_scores: List[float]
    execution_time: float
    total_chunks_searched: int
    context: Optional[CodeContext] = None

    model_config = ConfigDict(
        json_schema_extra={
            "json_encoders": {datetime: lambda v: v.isoformat()}
        }
    )

    @field_validator("chunks")
    @classmethod
    def validate_chunks(cls, v: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate chunk structure."""
        # Allow empty chunks for edge cases
        if not v:
            return v
            
        # Validate each chunk
        for chunk in v:
            if not chunk.get("content"):
                raise ValueError("Empty content in chunk")
        return v

    @field_validator("similarity_scores")
    @classmethod
    def validate_scores(cls, v: List[float]) -> List[float]:
        """Validate that similarity scores are between 0 and 1."""
        if not all(0 <= score <= 1 for score in v):
            raise ValueError("Similarity scores must be between 0 and 1")
        return v
