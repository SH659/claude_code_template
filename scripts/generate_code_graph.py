#!/usr/bin/env python3
"""
PURPOSE: Generate comprehensive code graph combining structural and dependency information
DESCRIPTION: Creates CODE_GRAPH.xml with hierarchical semantic tags containing full docstring 
            information and dependency relationships. Reuses existing parsing logic from 
            parse_module.py and parse_graph.py without reading artifact files.
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict

# Import existing parsing logic
from parse_module import parse_module_recursively, CodeElement
from parse_graph import DependencyAnalyzer, Edge


class CodeGraphGenerator:
    """
    PURPOSE: Generate XML code graph from parsed module and dependency data
    DESCRIPTION: Combines structural analysis from parse_module with dependency analysis
                from parse_graph to create comprehensive XML representation with filtering
    """
    
    def __init__(self, project_path: str = "./app"):
        self.project_path = Path(project_path)
        self.elements: Dict[str, CodeElement] = {}
        self.edges: List[Edge] = []
        self.dependency_map: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))
        
        # Configuration flags
        self.use_full_prefixes: bool = False
        self.use_subtags: bool = True
        
    def analyze_project(self):
        """
        PURPOSE: Run complete analysis of project structure and dependencies
        DESCRIPTION: Uses existing parsing logic to extract code elements and relationships
        """
        print("Analyzing project structure...")
        
        # Parse module structure using existing logic
        for file_path, element in parse_module_recursively(str(self.project_path)):
            # Create qualified name for element
            module_name = self._file_path_to_module(file_path)
            if element.type == "class":
                qualified_name = f"{module_name}.{element.name}"
            elif element.type == "method":
                # element.name is already in format Class.method
                qualified_name = f"{module_name}.{element.name}"
            elif element.type == "function":
                qualified_name = f"{module_name}.{element.name}"
            else:
                qualified_name = f"{module_name}.{element.name}"
            
            # Enhance the element with properly parsed docstring if needed
            self._enhance_element_docstring(element, file_path)
            self.elements[qualified_name] = element
            
        print(f"Found {len(self.elements)} code elements")
        
        # Analyze dependencies using existing logic
        print("Analyzing dependencies...")
        analyzer = DependencyAnalyzer(str(self.project_path))
        
        # Run pyreverse analysis
        classes_dot, packages_dot = analyzer.run_pyreverse()
        if classes_dot:
            analyzer.parse_dot_file(classes_dot)
        
        # Run AST analysis
        analyzer.analyze_ast()
        
        self.edges = analyzer.edges
        print(f"Found {len(self.edges)} dependency edges")
        
        # Group edges by source for easy lookup
        for edge in self.edges:
            self.dependency_map[edge.source][edge.edge_type].append(edge.target)
    
    def _enhance_element_docstring(self, element: CodeElement, file_path: str):
        """
        PURPOSE: Enhance element with better docstring parsing
        DESCRIPTION: Reads the actual source file to get raw docstring and parse it properly
        """
        try:
            # Read the source file
            full_file_path = self.project_path / file_path
            if not full_file_path.exists():
                return
                
            with open(full_file_path, 'r', encoding='utf-8') as f:
                source_lines = f.readlines()
            
            # Extract docstring lines for this element
            if hasattr(element, 'start_line') and hasattr(element, 'end_line'):
                start_idx = element.start_line - 1  # Convert to 0-based
                end_idx = min(element.end_line, len(source_lines))
                
                # Find docstring within the element
                raw_docstring = self._extract_raw_docstring(source_lines[start_idx:end_idx])
                if raw_docstring:
                    # Parse the raw docstring with our enhanced parser
                    parsed = self._parse_enhanced_docstring(raw_docstring)
                    
                    # Update element with enhanced information
                    if parsed["purpose"]:
                        element.purpose = parsed["purpose"]
                    if parsed["description"]:
                        element.description = parsed["description"]
                    if parsed["arguments"]:
                        element.arguments = parsed["arguments"]
                    if parsed["returns"]:
                        element.returns = parsed["returns"]
                    
                    # Add contracts as a new attribute
                    element.contracts = parsed["contracts"]
                    
        except Exception:
            # If anything fails, just keep the original parsing
            pass
    
    def _extract_raw_docstring(self, source_lines: List[str]) -> str:
        """
        PURPOSE: Extract raw docstring from source code lines
        DESCRIPTION: Finds and extracts the docstring text from function/class/method source
        """
        docstring_lines = []
        in_docstring = False
        quote_type = None
        
        for line in source_lines:
            stripped = line.strip()
            
            if not in_docstring:
                # Look for start of docstring
                if '"""' in stripped or "'''" in stripped:
                    if '"""' in stripped:
                        quote_type = '"""'
                    else:
                        quote_type = "'''"
                    
                    in_docstring = True
                    # Extract text after opening quotes
                    quote_pos = stripped.find(quote_type)
                    after_quotes = stripped[quote_pos + 3:]
                    
                    # Check if it's a single-line docstring
                    if quote_type in after_quotes:
                        # Single line docstring
                        end_pos = after_quotes.find(quote_type)
                        return after_quotes[:end_pos]
                    else:
                        # Multi-line docstring
                        if after_quotes.strip():
                            docstring_lines.append(after_quotes)
            else:
                # We're inside a docstring
                if quote_type in stripped:
                    # End of docstring
                    end_pos = stripped.find(quote_type)
                    if end_pos > 0:
                        docstring_lines.append(stripped[:end_pos])
                    break
                else:
                    # Continue collecting docstring lines
                    docstring_lines.append(line.rstrip())
        
        return '\n'.join(docstring_lines) if docstring_lines else ""
    
    def _file_path_to_module(self, file_path: str) -> str:
        """
        PURPOSE: Convert file path to module name format
        DESCRIPTION: Transforms relative file paths to dot-separated module names
        """
        # Remove .py extension and convert path separators to dots
        module_path = file_path.replace('.py', '').replace('/', '.').replace('\\', '.')
        return module_path
    
    def _should_include_edge(self, edge: Edge, include_builtin: bool, 
                           include_stdlib: bool, include_self_dep: bool,
                           include_certainty: str) -> bool:
        """
        PURPOSE: Apply filtering logic to determine if edge should be included
        DESCRIPTION: Checks edge properties against command-line filter arguments
        """
        if not include_builtin and edge.is_builtin:
            return False
        if not include_stdlib and edge.is_stdlib:
            return False
        if not include_self_dep and edge.is_self_dep:
            return False
        if include_certainty != "all" and edge.certainty != include_certainty:
            return False
        return True
    
    def _sanitize_xml_content(self, content: str) -> str:
        """
        PURPOSE: Escape XML special characters in content
        DESCRIPTION: Replaces XML special characters to prevent parsing errors
        """
        if not content:
            return ""
        return (content.replace("&", "&amp;")
                      .replace("<", "&lt;")
                      .replace(">", "&gt;")
                      .replace("\"", "&quot;")
                      .replace("'", "&apos;"))
    
    def _get_tag_name(self, qualified_name: str, section: str = None) -> str:
        """
        PURPOSE: Convert qualified name to XML tag name
        DESCRIPTION: Transforms module.class.method based on prefix configuration
        """
        parts = qualified_name.split('.')
        if self.use_full_prefixes:
            base_name = "_".join(parts)
            if section:
                return f"{base_name}_{section}"
            return base_name
        else:
            if section:
                return section
            return parts[-1]  # Just the element name
    
    def _parse_enhanced_docstring(self, docstring: str) -> dict:
        """
        PURPOSE: Enhanced docstring parser that preserves full formatting
        DESCRIPTION: Extracts all docstring sections with proper formatting for XML output
        """
        if not docstring:
            return {
                "purpose": "", "description": "", "arguments": [], 
                "returns": "", "contracts": ""
            }

        lines = docstring.strip().split('\n')
        purpose = ""
        description = ""
        arguments = []
        returns = ""
        contracts = []
        
        current_section = None

        for line in lines:
            stripped_line = line.strip()

            if stripped_line.startswith("PURPOSE:"):
                current_section = "purpose"
                purpose = stripped_line.replace("PURPOSE:", "").strip()
            elif stripped_line.startswith("DESCRIPTION:"):
                current_section = "description"
                description = stripped_line.replace("DESCRIPTION:", "").strip()
            elif stripped_line.startswith("ARGUMENTS:"):
                current_section = "arguments"
            elif stripped_line.startswith("RETURNS:"):
                current_section = "returns"
                returns = stripped_line.replace("RETURNS:", "").strip()
            elif stripped_line.startswith("CONTRACTS:"):
                current_section = "contracts"
            elif current_section == "purpose" and stripped_line:
                purpose += " " + stripped_line
            elif current_section == "description" and stripped_line:
                description += " " + stripped_line
            elif current_section == "arguments" and stripped_line:
                # Preserve full argument line: "param_name: type - Description"
                arguments.append(stripped_line)
            elif current_section == "returns" and stripped_line:
                returns += " " + stripped_line
            elif current_section == "contracts" and stripped_line:
                # Preserve contract formatting with indentation
                contracts.append(stripped_line)
            elif not current_section and stripped_line:
                # First line without section is treated as description
                description = stripped_line if not description else description + " " + stripped_line

        return {
            "purpose": purpose.strip(),
            "description": description.strip(),
            "arguments": arguments,
            "returns": returns.strip(),
            "contracts": '\n'.join(contracts) if contracts else ""
        }
    
    def generate_xml(self, include_builtin: bool = True, include_stdlib: bool = True,
                    include_self_dep: bool = True, include_certainty: str = "all",
                    use_full_prefixes: bool = False, use_subtags: bool = True) -> str:
        """
        PURPOSE: Generate complete XML code graph with filtering
        DESCRIPTION: Creates hierarchical XML structure with embedded dependencies
        ARGUMENTS:
            include_builtin: bool - Include built-in dependencies
            include_stdlib: bool - Include standard library dependencies  
            include_self_dep: bool - Include internal dependencies
            include_certainty: str - Filter by certainty level (all, high, low)
            use_full_prefixes: bool - Use full prefixes (auth_api_errors_ApiErrors_PURPOSE) vs simple names (PURPOSE)
            use_subtags: bool - Use subtags format vs plain text with indentation
        RETURNS: str - Complete XML content
        """
        self.use_full_prefixes = use_full_prefixes
        self.use_subtags = use_subtags
        
        xml_lines = []
        
        # Group elements by module hierarchy
        module_hierarchy = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        
        for qualified_name, element in self.elements.items():
            parts = qualified_name.split('.')
            if len(parts) >= 2:
                module = parts[0]
                submodule = parts[1] if len(parts) > 2 else parts[1]
                
                if element.type == "class":
                    if len(parts) == 2:  # top-level class
                        module_hierarchy[module][submodule]["classes"].append((qualified_name, element))
                    else:  # nested class
                        module_hierarchy[module][submodule]["classes"].append((qualified_name, element))
                elif element.type == "method":
                    # Methods are grouped under their parent class
                    module_hierarchy[module][submodule]["methods"].append((qualified_name, element))
                elif element.type == "function":
                    module_hierarchy[module][submodule]["functions"].append((qualified_name, element))
        
        # Generate XML for each module
        for module_name in sorted(module_hierarchy.keys()):
            xml_lines.append(f'<{module_name}>')
            
            for submodule_name in sorted(module_hierarchy[module_name].keys()):
                xml_lines.append(f'<{module_name}_{submodule_name}>')
                
                # Add classes first
                for qualified_name, element in sorted(module_hierarchy[module_name][submodule_name]["classes"]):
                    self._generate_element_xml(xml_lines, qualified_name, element, 
                                             include_builtin, include_stdlib, 
                                             include_self_dep, include_certainty)
                
                # Add standalone functions
                for qualified_name, element in sorted(module_hierarchy[module_name][submodule_name]["functions"]):
                    self._generate_element_xml(xml_lines, qualified_name, element,
                                             include_builtin, include_stdlib,
                                             include_self_dep, include_certainty)
                
                xml_lines.append(f'</{module_name}_{submodule_name}>')
            
            xml_lines.append(f'</{module_name}>')
        
        # No closing tag needed since we removed the root GRAPH tag
        return '\n'.join(xml_lines)
    
    def _generate_element_xml(self, xml_lines: List[str], qualified_name: str, 
                            element: CodeElement, include_builtin: bool,
                            include_stdlib: bool, include_self_dep: bool,
                            include_certainty: str):
        """
        PURPOSE: Generate XML section for a single code element
        DESCRIPTION: Creates hierarchical XML tags with docstring information and dependencies
        """
        tag_name = self._get_tag_name(qualified_name)
        xml_lines.append(f'<{tag_name}>')
        
        if self.use_subtags:
            self._generate_subtags_format(xml_lines, qualified_name, element, 
                                        include_builtin, include_stdlib, 
                                        include_self_dep, include_certainty)
        else:
            self._generate_text_format(xml_lines, qualified_name, element,
                                     include_builtin, include_stdlib,
                                     include_self_dep, include_certainty)
        
        # Handle methods under classes
        if element.type == "class":
            # Find all methods for this class
            class_methods = [
                (qname, elem) for qname, elem in self.elements.items()
                if elem.type == "method" and qname.startswith(qualified_name + ".")
            ]
            
            for method_qualified_name, method_element in sorted(class_methods):
                self._generate_element_xml(xml_lines, method_qualified_name, method_element,
                                         include_builtin, include_stdlib, 
                                         include_self_dep, include_certainty)
        
        xml_lines.append(f'</{tag_name}>')
    
    def _generate_subtags_format(self, xml_lines: List[str], qualified_name: str,
                               element: CodeElement, include_builtin: bool,
                               include_stdlib: bool, include_self_dep: bool,
                               include_certainty: str):
        """
        PURPOSE: Generate XML with subtags format
        DESCRIPTION: Creates separate XML tags for each docstring section
        """
        # Add docstring information directly from element (which may have been enhanced)
        if element.purpose:
            purpose_tag = self._get_tag_name(qualified_name, "PURPOSE")
            xml_lines.append(f'<{purpose_tag}>')
            xml_lines.append(self._sanitize_xml_content(element.purpose))
            xml_lines.append(f'</{purpose_tag}>')
        
        if element.description:
            description_tag = self._get_tag_name(qualified_name, "DESCRIPTION")
            xml_lines.append(f'<{description_tag}>')
            xml_lines.append(self._sanitize_xml_content(element.description))
            xml_lines.append(f'</{description_tag}>')
        
        # Add attributes section (for classes mainly) 
        if element.arguments and element.type == "class":
            attributes_tag = self._get_tag_name(qualified_name, "ATTRIBUTES")
            xml_lines.append(f'<{attributes_tag}>')
            for arg in element.arguments:
                xml_lines.append(self._sanitize_xml_content(arg))
            xml_lines.append(f'</{attributes_tag}>')
        
        # Add arguments section (for methods/functions)
        if element.arguments and element.type in ["method", "function"]:
            arguments_tag = self._get_tag_name(qualified_name, "ARGUMENTS")
            xml_lines.append(f'<{arguments_tag}>')
            for arg in element.arguments:
                xml_lines.append(self._sanitize_xml_content(arg))
            xml_lines.append(f'</{arguments_tag}>')
        
        # Add returns section
        if element.returns:
            returns_tag = self._get_tag_name(qualified_name, "RETURNS")
            xml_lines.append(f'<{returns_tag}>')
            xml_lines.append(self._sanitize_xml_content(element.returns))
            xml_lines.append(f'</{returns_tag}>')
        
        # Add contracts section (if enhanced parsing found contracts)
        if hasattr(element, 'contracts') and element.contracts:
            contracts_tag = self._get_tag_name(qualified_name, "CONTRACTS")
            xml_lines.append(f'<{contracts_tag}>')
            xml_lines.append(self._sanitize_xml_content(element.contracts))
            xml_lines.append(f'</{contracts_tag}>')
        
        # Add location
        if hasattr(element, 'start_line') and hasattr(element, 'end_line'):
            # Reconstruct file path from qualified name
            parts = qualified_name.split('.')
            if len(parts) >= 2:
                file_path = '/'.join(parts[:-1]) + '.py'
                if element.type == "method":
                    # For methods, the file path needs special handling
                    method_parts = parts[-1].split('.')
                    if len(method_parts) > 1:
                        file_path = '/'.join(parts[:-1]) + '.py'
                
                location = f"{file_path}#L{element.start_line}-{element.end_line}"
                location_tag = self._get_tag_name(qualified_name, "LOCATION")
                xml_lines.append(f'<{location_tag}>{location}</{location_tag}>')
        
        # Add dependency edges
        if qualified_name in self.dependency_map:
            for edge_type, targets in self.dependency_map[qualified_name].items():
                filtered_targets = []
                for target in targets:
                    # Find the edge to check filters
                    matching_edges = [e for e in self.edges 
                                    if e.source == qualified_name and e.target == target and e.edge_type == edge_type]
                    if matching_edges:
                        edge = matching_edges[0]
                        if self._should_include_edge(edge, include_builtin, include_stdlib, 
                                                   include_self_dep, include_certainty):
                            filtered_targets.append(target)
                
                if filtered_targets:
                    edge_type_upper = edge_type.upper()
                    edge_tag = self._get_tag_name(qualified_name, edge_type_upper)
                    xml_lines.append(f'<{edge_tag}>')
                    for target in sorted(set(filtered_targets)):  # Remove duplicates and sort
                        xml_lines.append(self._sanitize_xml_content(target))
                    xml_lines.append(f'</{edge_tag}>')
    
    def _generate_text_format(self, xml_lines: List[str], qualified_name: str,
                            element: CodeElement, include_builtin: bool,
                            include_stdlib: bool, include_self_dep: bool,
                            include_certainty: str):
        """
        PURPOSE: Generate XML with text format (indented like docstrings)
        DESCRIPTION: Creates plain text content with indentation like project docstring format
        """
        content_lines = []
        
        # Add docstring information in text format
        if element.purpose:
            content_lines.append(f"PURPOSE: {element.purpose}")
        
        if element.description:
            content_lines.append(f"DESCRIPTION: {element.description}")
        
        # Add attributes section (for classes mainly) 
        if element.arguments and element.type == "class":
            content_lines.append("ATTRIBUTES:")
            for arg in element.arguments:
                content_lines.append(f"    {arg}")
        
        # Add arguments section (for methods/functions)
        if element.arguments and element.type in ["method", "function"]:
            content_lines.append("ARGUMENTS:")
            for arg in element.arguments:
                content_lines.append(f"    {arg}")
        
        # Add returns section
        if element.returns:
            content_lines.append(f"RETURNS: {element.returns}")
        
        # Add contracts section (if enhanced parsing found contracts)
        if hasattr(element, 'contracts') and element.contracts:
            content_lines.append("CONTRACTS:")
            # Split contracts by lines and indent properly
            contract_lines = element.contracts.split('\n')
            for contract_line in contract_lines:
                if contract_line.strip():
                    content_lines.append(f"    {contract_line.strip()}")
        
        # Add location
        if hasattr(element, 'start_line') and hasattr(element, 'end_line'):
            # Reconstruct file path from qualified name
            parts = qualified_name.split('.')
            if len(parts) >= 2:
                file_path = '/'.join(parts[:-1]) + '.py'
                if element.type == "method":
                    # For methods, the file path needs special handling
                    method_parts = parts[-1].split('.')
                    if len(method_parts) > 1:
                        file_path = '/'.join(parts[:-1]) + '.py'
                
                location = f"{file_path}#L{element.start_line}-{element.end_line}"
                content_lines.append(f"LOCATION: {location}")
        
        # Add dependency edges
        if qualified_name in self.dependency_map:
            for edge_type, targets in self.dependency_map[qualified_name].items():
                filtered_targets = []
                for target in targets:
                    # Find the edge to check filters
                    matching_edges = [e for e in self.edges 
                                    if e.source == qualified_name and e.target == target and e.edge_type == edge_type]
                    if matching_edges:
                        edge = matching_edges[0]
                        if self._should_include_edge(edge, include_builtin, include_stdlib, 
                                                   include_self_dep, include_certainty):
                            filtered_targets.append(target)
                
                if filtered_targets:
                    edge_type_upper = edge_type.upper()
                    content_lines.append(f"{edge_type_upper}:")
                    for target in sorted(set(filtered_targets)):  # Remove duplicates and sort
                        content_lines.append(f"    {target}")
        
        # Add all content as sanitized XML text
        if content_lines:
            xml_lines.append(self._sanitize_xml_content('\n'.join(content_lines)))


def main():
    """
    PURPOSE: Main entry point for code graph generation
    DESCRIPTION: Parses command line arguments and generates filtered XML code graph
    """
    parser = argparse.ArgumentParser(description="Generate comprehensive code graph")
    parser.add_argument("--project-path", default="./app", 
                       help="Path to project directory (default: ./app)")
    parser.add_argument("--output", default="CODE_GRAPH.xml",
                       help="Output file path (default: CODE_GRAPH.xml)")
    parser.add_argument("--include-builtin", action="store_true", default=True,
                       help="Include built-in dependencies (default: True)")
    parser.add_argument("--no-builtin", action="store_false", dest="include_builtin",
                       help="Exclude built-in dependencies")
    parser.add_argument("--include-stdlib", action="store_true", default=True,
                       help="Include standard library dependencies (default: True)")
    parser.add_argument("--no-stdlib", action="store_false", dest="include_stdlib",
                       help="Exclude standard library dependencies")
    parser.add_argument("--include-self-dep", action="store_true", default=True,
                       help="Include internal dependencies (default: True)")
    parser.add_argument("--no-self-dep", action="store_false", dest="include_self_dep",
                       help="Exclude internal dependencies")
    parser.add_argument("--include-certainty", choices=["all", "high", "low"], default="all",
                       help="Filter by certainty level (default: all)")
    parser.add_argument("--use-full-prefixes", action="store_true", default=False,
                       help="Use full prefixes (auth_api_errors_ApiErrors_PURPOSE) vs simple names (PURPOSE)")
    parser.add_argument("--use-subtags", action="store_true", default=True,
                       help="Use subtags format vs plain text with indentation")
    parser.add_argument("--no-subtags", action="store_false", dest="use_subtags",
                       help="Use plain text format instead of subtags")
    
    args = parser.parse_args()
    
    if not Path(args.project_path).exists():
        print(f"Error: Project path '{args.project_path}' does not exist")
        sys.exit(1)
    
    print("Starting code graph generation...")
    
    generator = CodeGraphGenerator(args.project_path)
    generator.analyze_project()
    
    print("Generating XML...")
    xml_content = generator.generate_xml(
        include_builtin=args.include_builtin,
        include_stdlib=args.include_stdlib,
        include_self_dep=args.include_self_dep,
        include_certainty=args.include_certainty,
        use_full_prefixes=args.use_full_prefixes,
        use_subtags=args.use_subtags
    )
    
    # Write output
    output_path = Path(args.output)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    
    print(f"Code graph generated successfully: {output_path}")
    print(f"Total elements: {len(generator.elements)}")
    print(f"Total edges: {len(generator.edges)}")


if __name__ == "__main__":
    main()