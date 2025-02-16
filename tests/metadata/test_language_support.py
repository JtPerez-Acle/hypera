"""
Tests for language support functionality.
"""
from textwrap import dedent
import pytest

from src.metadata.parsing.parsers import get_parser
from src.metadata.language.support import SUPPORTED_LANGUAGES

@pytest.fixture
def simple_function():
    """Sample function with type hints."""
    return dedent("""
    def greet(name: str) -> str:
        return f"Hello, {name}!"
    """)

class TestLanguageSupport:
    """Test language support functionality."""
    
    def test_python_code_parsing(self, simple_function):
        """Test parsing Python code through language support."""
        parser = get_parser("python")
        result = parser.parse_code(simple_function)
        assert result.success
        
    def test_unsupported_language(self):
        """Test handling of unsupported languages."""
        with pytest.raises(ValueError):
            get_parser("unsupported")
            
    def test_supported_languages_list(self):
        """Test that supported languages are properly defined."""
        assert "python" in SUPPORTED_LANGUAGES
        
    def test_language_case_sensitivity(self, simple_function):
        """Test that language names are case-insensitive."""
        parser = get_parser("Python")  # Capital P
        result = parser.parse_code(simple_function)
        assert result.success
