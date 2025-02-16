"""
Tests for import statement parsing functionality.
"""
from textwrap import dedent
import pytest

from src.metadata.parsing.parsers import LarkParser

@pytest.fixture
def python_parser():
    """Create a Python parser instance."""
    return LarkParser()

@pytest.fixture
def imports_sample():
    """Sample import statements."""
    return dedent("""
    from typing import List, Dict, Optional
    from pathlib import Path
    import json
    import sys, os
    from .utils import helper
    """)

class TestImportParsing:
    """Test import statement parsing functionality."""
    
    def test_imports_parsing(self, python_parser, imports_sample):
        """Test parsing of various import statements."""
        result = python_parser.parse_code(imports_sample)
        
        assert result.success
        assert "typing.List" in result.imports
        assert "typing.Dict" in result.imports
        assert "typing.Optional" in result.imports
        assert "pathlib.Path" in result.imports
        assert "json" in result.imports
        assert "sys" in result.imports
        assert "os" in result.imports
        assert ".utils.helper" in result.imports
        
    def test_relative_imports(self, python_parser):
        """Test parsing of relative imports."""
        code = dedent("""
        from ..parent import something
        from . import local
        from .sub.module import item
        """)
        
        result = python_parser.parse_code(code)
        
        assert result.success
        assert "..parent.something" in result.imports
        assert ".local" in result.imports
        assert ".sub.module.item" in result.imports
        
    def test_import_as(self, python_parser):
        """Test parsing of import with aliases."""
        code = dedent("""
        import numpy as np
        from pandas import DataFrame as df
        from torch.nn import Module as base
        """)
        
        result = python_parser.parse_code(code)
        
        assert result.success
        assert any(imp["module"] == "numpy" and imp["alias"] == "np" 
                  for imp in result.imports if isinstance(imp, dict))
        assert any(imp["module"] == "pandas" and imp["name"] == "DataFrame" 
                  for imp in result.imports if isinstance(imp, dict))
