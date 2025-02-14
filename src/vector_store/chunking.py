"""
Code chunking and metadata extraction module.

This module handles the splitting of code into logical chunks and extraction
of rich metadata for each chunk.
"""

import ast
from typing import List, Dict, Any, Generator, Optional
from pathlib import Path
from .schema import CodeChunkPayload, CodeChunkMetadata, CodeChunkType, Language

class ChunkingConfig:
    """Configuration for code chunking."""
    # Maximum size for a code chunk (in characters)
    MAX_CHUNK_SIZE = 2000
    
    # Minimum size for a code chunk (in characters)
    MIN_CHUNK_SIZE = 50
    
    # Overlap between chunks (in characters)
    CHUNK_OVERLAP = 100

def detect_language(file_path: str) -> Language:
    """
    Detect the programming language of a file based on its extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Language: Detected programming language
        
    Metadata:
        - Dependencies: Language enum
        - Error Handling: Unknown extensions
    """
    ext = Path(file_path).suffix.lower()
    return {
        '.py': Language.PYTHON,
        '.rs': Language.RUST,
        '.ts': Language.TYPESCRIPT
    }.get(ext, Language.UNKNOWN)

def extract_python_metadata(node: ast.AST) -> Dict[str, Any]:
    """
    Extract metadata from a Python AST node.
    
    Args:
        node: AST node to analyze
        
    Returns:
        Dict[str, Any]: Extracted metadata
        
    Metadata:
        - Dependencies: ast module
        - AST Analysis: Function/class details
    """
    metadata = {
        'type': type(node).__name__,
        'lineno': getattr(node, 'lineno', None),
        'end_lineno': getattr(node, 'end_lineno', None),
    }
    
    if isinstance(node, ast.FunctionDef):
        metadata.update({
            'name': node.name,
            'args': [arg.arg for arg in node.args.args],
            'returns': getattr(node.returns, 'id', None) if node.returns else None,
            'decorators': [ast.unparse(d) for d in node.decorator_list],
            'docstring': ast.get_docstring(node)
        })
    elif isinstance(node, ast.ClassDef):
        metadata.update({
            'name': node.name,
            'bases': [ast.unparse(base) for base in node.bases],
            'decorators': [ast.unparse(d) for d in node.decorator_list],
            'docstring': ast.get_docstring(node)
        })
    
    return metadata

def extract_imports(code: str, language: Language) -> List[str]:
    """
    Extract import statements from code.
    
    Args:
        code: Source code to analyze
        language: Programming language of the code
        
    Returns:
        List[str]: List of imported modules/packages
        
    Metadata:
        - Dependencies: ast module for Python
        - Language Support: Python (others TODO)
    """
    imports = []
    if language == Language.PYTHON:
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(name.name for name in node.names)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    imports.extend(f"{module}.{name.name}" for name in node.names)
        except SyntaxError:
            pass  # Handle partial code chunks that might not parse
    return imports

def create_chunk(
    content: str,
    file_path: str,
    start_line: int,
    end_line: int,
    chunk_type: CodeChunkType,
    language: Language,
    ast_data: Optional[Dict[str, Any]] = None
) -> CodeChunkPayload:
    """
    Create a code chunk with metadata.
    
    Args:
        content: Code content
        file_path: Path to source file
        start_line: Starting line number
        end_line: Ending line number
        chunk_type: Type of code chunk
        language: Programming language
        ast_data: Optional AST metadata
        
    Returns:
        CodeChunkPayload: Created chunk with metadata
        
    Metadata:
        - Dependencies: CodeChunkPayload, CodeChunkMetadata
        - Rich Context: Combines code and metadata
    """
    imports = extract_imports(content, language)
    
    metadata = CodeChunkMetadata(
        chunk_type=chunk_type,
        language=language,
        file_path=file_path,
        start_line=start_line,
        end_line=end_line,
        imports=imports,
        ast_data=ast_data or {}
    )
    
    return CodeChunkPayload(
        content=content,
        metadata=metadata
    )

def chunk_python_file(file_path: str) -> Generator[CodeChunkPayload, None, None]:
    """
    Split a Python file into logical chunks with metadata.
    
    Args:
        file_path: Path to Python file
        
    Yields:
        CodeChunkPayload: Code chunks with metadata
        
    Metadata:
        - Dependencies: ast module
        - Chunking Strategy: Function/class based
        - Rich Context: AST metadata
    """
    with open(file_path, 'r') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
        
        # Process classes and functions as main chunks
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                chunk_content = ast.get_source_segment(content, node)
                if chunk_content:
                    chunk_type = (CodeChunkType.FUNCTION 
                                if isinstance(node, ast.FunctionDef)
                                else CodeChunkType.CLASS)
                    
                    yield create_chunk(
                        content=chunk_content,
                        file_path=file_path,
                        start_line=node.lineno,
                        end_line=node.end_lineno or node.lineno,
                        chunk_type=chunk_type,
                        language=Language.PYTHON,
                        ast_data=extract_python_metadata(node)
                    )
        
        # Handle remaining code as statement chunks
        # TODO: Implement smarter chunking for statements
        
    except SyntaxError:
        # If parsing fails, fall back to simple line-based chunking
        lines = content.splitlines()
        current_chunk = []
        current_size = 0
        start_line = 1
        
        for i, line in enumerate(lines, 1):
            line_size = len(line)
            if current_size + line_size > ChunkingConfig.MAX_CHUNK_SIZE and current_chunk:
                chunk_content = '\n'.join(current_chunk)
                yield create_chunk(
                    content=chunk_content,
                    file_path=file_path,
                    start_line=start_line,
                    end_line=i - 1,
                    chunk_type=CodeChunkType.BLOCK,
                    language=Language.PYTHON
                )
                current_chunk = []
                current_size = 0
                start_line = i
            
            current_chunk.append(line)
            current_size += line_size
        
        # Handle the last chunk
        if current_chunk:
            chunk_content = '\n'.join(current_chunk)
            yield create_chunk(
                content=chunk_content,
                file_path=file_path,
                start_line=start_line,
                end_line=len(lines),
                chunk_type=CodeChunkType.BLOCK,
                language=Language.PYTHON
            )
