"""
Tests for Python-specific parsing functionality.
"""
from textwrap import dedent
import pytest

from src.metadata.parsing.parsers import LarkParser

@pytest.fixture
def python_parser():
    """Create a Python parser instance."""
    return LarkParser()

@pytest.fixture
def simple_function():
    """Sample function with type hints."""
    return dedent("""
    def greet(name: str) -> str:
        return f"Hello, {name}!"
    """)

@pytest.fixture
def complex_class():
    """Sample class with decorators and async methods."""
    return dedent("""
    @dataclass
    class DataProcessor(BaseProcessor):
        name: str
        config: Dict[str, Any]
        
        @retry(max_attempts=3)
        async def process(self, data: List[dict]) -> Optional[Result]:
            return await self._process_internal(data)
    """)

class TestPythonParsing:
    """Test Python-specific parsing functionality."""
    
    def test_simple_function_parsing(self, python_parser, simple_function):
        """Test parsing of a simple function with type hints."""
        result = python_parser.parse_code(simple_function)
        
        assert result.success
        assert len(result.functions) == 1
        assert result.functions[0]["name"] == "greet"
        assert result.functions[0]["parameters"][0]["name"] == "name"
        assert result.functions[0]["parameters"][0]["type"] == "str"
        assert result.functions[0]["return_type"] == "str"
        
    def test_complex_class_parsing(self, python_parser, complex_class):
        """Test parsing of a complex class with decorators and async methods."""
        result = python_parser.parse_code(complex_class)
        
        assert result.success
        assert len(result.classes) == 1
        assert result.classes[0]["name"] == "DataProcessor"
        assert "dataclass" in result.classes[0]["decorators"]
        assert "BaseProcessor" in result.classes[0]["bases"]
        
    def test_class_hierarchy(self, python_parser):
        """Test extraction of class hierarchy information."""
        code = dedent("""
        class BaseProcessor:
            pass
        
        class SpecialProcessor(BaseProcessor):
            pass
        
        class VerySpecialProcessor(SpecialProcessor):
            pass
        """)
        
        result = python_parser.parse_code(code)
        
        assert result.success
        assert len(result.classes) == 3
        assert result.classes[0]["name"] == "BaseProcessor"
        assert result.classes[1]["name"] == "SpecialProcessor"
        assert "BaseProcessor" in result.classes[1]["bases"]
        assert result.classes[2]["name"] == "VerySpecialProcessor"
        assert "SpecialProcessor" in result.classes[2]["bases"]
