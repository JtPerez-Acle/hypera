"""Unit tests for metadata extraction and processing"""

import pytest
from pathlib import Path
from src.metadata.metadata_manager import CodeChunk, process_code_chunk
from src.metadata.language_support import PythonParser

@pytest.fixture
def sample_code():
    return """
import pandas as pd
from typing import List, Optional

class Parent:
    def method(self) -> None:
        pass

class Child(Parent):
    def __init__(self, value: int):
        self.value = value
    """

def test_code_chunk_initialization():
    """Test CodeChunk initialization and AST parsing"""
    chunk = CodeChunk(
        content="def example() -> None:\n    pass",
        file_path="src/example.py",
        line_range=(1, 2)
    )
    assert chunk.ast_snippet is not None
    assert chunk.language == "python"
    assert "functions" in chunk.ast_snippet

def test_python_parser_dependencies(sample_code):
    """Test dependency extraction from imports"""
    parser = PythonParser()
    deps = parser.parse_dependencies(sample_code)
    assert "pandas" in deps
    assert "typing" in deps

def test_python_parser_functions(sample_code):
    """Test function signature extraction"""
    parser = PythonParser()
    sigs = parser.parse_functions(sample_code)
    assert any(sig["name"] == "method" for sig in sigs)
    assert any(sig["name"] == "__init__" for sig in sigs)

def test_python_parser_classes(sample_code):
    """Test class hierarchy analysis"""
    parser = PythonParser()
    hierarchy = parser.parse_classes(sample_code)
    assert "Child" in hierarchy
    assert "Parent" in hierarchy["Child"]

def test_process_code_chunk():
    """Test full metadata processing pipeline"""
    code = "def test(x: int) -> str:\n    return str(x)"
    test_file = Path.cwd() / "tests" / "test_file.py"
    chunk = CodeChunk(content=code, file_path=str(test_file), line_range=(1, 2))
    result = process_code_chunk(chunk)
    assert "//// CODE ////" in result
    assert "//// METADATA ////" in result
    assert "function_signatures" in result
    assert "test" in result
