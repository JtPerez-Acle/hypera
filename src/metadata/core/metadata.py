"""
Metadata types and utilities for code analysis.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class CodeMetadata:
    """Metadata about a code snippet."""
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
