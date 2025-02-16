"""
Code chunking with minimal structural parsing.

This module handles basic code splitting, leaving deep analysis to LLM.
"""

import ast
from typing import Generator, Optional
from datetime import datetime
from pathlib import Path
from .schema import CodeChunkPayload, CodeChunkMetadata, Language

def detect_language(file_path: str) -> Language:
    """Detect the programming language of a file based on its extension."""
    ext = Path(file_path).suffix.lower()
    return {
        '.py': Language.PYTHON,
        '.rs': Language.RUST,
        '.ts': Language.TYPESCRIPT
    }.get(ext, Language.UNKNOWN)

def chunk_python_file(file_path: str) -> Generator[CodeChunkPayload, None, None]:
    """
    Split a Python file into basic structural chunks.
    Minimal parsing, letting LLM handle deep analysis.
    """
    with open(file_path, 'r') as f:
        content = f.read()
    
    try:
        # Basic structural validation only
        ast.parse(content)  # Validate syntax
        
        # Simple splitting on common structural markers
        chunks = []
        current_chunk = []
        current_start = 1
        
        for i, line in enumerate(content.split('\n'), 1):
            line = line.strip()
            if line.startswith(('class ', 'def ', 'async def ')):
                if current_chunk:
                    chunk_content = '\n'.join(current_chunk)
                    yield create_chunk(
                        content=chunk_content,
                        file_path=file_path,
                        start_line=current_start,
                        end_line=i-1,
                        chunk_type='code_block',
                        language=Language.PYTHON
                    )
                current_chunk = [line]
                current_start = i
            else:
                current_chunk.append(line)
        
        # Last chunk
        if current_chunk:
            chunk_content = '\n'.join(current_chunk)
            yield create_chunk(
                content=chunk_content,
                file_path=file_path,
                start_line=current_start,
                end_line=len(content.split('\n')),
                chunk_type='code_block',
                language=Language.PYTHON
            )
            
    except SyntaxError as e:
        # Only basic syntax validation
        raise ValueError(f"Invalid Python syntax in {file_path}: {str(e)}")

def create_chunk(
    content: str,
    file_path: str,
    start_line: int,
    end_line: int,
    chunk_type: str,
    language: Language,
) -> CodeChunkPayload:
    """Create a code chunk with basic metadata."""
    metadata = CodeChunkMetadata(
        chunk_type=chunk_type,
        language=language.value,
        file_path=file_path,
        start_line=start_line,
        end_line=end_line,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    return CodeChunkPayload(
        content=content,
        metadata=metadata
    )
