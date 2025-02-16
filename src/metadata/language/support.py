"""
Language detection and parser selection.
"""
from dataclasses import dataclass
from typing import Dict, Type

from ..parsing.parsers import LarkParser

@dataclass
class LanguageFeatures:
    """Features supported by a language parser."""
    has_types: bool = False
    has_imports: bool = True
    has_classes: bool = True
    has_functions: bool = True
    has_docstrings: bool = True
    has_comments: bool = True

# Language registry
SUPPORTED_LANGUAGES = {
    'python': {
        'parser': LarkParser,
        'features': LanguageFeatures(
            has_types=True,
            has_imports=True,
            has_classes=True,
            has_functions=True,
            has_docstrings=True,
            has_comments=True
        )
    }
}

def get_parser(language: str) -> Type[LarkParser]:
    """Get the appropriate parser for a given language."""
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {language}")
    return SUPPORTED_LANGUAGES[language]['parser']

def get_language_features(language: str) -> LanguageFeatures:
    """Get the features supported by a language."""
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {language}")
    return SUPPORTED_LANGUAGES[language]['features']
