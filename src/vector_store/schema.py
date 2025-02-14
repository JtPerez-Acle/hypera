"""
Schema definitions for vector store data structures.

This module defines the data structures for storing code chunks and their metadata
in the vector database.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict

class CodeChunkMetadata(BaseModel):
    """Metadata for a code chunk."""
    chunk_type: str = Field(..., description="Type of code chunk (function, class, etc.)")
    language: str = Field(..., description="Programming language")
    file_path: str = Field(..., description="Path to source file")
    start_line: int = Field(..., description="Starting line number")
    end_line: int = Field(..., description="Ending line number")
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    dependencies: Optional[List[str]] = None
    docstring: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(
        json_schema_extra={
            "json_encoders": {datetime: lambda v: v.isoformat()}
        }
    )

class CodeChunkPayload(BaseModel):
    """A code chunk with its metadata."""
    content: str = Field(..., description="Code content")
    metadata: CodeChunkMetadata = Field(..., description="Associated metadata")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding if generated")

    model_config = ConfigDict(
        json_schema_extra={
            "json_encoders": {datetime: lambda v: v.isoformat()}
        }
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate that content is not empty."""
        if not v or not v.strip():
            raise ValueError("Empty or whitespace-only content in chunk")
        return v

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, v: CodeChunkMetadata) -> CodeChunkMetadata:
        """Validate metadata fields."""
        # Check for valid line numbers
        if v.start_line < 0 or v.end_line < v.start_line:
            raise ValueError("Invalid line number range")
        return v
