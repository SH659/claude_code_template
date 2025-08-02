#!/usr/bin/env python3

import sys
from pathlib import Path

from parse_module import parse_module_recursively


def generate_module_map(module_path: str) -> str:
    """Generate a MODULE_MAP.md content for the given module path."""
    module_path = Path(module_path)
    
    classes = []
    methods = []
    functions = []
    
    # Use sets to track seen elements and avoid duplicates
    seen_classes = set()
    seen_methods = set()
    seen_functions = set()
    
    for file_path, element in parse_module_recursively(str(module_path)):
        description = element.description or element.purpose or "No description available"
        
        if element.type == "class":
            # For classes: show header range and full range
            header_end = element.header_end_line or element.start_line
            file_ref = f"@{file_path}#L{element.start_line}-{header_end}-{element.end_line}"
            entry = f"- {file_ref} - {element.name} - {description}"
            
            # Use element name and file path as unique key
            key = (file_path, element.name, element.start_line)
            if key not in seen_classes:
                classes.append(entry)
                seen_classes.add(key)
                
        elif element.type == "method":
            file_ref = f"@{file_path}#L{element.start_line}-{element.end_line}"
            entry = f"- {file_ref} - {element.name} - {description}"
            
            key = (file_path, element.name, element.start_line)
            if key not in seen_methods:
                methods.append(entry)
                seen_methods.add(key)
                
        elif element.type == "function":
            file_ref = f"@{file_path}#L{element.start_line}-{element.end_line}"
            entry = f"- {file_ref} - {element.name} - {description}"
            
            key = (file_path, element.name, element.start_line)
            if key not in seen_functions:
                functions.append(entry)
                seen_functions.add(key)
    
    content = "MODULE_MAP:\n\n"
    
    content += "CLASSES:\n"
    if classes:
        content += "\n".join(classes) + "\n\n"
    else:
        content += "- No classes found\n\n"
    
    content += "METHODS:\n"
    if methods:
        content += "\n".join(methods) + "\n\n"
    else:
        content += "- No methods found\n\n"
    
    content += "FUNCTIONS:\n"
    if functions:
        content += "\n".join(functions) + "\n"
    else:
        content += "- No functions found\n"
    
    return content


def main():
    """Main function to generate MODULE_MAP.md for a given module path."""
    if len(sys.argv) != 2:
        print("Usage: python generate_module_map.py <module_path>")
        sys.exit(1)
    
    module_path = sys.argv[1]
    module_path_obj = Path(module_path)
    
    if not module_path_obj.exists():
        print(f"Error: Module path '{module_path}' does not exist")
        sys.exit(1)
    
    if not module_path_obj.is_dir():
        print(f"Error: Module path '{module_path}' is not a directory")
        sys.exit(1)
    
    content = generate_module_map(module_path)
    output_file = module_path_obj / "MODULE_MAP.md"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"MODULE_MAP.md generated successfully at: {output_file}")


if __name__ == "__main__":
    main()