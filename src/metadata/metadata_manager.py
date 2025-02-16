"""Metadata management and processing module."""

import ast
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple

from .types import (
    CodeMetadata,
    MetadataRequest,
    MetadataExtractionLevel,
    CodeContext,
    AnalysisResult
)


@dataclass
class CodeChunk:
    """A chunk of code with its metadata."""
    code: str
    language: str = "python"
    metadata: Optional[CodeMetadata] = None
    file_path: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None


async def process_code_chunk(code: str, language: str = "python") -> CodeMetadata:
    """Process a code chunk and extract its metadata.
    
    Args:
        code: The code to process
        language: The programming language of the code
        
    Returns:
        Extracted metadata
    """
    agent = MetadataGenerationAgent()
    request = MetadataRequest(
        code=code,
        extraction_level=MetadataExtractionLevel.STANDARD,
        include_types=True,
        include_dependencies=True,
        max_dependency_depth=1,
        include_docstrings=True,
        include_comments=True
    )
    return await agent.extract_metadata(code, language, request)


class MetadataGenerationAgent:
    """Agent responsible for generating rich metadata from code."""

    def __init__(self):
        """Initialize the metadata generation agent."""
        pass

    async def extract_metadata(
        self,
        code_snippet: str,
        language: str,
        metadata_request: MetadataRequest,
    ) -> CodeMetadata:
        """Extract metadata from code using the configured metadata extraction pipeline.

        Args:
            code_snippet: Code to extract metadata from
            language: Programming language of the code
            metadata_request: Configuration for what metadata to extract

        Returns:
            Extracted metadata information
        """
        try:
            # Initialize with defaults
            metadata = CodeMetadata(
                imports=[],
                functions=[],
                classes=[],
                types={},
                dependencies={},
                docstrings={},
                comments=[],
                success=True,
                error=None
            )
            
            # Parse AST and extract basic information
            tree = ast.parse(code_snippet)
            
            # Extract imports
            metadata.imports = self._extract_imports(tree)
            
            # Extract functions and classes
            functions, classes = self._extract_definitions(tree)
            metadata.functions = functions
            metadata.classes = classes
            
            # Extract requested metadata
            if metadata_request.include_types:
                metadata.types = self._extract_types(tree)
            if metadata_request.include_dependencies:
                metadata.dependencies = self._extract_dependencies(tree)
                metadata.dependency_depth = metadata_request.max_dependency_depth
            if metadata_request.include_docstrings:
                metadata.docstrings = self._extract_docstrings(tree)
            if metadata_request.include_comments:
                metadata.comments = self._extract_comments(tree)
            
            # Add deep analysis for DEEP level
            if metadata_request.extraction_level in (
                MetadataExtractionLevel.DEEP,
                MetadataExtractionLevel.COMPREHENSIVE
            ):
                metadata.control_flow = self._analyze_control_flow(tree)
                metadata.data_flow = self._analyze_data_flow(tree)
            
            # Add cross-file analysis for COMPREHENSIVE level
            if metadata_request.extraction_level == MetadataExtractionLevel.COMPREHENSIVE:
                metadata.cross_file_refs = self._analyze_cross_file_refs(tree)
            
            return metadata
            
        except SyntaxError as e:
            return CodeMetadata(
                imports=[],
                functions=[],
                classes=[],
                success=False,
                error=f"SyntaxError: {str(e)}"
            )
        except Exception as e:
            return CodeMetadata(
                imports=[],
                functions=[],
                classes=[],
                success=False,
                error=f"Error during metadata extraction: {str(e)}"
            )

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements from AST."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.append(f"import {name.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for name in node.names:
                    if name.name == "*":
                        imports.append(f"from {module} import *")
                    else:
                        imports.append(f"from {module} import {name.name}")
        return imports

    def _extract_definitions(
        self,
        tree: ast.AST
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Extract function and class definitions from AST."""
        class DefinitionVisitor(ast.NodeVisitor):
            def __init__(self, agent):
                super().__init__()
                self.agent = agent
                self.functions = []
                self.classes = []
                self.current_class = None
                self.class_methods = {}
            
            def visit_FunctionDef(self, node):
                self._handle_function(node)
            
            def visit_AsyncFunctionDef(self, node):
                self._handle_function(node)
            
            def _handle_function(self, node):
                function_info = {
                    "name": node.name,
                    "params": [arg.arg for arg in node.args.args],
                    "return_type": self.agent._get_return_type(node)
                }
                
                if self.current_class:
                    function_info["name"] = f"{self.current_class.name}.{node.name}"
                    methods = self.class_methods.setdefault(self.current_class.name, [])
                    methods.append(node.name)
                    self.functions.append(function_info)
                else:
                    self.functions.append(function_info)
                self.generic_visit(node)
            
            def visit_ClassDef(self, node):
                prev_class = self.current_class
                self.current_class = node
                self.generic_visit(node)
                self.current_class = prev_class
                
                if not prev_class:  # Only add top-level classes
                    self.classes.append(self.agent._extract_class_info(node))
        
        visitor = DefinitionVisitor(self)
        visitor.visit(tree)
        return visitor.functions, visitor.classes

    def _extract_class_info(self, node: ast.ClassDef) -> Dict[str, Any]:
        """Extract information about a class definition."""
        methods = []
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(child.name)
        
        return {
            "name": node.name,
            "methods": methods,
            "base_classes": [base.id for base in node.bases if isinstance(base, ast.Name)],
            "decorators": [d.id for d in node.decorator_list if isinstance(d, ast.Name)]
        }

    def _get_name(self, node: ast.AST) -> str:
        """Get the name from an AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return ""

    def _get_return_type(self, node: ast.FunctionDef) -> Optional[str]:
        """Get the return type annotation from a function definition."""
        if node.returns:
            return ast.unparse(node.returns)
        return None

    def _extract_types(self, tree: ast.AST) -> Dict[str, str]:
        """Extract type annotations from AST."""
        class TypeVisitor(ast.NodeVisitor):
            def __init__(self):
                self.types = {}
                self.current_class = None
            
            def visit_ClassDef(self, node):
                prev_class = self.current_class
                self.current_class = node
                self.generic_visit(node)
                self.current_class = prev_class
            
            def visit_FunctionDef(self, node):
                if node.returns:
                    name = node.name
                    if self.current_class:
                        name = f"{self.current_class.name}.{node.name}"
                    self.types[name] = ast.unparse(node.returns)
                
                # Process function arguments
                for arg in node.args.args:
                    if arg.annotation:
                        arg_name = arg.arg
                        if self.current_class:
                            arg_name = f"{self.current_class.name}.{node.name}.{arg_name}"
                        self.types[arg_name] = ast.unparse(arg.annotation)
                
                self.generic_visit(node)
            
            def visit_AnnAssign(self, node):
                if isinstance(node.target, ast.Name):
                    name = node.target.id
                    if self.current_class:
                        name = f"{self.current_class.name}.{name}"
                    self.types[name] = ast.unparse(node.annotation)
                elif isinstance(node.target, ast.Attribute):
                    if isinstance(node.target.value, ast.Name):
                        name = f"{node.target.value.id}.{node.target.attr}"
                        self.types[name] = ast.unparse(node.annotation)
            
            def visit_arg(self, node):
                if node.annotation:
                    self.types[node.arg] = ast.unparse(node.annotation)
        
        visitor = TypeVisitor()
        visitor.visit(tree)
        return visitor.types

    def _extract_dependencies(self, tree: ast.AST) -> Dict[str, List[str]]:
        """Extract dependencies from AST."""
        dependencies = {}
        
        class DependencyVisitor(ast.NodeVisitor):
            def __init__(self):
                self.dependencies = {}
                self.current_scope = None
                self.current_class = None
            
            def visit_ClassDef(self, node):
                prev_class = self.current_class
                self.current_class = node
                
                # Get base class dependencies
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        self.add_dependency(node.name, base.id)
                
                self.generic_visit(node)
                self.current_class = prev_class
            
            def visit_FunctionDef(self, node):
                prev_scope = self.current_scope
                scope_name = node.name
                if self.current_class:
                    scope_name = f"{self.current_class.name}.{node.name}"
                self.current_scope = scope_name
                
                self.generic_visit(node)
                self.current_scope = prev_scope
            
            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Load) and self.current_scope:
                    self.add_dependency(self.current_scope, node.id)
            
            def add_dependency(self, scope: str, dependency: str):
                if scope not in self.dependencies:
                    self.dependencies[scope] = []
                if dependency not in self.dependencies[scope]:
                    self.dependencies[scope].append(dependency)
        
        visitor = DependencyVisitor()
        visitor.visit(tree)
        return visitor.dependencies

    def _extract_docstrings(self, tree: ast.AST) -> Dict[str, str]:
        """Extract docstrings from AST."""
        docstrings = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if ast.get_docstring(node):
                    docstrings[node.name] = ast.get_docstring(node)
        return docstrings

    def _extract_comments(self, tree: ast.AST) -> List[str]:
        """Extract comments from AST."""
        # Note: AST doesn't preserve comments, would need to parse source directly
        return []

    def _analyze_control_flow(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Analyze control flow from AST."""
        # Placeholder for control flow analysis
        return []

    def _analyze_data_flow(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Analyze data flow from AST."""
        # Placeholder for data flow analysis
        return []

    def _analyze_cross_file_refs(self, tree: ast.AST) -> Dict[str, List[str]]:
        """Analyze cross-file references from AST."""
        # Placeholder for cross-file reference analysis
        return {}

    def _extract_function_info(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Extract information about a function definition."""
        return {
            "name": node.name,
            "params": [arg.arg for arg in node.args.args],
            "return_type": self._get_return_type(node)
        }
