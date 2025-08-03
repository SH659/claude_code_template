#!/usr/bin/env python3
"""
PURPOSE: Analyze Python project dependencies and generate detailed dependency graph
DESCRIPTION: Uses pyreverse for structural relations and AST for method-level usage analysis
"""

import ast
import csv
import os
import re
import subprocess
import sys
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union


@dataclass
class Edge:
    """
    PURPOSE: Represent a dependency edge in the graph
    """
    source: str
    target: str
    edge_type: str  # inherits, associates, uses, imports
    certainty: str = "high"  # high, low
    is_builtin: bool = False  # True if target is a built-in function
    is_stdlib: bool = False   # True if target is from standard library
    is_self_dep: bool = False # True if dependency is within same module


class SymbolTable:
    """
    PURPOSE: Track symbol definitions and imports across modules
    """
    def __init__(self):
        self.modules: Dict[str, Dict] = {}
        self.imports: Dict[str, Dict[str, str]] = {}  # module -> {alias: full_name}
        self.classes: Dict[str, str] = {}  # class_name -> full_qualified_name
        self.functions: Dict[str, str] = {}  # function_name -> full_qualified_name
        
    def add_module(self, module_name: str):
        if module_name not in self.modules:
            self.modules[module_name] = {
                'classes': {},
                'functions': {},
                'methods': {}
            }
            self.imports[module_name] = {}
    
    def add_import(self, module_name: str, imported_name: str, alias: str = None):
        self.imports[module_name][alias or imported_name] = imported_name
    
    def add_class(self, module_name: str, class_name: str):
        full_name = f"{module_name}.{class_name}"
        self.modules[module_name]['classes'][class_name] = full_name
        self.classes[class_name] = full_name
        return full_name
    
    def add_function(self, module_name: str, function_name: str):
        full_name = f"{module_name}.{function_name}"
        self.modules[module_name]['functions'][function_name] = full_name
        self.functions[function_name] = full_name
        return full_name
    
    def add_method(self, module_name: str, class_name: str, method_name: str):
        full_name = f"{module_name}.{class_name}.{method_name}"
        if class_name not in self.modules[module_name]['methods']:
            self.modules[module_name]['methods'][class_name] = {}
        self.modules[module_name]['methods'][class_name][method_name] = full_name
        return full_name
    
    def resolve_name(self, module_name: str, name: str) -> Optional[str]:
        """Resolve a name to its full qualified name"""
        # Check imports first
        if name in self.imports[module_name]:
            return self.imports[module_name][name]
        
        # Check local classes
        if name in self.modules[module_name]['classes']:
            return self.modules[module_name]['classes'][name]
        
        # Check local functions
        if name in self.modules[module_name]['functions']:
            return self.modules[module_name]['functions'][name]
        
        return None


class TypeInference:
    """
    PURPOSE: Simple type inference for method calls
    """
    def __init__(self, symbol_table: SymbolTable):
        self.symbol_table = symbol_table
        self.local_vars: Dict[str, Dict[str, str]] = {}  # scope -> {var: type}
        self.instance_vars: Dict[str, Dict[str, str]] = {}  # class -> {attr: type}
    
    def enter_scope(self, scope_name: str):
        if scope_name not in self.local_vars:
            self.local_vars[scope_name] = {}
    
    def add_assignment(self, scope: str, var_name: str, value_type: str):
        if scope not in self.local_vars:
            self.local_vars[scope] = {}
        self.local_vars[scope][var_name] = value_type
    
    def add_instance_var(self, class_name: str, attr_name: str, attr_type: str):
        if class_name not in self.instance_vars:
            self.instance_vars[class_name] = {}
        self.instance_vars[class_name][attr_name] = attr_type
    
    def add_constructor_param_type(self, class_name: str, param_name: str, param_type: str):
        """Track constructor parameter types for self.param.method() resolution"""
        if class_name not in self.instance_vars:
            self.instance_vars[class_name] = {}
        self.instance_vars[class_name][param_name] = param_type
    
    def get_type(self, scope: str, var_name: str) -> Optional[str]:
        # Check local variables first
        if scope in self.local_vars and var_name in self.local_vars[scope]:
            return self.local_vars[scope][var_name]
        
        # Check instance variables if scope is a method
        if '.' in scope:
            # scope format is now module.Class.method
            parts = scope.split('.')
            if len(parts) >= 2:
                class_name = parts[-2]  # Second to last part is the class name
                if class_name in self.instance_vars and var_name in self.instance_vars[class_name]:
                    return self.instance_vars[class_name][var_name]
        
        return None


class DependencyAnalyzer:
    """
    PURPOSE: Main analyzer that combines pyreverse and AST analysis
    """
    def __init__(self, project_path: str = "./app"):
        self.project_path = Path(project_path)
        self.symbol_table = SymbolTable()
        self.type_inference = TypeInference(self.symbol_table)
        self.edges: List[Edge] = []
        self.inheritance_map: Dict[str, List[str]] = {}  # child -> [parents]
        self.builtin_functions = {
            'str', 'int', 'float', 'bool', 'list', 'dict', 'set', 'tuple',
            'len', 'range', 'enumerate', 'zip', 'map', 'filter', 'sorted',
            'max', 'min', 'sum', 'abs', 'round', 'isinstance', 'hasattr',
            'getattr', 'setattr', 'delattr', 'type', 'super', 'print'
        }
        self.stdlib_modules = {
            'os', 'sys', 'json', 'csv', 'ast', 're', 'subprocess', 'pathlib',
            'collections', 'dataclasses', 'typing', 'functools', 'itertools',
            'datetime', 'time', 'random', 'math', 'sqlite3', 'urllib', 'http',
            'email', 'logging', 'unittest', 'pickle', 'io', 'base64', 'hashlib',
            'uuid', 'copy', 'threading', 'multiprocessing', 'asyncio', 'queue',
            'heapq', 'bisect', 'weakref', 'gc', 'inspect', 'importlib', 'pkgutil',
            'traceback', 'warnings', 'contextlib', 'tempfile', 'shutil', 'glob',
            'fnmatch', 'linecache', 'textwrap', 'string', 'codecs', 'unicodedata'
        }
    
    def _is_builtin(self, target: str) -> bool:
        """Check if target is a built-in function"""
        return target in self.builtin_functions
    
    def _is_stdlib(self, target: str) -> bool:
        """Check if target is from standard library"""
        if not target:
            return False
        # Get the root module name
        root_module = target.split('.')[0]
        return root_module in self.stdlib_modules
    
    def _is_self_dependency(self, source: str, target: str) -> bool:
        """Check if this is a self-dependency within the same module"""
        if not source or not target:
            return False
        
        source_parts = source.split('.')
        target_parts = target.split('.')
        
        if len(source_parts) >= 1 and len(target_parts) >= 1:
            # Get the module path (first part for module-level, or first two parts for module.class)
            source_module = source_parts[0]  # e.g., 'auth' from 'auth.services.AuthService.login'
            target_module = target_parts[0]  # e.g., 'auth' from 'auth.services.AuthService.create_auth'
            
            # Consider it a self-dependency if they're in the same top-level module
            if source_module == target_module:
                return True
        
        return False
        
    def run_pyreverse(self) -> Tuple[str, str]:
        """
        PURPOSE: Run pyreverse to get structural information
        RETURNS: tuple of (dot_content, packages_content)
        """
        try:
            # Run pyreverse to generate DOT files
            result = subprocess.run([
                'pyreverse', '-o', 'dot', '-p', 'analysis', str(self.project_path)
            ], capture_output=True, text=True, cwd='.')
            
            if result.returncode != 0:
                print(f"Warning: pyreverse failed: {result.stderr}")
                return "", ""
            
            # Read generated files
            classes_dot = ""
            packages_dot = ""
            
            if os.path.exists('classes_analysis.dot'):
                with open('classes_analysis.dot', 'r') as f:
                    classes_dot = f.read()
                os.remove('classes_analysis.dot')
            
            if os.path.exists('packages_analysis.dot'):
                with open('packages_analysis.dot', 'r') as f:
                    packages_dot = f.read()
                os.remove('packages_analysis.dot')
            
            return classes_dot, packages_dot
            
        except FileNotFoundError:
            print("Warning: pyreverse not found. Install pylint for structural analysis.")
            return "", ""
    
    def parse_dot_file(self, dot_content: str):
        """
        PURPOSE: Parse DOT file content to extract relationships
        """
        lines = dot_content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Parse inheritance relationships
            if '->' in line and 'arrowhead=empty' in line:
                match = re.match(r'"([^"]+)"\s*->\s*"([^"]+)"', line)
                if match:
                    child, parent = match.groups()
                    child_full = self._normalize_class_name(child)
                    parent_full = self._normalize_class_name(parent)
                    
                    if child_full not in self.inheritance_map:
                        self.inheritance_map[child_full] = []
                    self.inheritance_map[child_full].append(parent_full)
                    
                    self.edges.append(Edge(
                        source=child_full,
                        target=parent_full,
                        edge_type="inherits",
                        certainty="high",
                        is_builtin=self._is_builtin(parent_full),
                        is_stdlib=self._is_stdlib(parent_full),
                        is_self_dep=self._is_self_dependency(child_full, parent_full)
                    ))
            
            # Parse associations
            elif '->' in line and ('arrowhead=diamond' in line or 'arrowhead=none' in line):
                match = re.match(r'"([^"]+)"\s*->\s*"([^"]+)"', line)
                if match:
                    source, target = match.groups()
                    source_full = self._normalize_class_name(source)
                    target_full = self._normalize_class_name(target)
                    
                    self.edges.append(Edge(
                        source=source_full,
                        target=target_full,
                        edge_type="associates",
                        certainty="high",
                        is_builtin=self._is_builtin(target_full),
                        is_stdlib=self._is_stdlib(target_full),
                        is_self_dep=self._is_self_dependency(source_full, target_full)
                    ))
    
    def _normalize_class_name(self, name: str) -> str:
        """
        PURPOSE: Normalize class names from DOT format to our format
        """
        # Remove quotes and handle module.Class format
        name = name.strip('"')
        if '.' in name:
            parts = name.split('.')
            if len(parts) >= 2:
                module_path = '.'.join(parts[:-1])
                class_name = parts[-1]
                return f"{module_path}.{class_name}"
        return name
    
    def analyze_ast(self):
        """
        PURPOSE: Walk AST to find method calls and build symbol table
        """
        for py_file in self.project_path.rglob("*.py"):
            if py_file.name.startswith('.'):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                module_name = self._get_module_name(py_file)
                self.symbol_table.add_module(module_name)
                
                visitor = ASTVisitor(module_name, self.symbol_table, self.type_inference, self.edges, self)
                visitor.visit(tree)
                
            except Exception as e:
                print(f"Warning: Failed to parse {py_file}: {e}")
    
    def _get_module_name(self, file_path: Path) -> str:
        """
        PURPOSE: Convert file path to module name
        """
        rel_path = file_path.relative_to(self.project_path)
        module_parts = list(rel_path.parts)
        
        # Remove .py extension
        if module_parts[-1].endswith('.py'):
            module_parts[-1] = module_parts[-1][:-3]
        
        # Remove __init__
        if module_parts[-1] == '__init__':
            module_parts.pop()
        
        return '.'.join(module_parts)
    
    def generate_csv(self, output_file: str = "dependency_graph.csv"):
        """
        PURPOSE: Generate CSV output with all edges
        """
        # Deduplicate edges
        unique_edges = {}
        for edge in self.edges:
            key = (edge.source, edge.target, edge.edge_type)
            if key not in unique_edges:
                unique_edges[key] = edge
            else:
                # Keep the edge with higher certainty
                existing_edge = unique_edges[key]
                if edge.certainty == "high" and existing_edge.certainty == "low":
                    unique_edges[key] = edge
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['dependant', 'depends', 'dependency_type', 'certainty', 'is_builtin', 'is_stdlib', 'is_self_dep'])
            
            for edge in unique_edges.values():
                writer.writerow([
                    edge.source,
                    edge.target,
                    edge.edge_type,
                    edge.certainty,
                    edge.is_builtin,
                    edge.is_stdlib,
                    edge.is_self_dep
                ])
        
        print(f"Generated {output_file} with {len(unique_edges)} unique edges (deduplicated from {len(self.edges)})")


class ASTVisitor(ast.NodeVisitor):
    """
    PURPOSE: AST visitor to extract method calls and definitions
    """
    def __init__(self, module_name: str, symbol_table: SymbolTable, 
                 type_inference: TypeInference, edges: List[Edge], analyzer: 'DependencyAnalyzer'):
        self.module_name = module_name
        self.symbol_table = symbol_table
        self.type_inference = type_inference
        self.edges = edges
        self.analyzer = analyzer
        self.current_class = None
        self.current_method = None
        self.current_scope = module_name
        
    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            alias_name = alias.asname or alias.name
            self.symbol_table.add_import(self.module_name, alias.name, alias_name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            for alias in node.names:
                full_name = f"{node.module}.{alias.name}" if alias.name != '*' else node.module
                alias_name = alias.asname or alias.name
                self.symbol_table.add_import(self.module_name, full_name, alias_name)
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        old_class = self.current_class
        old_scope = self.current_scope
        
        self.current_class = node.name
        class_full_name = self.symbol_table.add_class(self.module_name, node.name)
        self.current_scope = class_full_name
        self.type_inference.enter_scope(class_full_name)
        
        # Handle inheritance
        for base in node.bases:
            base_name = None
            if isinstance(base, ast.Name):
                base_name = self.symbol_table.resolve_name(self.module_name, base.id)
            elif isinstance(base, ast.Subscript):
                # Handle generic types like CrudBase[UUID, DTO]
                if isinstance(base.value, ast.Name):
                    base_name = self.symbol_table.resolve_name(self.module_name, base.value.id)
                elif isinstance(base.value, ast.Attribute):
                    # Handle qualified generic types like some.module.Base[T]
                    base_name = self._resolve_attribute_chain(base.value)
            elif isinstance(base, ast.Attribute):
                # Handle qualified base classes like some.module.BaseClass
                base_name = self._resolve_attribute_chain(base)
            
            if base_name:
                self.edges.append(Edge(
                    source=class_full_name,
                    target=base_name,
                    edge_type="inherits",
                    certainty="high",
                    is_builtin=self.analyzer._is_builtin(base_name),
                    is_stdlib=self.analyzer._is_stdlib(base_name),
                    is_self_dep=self.analyzer._is_self_dependency(class_full_name, base_name)
                ))
        
        self.generic_visit(node)
        
        self.current_class = old_class
        self.current_scope = old_scope
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        old_method = self.current_method
        old_scope = self.current_scope
        
        if self.current_class:
            # Method
            method_full_name = self.symbol_table.add_method(
                self.module_name, self.current_class, node.name
            )
            self.current_method = node.name
            self.current_scope = method_full_name
            
            # Track parameter types for all methods
            skip_first = 1 if node.name != '__init__' else 1  # Skip 'self' for methods
            for arg in node.args.args[skip_first:]:
                if arg.annotation:
                    param_type = self._extract_type_from_annotation(arg.annotation)
                    if param_type:
                        resolved_type = self.symbol_table.resolve_name(self.module_name, param_type)
                        if resolved_type:
                            if node.name == '__init__':
                                self.type_inference.add_constructor_param_type(
                                    self.current_class, arg.arg, resolved_type
                                )
                            # Add to local scope for all methods
                            self.type_inference.add_assignment(method_full_name, arg.arg, resolved_type)
        else:
            # Function
            func_full_name = self.symbol_table.add_function(self.module_name, node.name)
            self.current_scope = func_full_name
            
            # Track parameter types for functions
            for arg in node.args.args:
                if arg.annotation:
                    param_type = self._extract_type_from_annotation(arg.annotation)
                    if param_type:
                        resolved_type = self.symbol_table.resolve_name(self.module_name, param_type)
                        if resolved_type:
                            self.type_inference.add_assignment(func_full_name, arg.arg, resolved_type)
        
        self.type_inference.enter_scope(self.current_scope)
        
        # Analyze function body
        self.generic_visit(node)
        
        self.current_method = old_method
        self.current_scope = old_scope
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        # Handle async functions the same way as regular functions
        self.visit_FunctionDef(node)
    
    def _get_annotation_name(self, annotation: ast.AST) -> Optional[str]:
        """Extract type name from annotation"""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Attribute):
            return f"{annotation.value.id}.{annotation.attr}" if isinstance(annotation.value, ast.Name) else None
        return None
    
    def _extract_type_from_annotation(self, annotation: ast.AST) -> Optional[str]:
        """Extract actual type from complex annotations like FromDishka[QrCodeService]"""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Attribute):
            return f"{annotation.value.id}.{annotation.attr}" if isinstance(annotation.value, ast.Name) else None
        elif isinstance(annotation, ast.Subscript):
            # Handle generic types like FromDishka[QrCodeService]
            if isinstance(annotation.slice, ast.Name):
                # For FromDishka[QrCodeService], we want QrCodeService
                return annotation.slice.id
            elif isinstance(annotation.slice, ast.Attribute):
                # For FromDishka[some.module.Service]
                return self._resolve_attribute_chain(annotation.slice)
        return None
    
    def visit_Assign(self, node: ast.Assign):
        # Handle type inference for assignments
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id
            
            # Try to infer type from value
            if isinstance(node.value, ast.Call):
                if isinstance(node.value.func, ast.Name):
                    type_name = self.symbol_table.resolve_name(self.module_name, node.value.func.id)
                    if type_name:
                        self.type_inference.add_assignment(self.current_scope, var_name, type_name)
                elif isinstance(node.value.func, ast.Attribute):
                    # Handle qualified constructor calls like qrcode.main.QRCode()
                    full_path = self._resolve_attribute_chain(node.value.func)
                    if full_path:
                        self.type_inference.add_assignment(self.current_scope, var_name, full_path)
                    else:
                        # Fallback to old logic
                        if isinstance(node.value.func.value, ast.Name):
                            module_alias = node.value.func.value.id
                            class_name = node.value.func.attr
                            resolved_module = self.symbol_table.resolve_name(self.module_name, module_alias)
                            if resolved_module:
                                full_type = f"{resolved_module}.{class_name}"
                                self.type_inference.add_assignment(self.current_scope, var_name, full_type)
        
        # Handle self.attr = ... assignments
        elif (len(node.targets) == 1 and isinstance(node.targets[0], ast.Attribute) 
              and isinstance(node.targets[0].value, ast.Name) 
              and node.targets[0].value.id == 'self' and self.current_class):
            
            attr_name = node.targets[0].attr
            if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
                type_name = self.symbol_table.resolve_name(self.module_name, node.value.func.id)
                if type_name:
                    self.type_inference.add_instance_var(self.current_class, attr_name, type_name)
            elif isinstance(node.value, ast.Name):
                # Handle direct assignments like self.crud = crud
                # Look up the parameter type from constructor annotations
                if self.current_method == '__init__':
                    param_type = self.type_inference.get_type(self.current_scope, node.value.id)
                    if param_type:
                        self.type_inference.add_instance_var(self.current_class, attr_name, param_type)
        
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        # Analyze method/function calls
        self._analyze_call(node)
        self.generic_visit(node)
    
    def _analyze_call(self, node: ast.Call):
        """
        PURPOSE: Analyze a function/method call and create usage edges
        """
        certainty = "high"
        target = None
        
        if isinstance(node.func, ast.Name):
            # Direct function call: func()
            func_name = node.func.id
            
            # Check if it's a built-in function
            if func_name in self.analyzer.builtin_functions:
                target = func_name
                certainty = "high"
            else:
                target = self.symbol_table.resolve_name(self.module_name, func_name)
                if not target:
                    target = f"{self.module_name}.{func_name}"
                    certainty = "low"
        
        elif isinstance(node.func, ast.Attribute):
            # Method call: obj.method() or module.func()
            target, certainty = self._resolve_method_call(node.func)
        
        if target:
            is_self_dep = self.analyzer._is_self_dependency(self.current_scope, target)
            # Always create the edge, but mark self-dependencies
            self.edges.append(Edge(
                source=self.current_scope,
                target=target,
                edge_type="uses",
                certainty=certainty,
                is_builtin=self.analyzer._is_builtin(target),
                is_stdlib=self.analyzer._is_stdlib(target),
                is_self_dep=is_self_dep
            ))
    
    def _resolve_method_call(self, attr_node: ast.Attribute) -> Tuple[Optional[str], str]:
        """
        PURPOSE: Resolve method calls like obj.method() to target method
        """
        method_name = attr_node.attr
        certainty = "low"
        
        if isinstance(attr_node.value, ast.Name):
            obj_name = attr_node.value.id
            
            # Handle self.method()
            if obj_name == 'self' and self.current_class:
                target = f"{self.module_name}.{self.current_class}.{method_name}"
                return target, "high"
            
            # Handle super().method()
            elif obj_name == 'super' and self.current_class:
                # Find parent class from inheritance map
                current_full = f"{self.module_name}.{self.current_class}"
                if current_full in self.analyzer.inheritance_map:
                    for parent in self.analyzer.inheritance_map[current_full]:
                        target = f"{parent}.{method_name}"
                        return target, "high"
                return None, "low"
            
            # Try to resolve object type from local variables
            else:
                obj_type = self.type_inference.get_type(self.current_scope, obj_name)
                if obj_type:
                    # For external modules like fastapi.FastAPI, the method becomes fastapi.FastAPI.method_name
                    if '.' in obj_type and not ':' in obj_type:
                        # External module case
                        target = f"{obj_type}.{method_name}"
                    else:
                        # Internal class case
                        target = f"{obj_type}.{method_name}"
                    certainty = "high"
                else:
                    # Check if obj_name is an imported module
                    resolved_module = self.symbol_table.resolve_name(self.module_name, obj_name)
                    if resolved_module:
                        target = f"{resolved_module}.{method_name}"
                        certainty = "high"
                    else:
                        # Fallback: assume it's in current module
                        target = f"{self.module_name}.{obj_name}.{method_name}"
                        certainty = "low"
                
                return target, certainty
        
        elif isinstance(attr_node.value, ast.Attribute):
            # Handle self.attribute.method() calls
            if (isinstance(attr_node.value.value, ast.Name) 
                and attr_node.value.value.id == 'self' 
                and self.current_class):
                
                attr_name = attr_node.value.attr
                # Get the type of self.attribute
                attr_type = self.type_inference.get_type(
                    f"{self.module_name}.{self.current_class}", attr_name
                )
                if attr_type:
                    target = f"{attr_type}.{method_name}"
                    certainty = "high"
                    return target, certainty
                else:
                    # If we can't resolve the type, skip this dependency
                    return None, "low"

            # Handle other chained calls: module.submodule.function()
            full_path = self._resolve_attribute_chain(attr_node.value)
            if full_path:
                target = f"{full_path}.{method_name}"
                certainty = "high"
            else:
                # Skip unresolved chained calls to avoid noise
                return None, "low"
            return target, certainty
        
        return None, "low"
    
    
    def _resolve_attribute_chain(self, attr_node: ast.AST) -> Optional[str]:
        """
        PURPOSE: Resolve chained attributes like auth.api_errors to full module name
        """
        if not isinstance(attr_node, ast.Attribute):
            return None
            
        parts = []
        current = attr_node
        
        # Walk the chain backwards
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        
        if isinstance(current, ast.Name):
            parts.append(current.id)
            parts.reverse()
            
            # Check if the first part is an imported module
            base_name = parts[0]
            resolved_base = self.symbol_table.resolve_name(self.module_name, base_name)
            
            if resolved_base:
                # If it's a module import, combine with the rest of the path
                if len(parts) > 1:
                    return f"{resolved_base}.{'.'.join(parts[1:])}"
                else:
                    return resolved_base
            else:
                # Try as a direct module reference
                return '.'.join(parts)
        
        return None


def main():
    """
    PURPOSE: Main entry point for the dependency analyzer
    """
    analyzer = DependencyAnalyzer()
    
    print("Running pyreverse analysis...")
    classes_dot, packages_dot = analyzer.run_pyreverse()
    
    if classes_dot:
        print("Parsing pyreverse output...")
        analyzer.parse_dot_file(classes_dot)
    
    print("Analyzing AST for method calls...")
    analyzer.analyze_ast()
    
    print("Generating CSV output...")
    analyzer.generate_csv()
    
    print(f"Analysis complete. Found {len(analyzer.edges)} dependency edges.")


if __name__ == "__main__":
    main()