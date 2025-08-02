import ast
import importlib.util
import inspect
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Iterator


@dataclass
class CodeElement:
    type: Literal["class", "method", "function"]
    name: str
    purpose: str
    description: str
    arguments: list[str]
    returns: str
    start_line: int
    end_line: int
    header_end_line: int | None = None  # For classes: end of docstring/class definition


def parse_docstring(docstring: str) -> dict:
    """Parse docstring to extract PURPOSE, DESCRIPTION, ARGUMENTS, RETURNS."""
    if not docstring:
        return {"purpose": "", "description": "", "arguments": [], "returns": ""}

    lines = docstring.strip().split('\n')
    purpose = ""
    description = ""
    arguments = []
    returns = ""

    current_section = None

    for line in lines:
        line = line.strip()

        if line.startswith("PURPOSE:"):
            current_section = "purpose"
            purpose = line.replace("PURPOSE:", "").strip()
        elif line.startswith("DESCRIPTION:"):
            current_section = "description"
            description = line.replace("DESCRIPTION:", "").strip()
        elif line.startswith("ARGUMENTS:"):
            current_section = "arguments"
        elif line.startswith("RETURNS:"):
            current_section = "returns"
            returns = line.replace("RETURNS:", "").strip()
        elif current_section == "purpose" and line:
            purpose += " " + line
        elif current_section == "description" and line:
            description += " " + line
        elif current_section == "arguments" and line and ":" in line:
            arg_name = line.split(":")[0].strip()
            arguments.append(arg_name)
        elif current_section == "returns" and line:
            returns += " " + line
        elif not current_section and line:
            # First line without section is treated as description
            description = line if not description else description + " " + line

    return {
        "purpose": purpose.strip(),
        "description": description.strip(),
        "arguments": arguments,
        "returns": returns.strip()
    }


def find_class_header_end(source_lines: list[str], start_line: int) -> int:
    """Find the end line of a class header (including docstring, annotations, and __init__ method)."""
    # Convert to 0-based indexing for array access
    current_idx = start_line - 1

    # Find the class definition line first
    while current_idx < len(source_lines):
        line = source_lines[current_idx].strip()
        if line.startswith('class '):
            break
        current_idx += 1

    # Move to next line after class definition
    current_idx += 1
    docstring_end_idx = current_idx

    # Look for docstring first
    while current_idx < len(source_lines):
        line = source_lines[current_idx].strip()

        # If we find a triple-quoted docstring
        if line.startswith('"""') or line.startswith("'''"):
            quote_type = line[:3]

            # Single line docstring
            if line.count(quote_type) >= 2:
                docstring_end_idx = current_idx + 1
                break

            # Multi-line docstring - find the end
            current_idx += 1
            while current_idx < len(source_lines):
                if quote_type in source_lines[current_idx]:
                    docstring_end_idx = current_idx + 1
                    break
                current_idx += 1
            break

        # If we find actual code (not whitespace/comments), no docstring
        elif line and not line.startswith('#'):
            docstring_end_idx = current_idx
            break

        current_idx += 1

    # Now look for class annotations (field definitions) and __init__ method
    current_idx = docstring_end_idx - 1  # Convert back to 0-based
    header_end_idx = docstring_end_idx

    while current_idx < len(source_lines):
        line = source_lines[current_idx].strip()

        # Skip empty lines and comments
        if not line or line.startswith('#'):
            current_idx += 1
            continue

        # Check for class annotations (field definitions like "id: UUID = ...")
        if ':' in line and not line.startswith('def ') and not line.startswith('class '):
            header_end_idx = current_idx + 1
            current_idx += 1
            continue

        # Check for __init__ method
        if line.startswith('def __init__('):
            # Find the end of __init__ method
            indent_level = len(source_lines[current_idx]) - len(source_lines[current_idx].lstrip())
            current_idx += 1

            while current_idx < len(source_lines):
                line = source_lines[current_idx]
                if line.strip():  # Non-empty line
                    current_indent = len(line) - len(line.lstrip())
                    # If we've returned to class level or less, __init__ is done
                    if current_indent <= indent_level:
                        break
                header_end_idx = current_idx + 1
                current_idx += 1
            break

        # If we find any other method or class-level code, header is done
        elif line.startswith('def ') or line.startswith('class '):
            break

        current_idx += 1

    return header_end_idx  # Already 1-based


class NestedStructureVisitor(ast.NodeVisitor):
    """AST visitor to find nested classes and functions."""
    
    def __init__(self, source_lines: list[str]):
        self.source_lines = source_lines
        self.elements = []
        self.class_stack = []  # Track nested class context
        self.function_stack = []  # Track nested function context
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definitions, including nested ones."""
        # Build qualified name based on context
        if self.class_stack:
            qualified_name = ".".join(self.class_stack) + f".{node.name}"
        else:
            qualified_name = node.name
        
        # Extract docstring
        docstring = ast.get_docstring(node) or ""
        docstring_info = parse_docstring(docstring)
        
        # Calculate end line
        end_line = node.end_lineno if hasattr(node, 'end_lineno') and node.end_lineno else node.lineno
        
        # Find header end for nested classes (simplified approach)
        header_end_line = node.lineno
        if docstring:
            # Rough estimation - add lines for docstring
            header_end_line += len(docstring.split('\n')) + 2
        
        element = CodeElement(
            type="class",
            name=qualified_name,
            purpose=docstring_info["purpose"],
            description=docstring_info["description"],
            arguments=docstring_info["arguments"],
            returns=docstring_info["returns"],
            start_line=node.lineno,
            end_line=end_line,
            header_end_line=header_end_line
        )
        
        # Only add nested classes (not top-level ones, as they're handled by inspect)
        if self.class_stack:
            self.elements.append(element)
        
        # Enter nested context
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definitions, including nested ones."""
        self._visit_function_def(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definitions, including nested ones."""
        self._visit_function_def(node)
    
    def _visit_function_def(self, node) -> None:
        """Common logic for both sync and async function definitions."""
        # Build qualified name based on context
        if self.class_stack:
            qualified_name = ".".join(self.class_stack) + f".{node.name}"
            element_type = "method"
        elif self.function_stack:
            # This is a nested function
            qualified_name = ".".join(self.function_stack) + f".{node.name}"
            element_type = "function"
        else:
            # Top-level function (handled by inspect, so skip)
            qualified_name = node.name
            element_type = "function"
        
        # Extract docstring
        docstring = ast.get_docstring(node) or ""
        docstring_info = parse_docstring(docstring)
        
        # Calculate start line (include decorators if present)
        start_line = node.lineno
        if node.decorator_list:
            decorator_lines = [d.lineno for d in node.decorator_list]
            start_line = min(decorator_lines)
        
        # Calculate end line
        end_line = node.end_lineno if hasattr(node, 'end_lineno') and node.end_lineno else node.lineno
        
        element = CodeElement(
            type=element_type,  # noqa
            name=qualified_name,
            purpose=docstring_info["purpose"],
            description=docstring_info["description"],
            arguments=docstring_info["arguments"],
            returns=docstring_info["returns"],
            start_line=start_line,
            end_line=end_line
        )
        
        # Add nested methods and nested functions (skip top-level functions)
        if self.class_stack or self.function_stack:
            self.elements.append(element)
        
        # Enter function context for nested functions
        self.function_stack.append(node.name)
        self.generic_visit(node)
        self.function_stack.pop()


def find_nested_structures(file_path: str) -> Iterator[CodeElement]:
    """Use AST parsing to find nested classes and functions."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
            source_lines = source.split('\n')
        
        tree = ast.parse(source)
        visitor = NestedStructureVisitor(source_lines)
        visitor.visit(tree)
        
        for element in visitor.elements:
            yield element
            
    except (SyntaxError, FileNotFoundError, UnicodeDecodeError):
        return


def ast_parse_top_level_structures(file_path: str) -> Iterator[CodeElement]:
    """Use AST parsing to find top-level classes and functions when inspect fails."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()

        tree = ast.parse(source)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Only process top-level classes (not nested ones)
                if hasattr(node, 'col_offset') and node.col_offset == 0:
                    # Extract docstring
                    docstring = ast.get_docstring(node) or ""
                    docstring_info = parse_docstring(docstring)
                    
                    # Calculate end line
                    end_line = node.end_lineno if hasattr(node, 'end_lineno') and node.end_lineno else node.lineno
                    
                    # Find header end line
                    header_end_line = node.lineno
                    if docstring:
                        # Rough estimation - add lines for docstring
                        header_end_line += len(docstring.split('\n')) + 2
                    
                    yield CodeElement(
                        type="class",
                        name=node.name,
                        purpose=docstring_info["purpose"],
                        description=docstring_info["description"],
                        arguments=docstring_info["arguments"],
                        returns=docstring_info["returns"],
                        start_line=node.lineno,
                        end_line=end_line,
                        header_end_line=header_end_line
                    )
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Only process top-level functions (not nested ones)
                if hasattr(node, 'col_offset') and node.col_offset == 0:
                    # Extract docstring
                    docstring = ast.get_docstring(node) or ""
                    docstring_info = parse_docstring(docstring)
                    
                    # Calculate start line (include decorators if present)
                    start_line = node.lineno
                    if node.decorator_list:
                        decorator_lines = [d.lineno for d in node.decorator_list]
                        start_line = min(decorator_lines)
                    
                    # Calculate end line
                    end_line = node.end_lineno if hasattr(node, 'end_lineno') and node.end_lineno else node.lineno
                    
                    yield CodeElement(
                        type="function",
                        name=node.name,
                        purpose=docstring_info["purpose"],
                        description=docstring_info["description"],
                        arguments=docstring_info["arguments"],
                        returns=docstring_info["returns"],
                        start_line=start_line,
                        end_line=end_line
                    )
            
    except (SyntaxError, FileNotFoundError, UnicodeDecodeError):
        return


def parse_python_module(file_path: str) -> Iterator[CodeElement]:
    """Parse a Python module using inspect to extract classes, methods, and functions."""
    spec = None
    try:
        file_path_obj = Path(file_path)
        
        # Try to determine the package structure
        parent_dir = file_path_obj.parent
        module_name = file_path_obj.stem
        
        # Add the parent directory to sys.path for imports
        parent_str = str(parent_dir)
        added_to_path = False
        if parent_str not in sys.path:
            sys.path.insert(0, parent_str)
            added_to_path = True
        
        try:
            # Load the module with proper package context
            if parent_dir.name and (parent_dir / "__init__.py").exists():
                # This is part of a package
                package_name = parent_dir.name
                full_module_name = f"{package_name}.{module_name}"
                spec = importlib.util.spec_from_file_location(full_module_name, file_path)
            else:
                # Standalone module
                spec = importlib.util.spec_from_file_location(module_name, file_path)
            
            if spec is None or spec.loader is None:
                return

            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
        finally:
            # Clean up sys.path if we added to it
            if added_to_path and parent_str in sys.path:
                sys.path.remove(parent_str)

        # Get source lines for line number mapping
        with open(file_path, 'r', encoding='utf-8') as f:
            source_lines = f.readlines()

        # Parse classes
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if obj.__module__ == module.__name__:
                try:
                    source_info = inspect.getsourcelines(obj)
                    start_line = source_info[1]
                    end_line = start_line + len(source_info[0]) - 1
                    header_end_line = find_class_header_end(source_lines, start_line)

                    docstring_info = parse_docstring(obj.__doc__ or "")

                    yield CodeElement(
                        type="class",
                        name=name,
                        purpose=docstring_info["purpose"],
                        description=docstring_info["description"],
                        arguments=docstring_info["arguments"],
                        returns=docstring_info["returns"],
                        start_line=start_line,
                        end_line=end_line,
                        header_end_line=header_end_line
                    )

                    # Parse methods within the class (only user-defined methods)
                    for method_name, method_obj in inspect.getmembers(obj, inspect.isfunction):
                        # Skip methods defined in parent classes or external modules
                        if (hasattr(method_obj, '__qualname__') and
                            method_obj.__qualname__.startswith(name + '.') and
                            method_obj.__module__ == module.__name__):
                            try:
                                method_source_info = inspect.getsourcelines(method_obj)
                                method_start_line = method_source_info[1]
                                method_end_line = method_start_line + len(method_source_info[0]) - 1

                                # Check for decorators above the method
                                decorator_start = method_start_line
                                if method_start_line > 1:
                                    # Look backwards for decorators
                                    for i in range(method_start_line - 1, max(0, method_start_line - 10), -1):
                                        if i <= len(source_lines):
                                            line = source_lines[i - 1].strip()
                                            if line.startswith('@'):
                                                decorator_start = i
                                            elif line and not line.startswith('#'):
                                                # Non-decorator, non-comment line found, stop looking
                                                break

                                method_docstring_info = parse_docstring(method_obj.__doc__ or "")

                                yield CodeElement(
                                    type="method",
                                    name=f"{name}.{method_name}",
                                    purpose=method_docstring_info["purpose"],
                                    description=method_docstring_info["description"],
                                    arguments=method_docstring_info["arguments"],
                                    returns=method_docstring_info["returns"],
                                    start_line=decorator_start,
                                    end_line=method_end_line
                                )
                            except (OSError, TypeError):
                                continue

                except (OSError, TypeError):
                    continue

        # Parse standalone functions
        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if obj.__module__ == module.__name__:
                try:
                    source_info = inspect.getsourcelines(obj)
                    start_line = source_info[1]
                    end_line = start_line + len(source_info[0]) - 1

                    # Check for decorators above the function
                    decorator_start = start_line
                    if start_line > 1:
                        # Look backwards for decorators
                        for i in range(start_line - 1, max(0, start_line - 10), -1):
                            if i <= len(source_lines):
                                line = source_lines[i - 1].strip()
                                if line.startswith('@'):
                                    decorator_start = i
                                elif line and not line.startswith('#'):
                                    # Non-decorator, non-comment line found, stop looking
                                    break

                    docstring_info = parse_docstring(obj.__doc__ or "")

                    yield CodeElement(
                        type="function",
                        name=name,
                        purpose=docstring_info["purpose"],
                        description=docstring_info["description"],
                        arguments=docstring_info["arguments"],
                        returns=docstring_info["returns"],
                        start_line=decorator_start,
                        end_line=end_line
                    )
                except (OSError, TypeError):
                    continue

    except Exception:
        return
    finally:
        # Clean up the loaded module
        if spec and spec.name in sys.modules:
            del sys.modules[spec.name]


def parse_python_file(file_path: str) -> Iterator[CodeElement]:
    """Parse a single Python file and yield CodeElement objects."""
    # Try inspect-based parsing first (more accurate for introspection)
    elements_found = False
    try:
        for element in parse_python_module(file_path):
            elements_found = True
            yield element
    except Exception:
        # If inspect-based parsing fails, we'll fall back to AST-only
        pass
    
    # Get nested structures from AST-based parsing
    for element in find_nested_structures(file_path):
        yield element
        
    # If inspect-based parsing failed and we need top-level structures,
    # fall back to AST-only parsing for top-level structures
    if not elements_found:
        for element in ast_parse_top_level_structures(file_path):
            yield element


def parse_module_recursively(module_path: str) -> Iterator[tuple[str, CodeElement]]:
    """Parse all .py files in a module recursively and yield (file_path, CodeElement) tuples."""
    module_path = Path(module_path)

    if not module_path.exists():
        return

    for py_file in module_path.rglob("*.py"):
        try:
            relative_path = py_file.relative_to(module_path)
            for element in parse_python_file(str(py_file)):
                yield str(relative_path), element
        except (ValueError, OSError):
            continue


if __name__ == "__main__":
    if len(sys.argv) > 1:
        module_path = sys.argv[1]
        for file_path, element in parse_module_recursively(module_path):
            print(f"{element.type}: {element.name} in {file_path}")
            print(f"  Purpose: {element.purpose}")
            print(f"  Description: {element.description}")
            print(f"  Arguments: {element.arguments}")
            print(f"  Returns: {element.returns}")
            print(f"  Lines: {element.start_line}-{element.end_line}")
            print()
