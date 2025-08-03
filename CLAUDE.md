
# 🔄 Code Exploration Strategy

When exploring modules or understanding code structure:

1. **Use MODULE_MAP as navigation** - The MODULE_MAP provides structured overview with line references
2. **Targeted file reading** - Use MODULE_MAP line references (`@file.py#L26-42`) with Read tool's.
    - Line reference format: L{start_line}-{end_line} or L{start_line}-{header_end_line}-{end_line}
    - Line format: line reference - class/method/function name - description
    - This reads only the specific function/method instead of the entire file
3. **Efficient exploration** - Avoid directory listing when MODULE_MAP is available
4. **Minimize context usage** - Read only necessary code sections to reduce token consumption

@docs/docstring_standart.md
@app/MODULE_MAP.md
