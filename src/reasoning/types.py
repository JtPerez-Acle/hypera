"""
Type definitions for the reasoning module's multi-agent system.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict


class CodeUnderstandingLevel(Enum):
    """Levels of code understanding depth."""
    SURFACE = "surface"  # Basic syntax and structure
    SEMANTIC = "semantic"  # Meaning and purpose
    CONTEXTUAL = "contextual"  # Relationship with other code
    ARCHITECTURAL = "architectural"  # System-level implications
    BEHAVIORAL = "behavioral"  # Runtime behavior and side effects


class MetadataExtractionLevel(Enum):
    """Levels of metadata extraction depth."""
    MINIMAL = "minimal"  # Basic imports and signatures only
    STANDARD = "standard"  # + types and direct dependencies
    DEEP = "deep"  # + control flow and data flow
    COMPREHENSIVE = "comprehensive"  # + cross-file analysis


class MetadataRequest(BaseModel):
    """Configuration for metadata extraction requests."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "extraction_level": "standard",
                "include_types": True,
                "include_dependencies": True,
                "max_dependency_depth": 2,
                "include_docstrings": True,
                "include_comments": False
            }
        }
    )

    extraction_level: MetadataExtractionLevel = Field(
        default=MetadataExtractionLevel.STANDARD,
        description="Desired depth of metadata extraction"
    )
    include_types: bool = Field(
        default=True,
        description="Whether to include type information"
    )
    include_dependencies: bool = Field(
        default=True,
        description="Whether to include dependency information"
    )
    max_dependency_depth: Optional[int] = Field(
        default=None,
        description="Maximum depth for dependency analysis"
    )
    include_docstrings: bool = Field(
        default=True,
        description="Whether to include docstrings"
    )
    include_comments: bool = Field(
        default=False,
        description="Whether to include comments"
    )


class CodeMetadata(BaseModel):
    """Structured metadata about a code chunk."""
    model_config = ConfigDict(frozen=True)

    # Basic information
    imports: List[str] = Field(default_factory=list, description="Import statements")
    functions: List[Dict[str, Any]] = Field(default_factory=list, description="Functions")
    classes: List[Dict[str, Any]] = Field(default_factory=list, description="Classes")

    # Type information
    types: Optional[Dict[str, str]] = Field(None, description="Type information")

    # Dependency information
    dependencies: Optional[Dict[str, List[str]]] = Field(None, description="Dependencies")
    dependency_depth: Optional[int] = Field(None, description="Dependency depth")

    # Documentation
    docstrings: Optional[Dict[str, str]] = Field(None, description="Docstrings")
    comments: Optional[List[str]] = Field(None, description="Comments")

    # Analysis results
    control_flow: Optional[List[Dict[str, Any]]] = Field(None, description="Control flow")
    data_flow: Optional[List[Dict[str, Any]]] = Field(None, description="Data flow")
    cross_file_refs: Optional[Dict[str, List[str]]] = Field(None, description="Cross-file references")

    # Status
    success: bool = Field(True, description="Success status")
    error: Optional[str] = Field(None, description="Error message")


class CodeContext(BaseModel):
    """Rich context about the code being analyzed."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code_snippet": "def process_data(items: List[dict]) -> None:\n    for item in items:\n        item['processed'] = True",
                "file_path": "processor.py",
                "start_line": 10,
                "end_line": 13,
                "language": "python",
                "imports": ["from typing import List"],
                "dependencies": ["database.py", "config.py"],
                "metadata": {
                    "imports": ["import os"],
                    "functions": [{"name": "process_data", "params": ["items"]}],
                    "classes": [],
                    "types": {"items": "List[dict]"},
                    "dependencies": {"processor.py": ["database.py"]},
                    "dependency_depth": 1,
                    "docstrings": {"process_data": "Process a list of items"},
                    "comments": ["# This is a comment"]
                }
            }
        }
    )

    code_snippet: str = Field(description="The code being analyzed")
    file_path: str = Field(description="Path to the file containing the code")
    start_line: int = Field(description="Starting line number in the file")
    end_line: int = Field(description="Ending line number in the file")
    language: str = Field(description="Programming language of the code")
    imports: List[str] = Field(default_factory=list, description="Import statements")
    dependencies: List[str] = Field(default_factory=list, description="Related files")
    metadata: Optional[CodeMetadata] = Field(None, description="Metadata about the code")


class SecurityIssue(BaseModel):
    """Security-related findings in the code."""
    severity: str = Field(description="Severity level (low/medium/high/critical)")
    type: str = Field(description="Type of security issue")
    description: str = Field(description="Detailed description of the issue")
    line_number: Optional[int] = Field(None, description="Line where issue was found")
    recommendation: str = Field(description="How to fix the issue")


class DesignPattern(BaseModel):
    """Identified design pattern in the code."""
    name: str = Field(description="Name of the design pattern")
    confidence: float = Field(description="Confidence in pattern detection", ge=0.0, le=1.0)
    matches: List[str] = Field(description="Code elements matching the pattern")
    explanation: str = Field(description="Why this pattern was detected")


class CodeMetrics(BaseModel):
    """Code quality and complexity metrics."""
    complexity: int = Field(description="Cyclomatic complexity")
    maintainability: float = Field(description="Maintainability index", ge=0.0, le=100.0)
    cognitive_complexity: int = Field(description="Cognitive complexity score")
    lines_of_code: int = Field(description="Number of lines of code")
    comment_ratio: float = Field(description="Ratio of comments to code", ge=0.0, le=1.0)


class DependencyInfo(BaseModel):
    """Information about code dependencies."""
    direct_deps: List[str] = Field(description="Direct dependencies")
    indirect_deps: List[str] = Field(description="Indirect dependencies")
    circular_deps: List[List[str]] = Field(description="Circular dependency chains")
    external_deps: Dict[str, str] = Field(description="External package dependencies")


class AgentDependencies(BaseModel):
    """Dependencies required by the reasoning agents."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "deepseek_api_key": "sk-...",
                "code_context": {"code_snippet": "...", "file_path": "..."},
                "retrieval_results": [{"content": "...", "score": 0.95}]
            }
        }
    )

    deepseek_api_key: str = Field(description="DeepSeek API key for the R1 model")
    code_context: CodeContext = Field(description="Context about the code being analyzed")
    retrieval_results: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Results from the Gemini retrieval system"
    )


class AgentAnalysis(BaseModel):
    """Analysis results from a single agent."""
    agent_name: str = Field(description="Name of the agent that produced this analysis")
    understanding_level: CodeUnderstandingLevel = Field(
        description="Depth of understanding achieved"
    )
    findings: Dict[str, Any] = Field(description="Agent-specific analysis findings")
    confidence: float = Field(description="Confidence in the analysis", ge=0.0, le=1.0)
    supporting_evidence: List[str] = Field(description="Evidence supporting the findings")
    warnings: Optional[List[str]] = Field(None, description="Potential issues identified")


class ComprehensiveAnalysis(BaseModel):
    """Complete analysis from all agents combined."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "What are the side effects of this function?",
                "agent_analyses": [
                    {
                        "agent_name": "behavioral_analyzer",
                        "understanding_level": "behavioral",
                        "findings": {"side_effects": ["Modifies input list", "Writes to database"]},
                        "confidence": 0.95
                    }
                ],
                "security_issues": [{"severity": "medium", "type": "Input validation"}],
                "design_patterns": [{"name": "Observer", "confidence": 0.8}],
                "metrics": {"complexity": 5, "maintainability": 85.0},
                "dependencies": {"direct_deps": ["database.py"]},
                "summary": "The function has side effects...",
                "recommendations": ["Add input validation", "Document side effects"]
            }
        }
    )

    query: str = Field(description="The original analysis query")
    agent_analyses: List[AgentAnalysis] = Field(
        description="Individual analyses from each agent"
    )
    security_issues: Optional[List[SecurityIssue]] = Field(
        None, description="Security-related findings"
    )
    design_patterns: Optional[List[DesignPattern]] = Field(
        None, description="Identified design patterns"
    )
    metrics: Optional[CodeMetrics] = Field(
        None, description="Code quality metrics"
    )
    dependencies: Optional[DependencyInfo] = Field(
        None, description="Dependency analysis"
    )
    summary: str = Field(description="Overall analysis summary")
    recommendations: List[str] = Field(
        description="Recommended improvements"
    )
