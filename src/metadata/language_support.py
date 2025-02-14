"""
Language Support Module for Code Analysis

This module provides language-specific parsing and analysis capabilities,
with a focus on extensibility for multi-language support.
"""

import ast
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

@dataclass
class LanguageFeatures:
    """Features and capabilities of a supported programming language"""
    name: str
    file_extensions: List[str]
    supports_ast: bool = True
    supports_type_hints: bool = True

class LanguageParser(ABC):
    """Abstract base class for language-specific parsing"""
    
    @abstractmethod
    def parse_dependencies(self, content: str) -> List[str]:
        """Extract dependencies from code content"""
        pass
    
    @abstractmethod
    def parse_functions(self, content: str) -> List[Dict[str, Any]]:
        """Extract function definitions and signatures"""
        pass
    
    @abstractmethod
    def parse_classes(self, content: str) -> Dict[str, List[str]]:
        """Extract class definitions and inheritance"""
        pass

class PythonParser(LanguageParser):
    """Python-specific implementation of language parsing"""
    
    def parse_dependencies(self, content: str) -> List[str]:
        try:
            tree = ast.parse(content)
            deps = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    deps.extend(name.name for name in node.names)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        deps.append(node.module)
            return deps
        except SyntaxError:
            return []
    
    def parse_functions(self, content: str) -> List[Dict[str, Any]]:
        try:
            tree = ast.parse(content)
            funcs = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func = {
                        'name': node.name,
                        'args': [arg.arg for arg in node.args.args],
                        'returns': getattr(node.returns, 'id', None),
                        'decorators': [ast.unparse(d) for d in node.decorator_list],
                        'async': isinstance(node, ast.AsyncFunctionDef)
                    }
                    funcs.append(func)
            return funcs
        except SyntaxError:
            return []
    
    def parse_classes(self, content: str) -> Dict[str, List[str]]:
        try:
            tree = ast.parse(content)
            classes = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    bases = [
                        base.id if isinstance(base, ast.Name)
                        else ast.unparse(base)
                        for base in node.bases
                    ]
                    classes[node.name] = bases
            return classes
        except SyntaxError:
            return {}

# Language registry
SUPPORTED_LANGUAGES = {
    'python': LanguageFeatures(
        name='Python',
        file_extensions=['.py', '.pyi', '.pyx'],
    ),
    # Add more languages as needed
}

def get_parser(language: str) -> Optional[LanguageParser]:
    """Factory function to get appropriate parser for a language"""
    if language.lower() == 'python':
        return PythonParser()
    return None
