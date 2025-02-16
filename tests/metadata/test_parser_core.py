"""
Tests for core parser functionality.
"""
from textwrap import dedent
import pytest

from src.metadata.parsing.parsers import LarkParser

@pytest.fixture
def python_parser():
    """Create a Python parser instance."""
    return LarkParser()

class TestParserCore:
    """Test core parser functionality."""
    
    def test_parser_initialization(self, python_parser):
        """Test parser initialization."""
        assert python_parser is not None
        
    def test_invalid_code_handling(self, python_parser):
        """Test handling of invalid Python code."""
        result = python_parser.parse_code("def invalid syntax(")
        assert not result.success
        assert result.error is not None
        
    def test_empty_code_handling(self, python_parser):
        """Test handling of empty code."""
        result = python_parser.parse_code("")
        assert result.success
        assert not result.imports
        assert not result.functions
        assert not result.classes
