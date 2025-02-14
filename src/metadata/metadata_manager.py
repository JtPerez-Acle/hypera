"""
Metadata Manager for Code Analysis

This module provides tools for extracting and managing rich metadata from code chunks,
including AST analysis, dependency tracking, and context linking.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import logging

from .language_support import get_parser, SUPPORTED_LANGUAGES

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CodeChunk:
    """Represents a chunk of code with its metadata"""
    content: str
    file_path: str
    line_range: tuple[int, int]
    language: str = "python"
    ast_snippet: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize language-specific parsing"""
        if self.ast_snippet is None:
            parser = get_parser(self.language)
            if parser:
                try:
                    # We'll store parsing results instead of raw AST
                    self.ast_snippet = {
                        "dependencies": parser.parse_dependencies(self.content),
                        "functions": parser.parse_functions(self.content),
                        "classes": parser.parse_classes(self.content)
                    }
                except Exception as e:
                    logger.error(f"Failed to parse code: {e}")
                    self.ast_snippet = None

@dataclass
class CodeMetadata:
    """Structured metadata for code analysis"""
    dependencies: List[str] = field(default_factory=list)
    function_signatures: List[Dict[str, Any]] = field(default_factory=list)
    class_hierarchy: Dict[str, List[str]] = field(default_factory=dict)
    context_links: Dict[str, str] = field(default_factory=dict)

def generate_context_links(file_path: str) -> Dict[str, str]:
    """Generate repository and documentation links"""
    path = Path(file_path)
    return {
        "file": str(path.absolute()),
        "repo_path": str(path.relative_to(Path.cwd())),
        "doc_link": f"docs/api/{path.stem}.md"
    }

def process_code_chunk(chunk: CodeChunk) -> str:
    """
    Process a code chunk and generate rich metadata
    
    Args:
        chunk: CodeChunk instance containing code and context
        
    Returns:
        Formatted string containing code and metadata
    """
    if not chunk.ast_snippet:
        return f"Error: Unable to process code chunk from {chunk.file_path}"
    
    metadata = CodeMetadata(
        dependencies=chunk.ast_snippet.get("dependencies", []),
        function_signatures=chunk.ast_snippet.get("functions", []),
        class_hierarchy=chunk.ast_snippet.get("classes", {}),
        context_links=generate_context_links(chunk.file_path)
    )
    
    return f"""
    //// CODE ////
    {chunk.content}
    
    //// METADATA ////
    {json.dumps(metadata.__dict__, indent=2)}
    """
