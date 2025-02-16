"""
Parser implementations for different programming languages.
"""
from textwrap import dedent

from lark import Lark

from ..core.metadata import CodeMetadata
from .grammars.python import PYTHON_GRAMMAR, CustomPythonIndenter, PythonTransformer

def get_parser(language: str) -> 'LarkParser':
    """Get a parser for the specified language."""
    if language.lower() == 'python':
        return LarkParser()
    raise ValueError(f"Unsupported language: {language}")

class LarkParser:
    """Parse Python code using Lark."""

    def __init__(self):
        """Initialize the parser."""
        self.parser = Lark(
            PYTHON_GRAMMAR,
            parser='lalr',
            postlex=CustomPythonIndenter(),
            maybe_placeholders=False,
            propagate_positions=True,
            debug=True
        )
        self.transformer = PythonTransformer()

    def parse_code(self, code: str) -> CodeMetadata:
        """Parse code and return metadata.
        
        Args:
            code: The code to parse.
            
        Returns:
            CodeMetadata containing the extracted metadata.
            If parsing fails, returns CodeMetadata with success=False and error message.
        """
        try:
            # Ensure consistent line endings and dedent
            code = dedent(code.replace('\r\n', '\n'))
            print(f"Parsing code:\n{code}")  # Debug output
            tree = self.parser.parse(code)
            print(f"Parse tree:\n{tree.pretty()}")  # Debug output
            result = self.transformer.transform(tree)
            return CodeMetadata(
                imports=result['imports'],
                functions=result['functions'],
                classes=result['classes'],
                docstrings=result['docstrings'],
                success=True
            )
        except Exception as e:
            print(f"Parse error: {str(e)}")  # Debug output
            return CodeMetadata(
                imports=[],
                functions=[],
                classes=[],
                error=str(e),
                success=False
            )