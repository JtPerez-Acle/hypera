"""
Transformers for converting parse trees into metadata.
"""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from lark import Transformer, Tree, Token


@dataclass
class ImportInfo:
    """Information about an import statement."""
    module: str
    alias: Optional[str] = None
    is_relative: bool = False
    relative_level: int = 0
    imported_names: List[tuple[str, Optional[str]]] = field(default_factory=list)

@dataclass
class FunctionInfo:
    """Information about a function definition."""
    name: str
    decorators: List[Dict[str, Any]] = field(default_factory=list)
    is_async: bool = False
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    return_type: Optional[str] = None
    docstring: Optional[str] = None
    class_name: Optional[str] = None

@dataclass
class ClassInfo:
    """Information about a class definition."""
    name: str
    decorators: List[Dict[str, Any]] = field(default_factory=list)
    bases: List[str] = field(default_factory=list)
    docstring: Optional[str] = None

@dataclass
class PythonMetadataExtractor(Transformer):
    """Extracts metadata from Python parse trees."""
    
    imports: List[str] = field(default_factory=list)
    functions: List[Dict[str, Any]] = field(default_factory=list)
    classes: List[Dict[str, Any]] = field(default_factory=list)
    current_class: Optional[str] = None
    
    def file_input(self, items):
        """Process the entire file."""
        return self
    
    def import_from(self, items):
        """Process 'from x import y' statements."""
        info = ImportInfo(module="")
        
        for item in items:
            if isinstance(item, Tree):
                if item.data == "relative_import":
                    dots = str(item.children[0]).count(".")
                    info.is_relative = True
                    info.relative_level = dots
                    if len(item.children) > 1:
                        info.module = self._join_dotted_name(item.children[1])
                elif item.data == "dotted_name":
                    info.module = self._join_dotted_name(item.children)
                elif item.data == "import_as_names":
                    for name_item in item.children:
                        if isinstance(name_item, Tree):
                            name = str(name_item.children[0])
                            alias = str(name_item.children[2]) if len(name_item.children) > 2 else None
                            info.imported_names.append((name, alias))
                        else:
                            info.imported_names.append((str(name_item), None))
            elif item == "*":
                info.imported_names.append(("*", None))
        
        # Convert ImportInfo to string format
        prefix = "." * info.relative_level
        if info.imported_names:
            for name, alias in info.imported_names:
                if name == "*":
                    self.imports.append(f"from {prefix}{info.module} import *")
                else:
                    import_str = f"from {prefix}{info.module} import {name}"
                    if alias:
                        import_str += f" as {alias}"
                    self.imports.append(import_str)
                
        return items
    
    def import_name(self, items):
        """Process 'import x' statements."""
        if len(items) < 2:
            return items
            
        for item in items[1:]:
            if isinstance(item, Tree):
                if item.data == "dotted_as_name":
                    module = self._join_dotted_name(item.children[0])
                    if len(item.children) > 1:
                        alias = str(item.children[2])
                        self.imports.append(f"import {module} as {alias}")
                    else:
                        self.imports.append(f"import {module}")
                elif item.data == "dotted_as_names":
                    for name in item.children:
                        if isinstance(name, Tree) and name.data == "dotted_as_name":
                            module = self._join_dotted_name(name.children[0])
                            if len(name.children) > 1:
                                alias = str(name.children[2])
                                self.imports.append(f"import {module} as {alias}")
                            else:
                                self.imports.append(f"import {module}")
                
        return items
    
    def function_def(self, items):
        """Process function definitions."""
        info = FunctionInfo(name="")
        
        for item in items:
            if isinstance(item, list) and item and isinstance(item[0], dict):
                info.decorators = item
            elif isinstance(item, Token):
                if item.type == "ASYNC":
                    info.is_async = True
                elif item.type == "NAME":
                    info.name = str(item)
            elif isinstance(item, list) and not isinstance(item[0], dict):
                info.parameters = self._process_parameters(item)
            elif isinstance(item, Tree):
                if item.data == "test":
                    info.return_type = self._process_type_annotation(item)
        
        if info.name:
            if self.current_class:
                info.class_name = self.current_class
            
            self.functions.append({
                "name": info.name,
                "decorators": [d["name"] for d in info.decorators],
                "is_async": info.is_async,
                "parameters": info.parameters,
                "return_type": info.return_type,
                "class": info.class_name
            })
            
        return items
    
    def class_def(self, items):
        """Process class definitions."""
        info = ClassInfo(name="")
        
        for item in items:
            if isinstance(item, list) and item and isinstance(item[0], dict):
                info.decorators = item
            elif isinstance(item, Token) and item.type == "NAME":
                if not info.name:
                    info.name = str(item)
                else:
                    info.bases.append(str(item))
            elif isinstance(item, Tree):
                if item.data == "arguments":
                    for arg in item.children:
                        if isinstance(arg, Tree) and arg.data == "argument":
                            base = self._process_argument(arg)
                            if base:
                                info.bases.append(base)
        
        if info.name:
            prev_class = self.current_class
            self.current_class = info.name
            
            self.classes.append({
                "name": info.name,
                "decorators": [d["name"] for d in info.decorators],
                "bases": info.bases,
                "docstring": info.docstring
            })
            
            self.current_class = prev_class
            
        return items
    
    def decorator(self, items):
        """Process decorators."""
        name = self._join_dotted_name(items[0])
        args = []
        if len(items) > 2:
            args = self._process_decorator_arguments(items[2])
        return {"name": name, "arguments": args}
    
    def _process_decorator_arguments(self, args_tree) -> List[Any]:
        """Process decorator arguments."""
        args = []
        if isinstance(args_tree, Tree):
            for arg in args_tree.children:
                if isinstance(arg, Tree):
                    if arg.data == "argument":
                        processed = self._process_argument(arg)
                        if processed:
                            args.append(processed)
        return args
    
    def _process_argument(self, arg_tree) -> Optional[str]:
        """Process a single argument."""
        if isinstance(arg_tree, Tree):
            if len(arg_tree.children) > 0:
                test_tree = arg_tree.children[0]
                if isinstance(test_tree, Tree):
                    return self._process_type_annotation(test_tree)
        return None
    
    def _join_dotted_name(self, items) -> str:
        """Helper to join dotted names."""
        if isinstance(items, list):
            return ".".join(str(i) for i in items)
        elif isinstance(items, Tree) and items.data == "dotted_name":
            return ".".join(str(i) for i in items.children)
        return str(items)
    
    def _process_parameters(self, params) -> List[Dict[str, Any]]:
        """Process function parameters."""
        processed = []
        for param in params:
            if isinstance(param, Tree) and param.data == "param":
                param_info = {"name": str(param.children[0])}
                
                for i, child in enumerate(param.children[1:], 1):
                    if isinstance(child, Tree):
                        if child.data == "test" and i == 1:
                            param_info["type"] = self._process_type_annotation(child)
                        elif child.data == "test" and i == 2:
                            param_info["default"] = self._process_type_annotation(child)
                
                processed.append(param_info)
            else:
                processed.append({"name": str(param)})
        return processed
    
    def _process_type_annotation(self, type_tree) -> Optional[str]:
        """Process type annotations."""
        if isinstance(type_tree, Tree):
            if type_tree.data == "test":
                parts = []
                for child in type_tree.children:
                    if isinstance(child, Token):
                        parts.append(str(child))
                    elif isinstance(child, Tree):
                        if child.data == "power":
                            power_type = self._process_power(child)
                            if power_type:
                                parts.append(power_type)
                        else:
                            child_type = self._process_type_annotation(child)
                            if child_type:
                                parts.append(child_type)
                return "".join(parts)
        return None
    
    def _process_power(self, power_tree) -> Optional[str]:
        """Process power expressions in type annotations."""
        if isinstance(power_tree, Tree):
            parts = []
            for child in power_tree.children:
                if isinstance(child, Tree):
                    if child.data == "atom_expr":
                        atom_type = self._process_atom_expr(child)
                        if atom_type:
                            parts.append(atom_type)
            return "".join(parts)
        return None
    
    def _process_atom_expr(self, atom_expr_tree) -> Optional[str]:
        """Process atom expressions in type annotations."""
        if isinstance(atom_expr_tree, Tree):
            parts = []
            for child in atom_expr_tree.children:
                if isinstance(child, Tree):
                    if child.data == "var":
                        parts.append(str(child.children[0]))
                    elif child.data == "trailer":
                        trailer_type = self._process_trailer(child)
                        if trailer_type:
                            parts.append(trailer_type)
            return "".join(parts)
        return None
    
    def _process_trailer(self, trailer_tree) -> Optional[str]:
        """Process trailers in type annotations."""
        if isinstance(trailer_tree, Tree):
            if len(trailer_tree.children) > 0:
                if isinstance(trailer_tree.children[0], Token):
                    if trailer_tree.children[0].value == ".":
                        return "." + str(trailer_tree.children[1])
                    elif trailer_tree.children[0].value == "[":
                        return "[" + self._process_subscriptlist(trailer_tree.children[1]) + "]"
        return None
    
    def _process_subscriptlist(self, subscript_tree) -> str:
        """Process subscript lists in type annotations."""
        if isinstance(subscript_tree, Tree):
            parts = []
            for child in subscript_tree.children:
                if isinstance(child, Tree):
                    if child.data == "subscript":
                        subscript = self._process_type_annotation(child.children[0])
                        if subscript:
                            parts.append(subscript)
                    else:
                        child_type = self._process_type_annotation(child)
                        if child_type:
                            parts.append(child_type)
            return ", ".join(parts)
        return ""
