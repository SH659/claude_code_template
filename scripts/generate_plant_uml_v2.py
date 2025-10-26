import os
import textwrap
from pathlib import Path

from scripts.parse_graph_v2 import ASTVisitor, DependencyType, Package, Node, ClassNode, FunctionNode, Dependency

CHARS_PER_INDENTATION = 4
INDENTATION = ' ' * CHARS_PER_INDENTATION

# Mapping for PlantUML dependency arrows
DEPENDENCY_ARROWS = {
    DependencyType.inheritance: '--|>',
    DependencyType.association: '..>',
    DependencyType.aggregation: 'o--',
    DependencyType.composition: '*--',
    DependencyType.unknown: '..>',
}


# package_template = 'package "{module_path}" as {package_name}'
# plant_uml_template = '@startuml\n{content}\n@enduml'
# print(package_template.format_map({'module_path': 'module_path', 'package_name': 'package_name'}))


def present_class_name(cls: ClassNode) -> str:
    return cls.module_path


def present_class(cls: ClassNode) -> str:
    class_str_parts = [f'class {present_class_name(cls)}']

    methods_str_parts = []
    for method in cls.methods:
        # methods_str_parts.append(f'"{method.name}" as {method.package_path}')
        methods_str_parts.append(f'{method.name}()')
    if methods_str_parts:
        methods_content = textwrap.indent('\n'.join(methods_str_parts), INDENTATION)
        class_str_parts.extend([' {\n', methods_content, ' \n}'])

    return ''.join(class_str_parts)


def present_function_dependency_name(func: FunctionNode) -> str:
    if func.is_method:
        return f'"{func.package_path}::{func.name}"'
    return f'"{func.package_path}.{func.name}"'


def present_function(func: FunctionNode) -> str:
    return f'object "{func.name}" as {func.module_path}'  # use "as" to avoid plantuml object already exist error


def present_node(node: Node) -> str:
    match node:
        case ClassNode():
            return present_class(node)
        case FunctionNode():
            return present_function(node)
        case _:
            raise NotImplementedError


def present_node_name(node: Node) -> str:
    match node:
        case ClassNode():
            return present_class_name(node)
        case FunctionNode():
            return present_function_dependency_name(node)
        case _:
            raise NotImplementedError


def package_to_str(package: Package, indent: int = 0) -> str:
    # package_str_parts = [f'package "{package.name}" as {package.package_path or 'root'}']
    package_str_parts = [f'package "{package.name}"']

    package_content_lst = []
    for node in package.nodes:
        package_content_lst.append(present_node(node))
    for subpackage in package.subpackages.values():
        package_content_lst.append(package_to_str(subpackage))
    if package_content_lst:
        package_content = '\n'.join(package_content_lst)
        indent_times = indent + 1
        package_content = textwrap.indent(package_content, INDENTATION * indent_times)
        package_str_parts.extend([' {\n', package_content, '\n}'])

    return ''.join(package_str_parts)


def present_dependency(dep: Dependency) -> str:
    if dep.type is DependencyType.inheritance:
        return '--[norank]|>'
    return '--[norank]>'


def dependency_to_str(dependency: Dependency) -> str:
    return (
        f'{present_node_name(dependency.dependant)} '
        f'{present_dependency(dependency)} '
        f'{present_node_name(dependency.dependent)}'
    )


plant_uml_header = [
    '@startuml',
    '!pragma layout smetana',
    'skinparam nodesep 0',
    'skinparam ranksep 10',
    'skinparam padding 0',
    'hide empty members',
    'skinparam linetype ortho',
    'skinparam linetype polyline',
    'skinparam groupInheritance 2',
    'left to right direction',
]


def main():
    os.chdir(Path('../app'))
    start_directory = Path('.')
    visitor = ASTVisitor()
    visitor.visit_path(start_directory)
    # visitor.visit_path(start_directory)
    code_graph = visitor.get_code_graph()
    code_graph = code_graph.subgraph(
        [
            'core.models.Model'
        ],
        dependant_depth=3
    )

    # pprint(code_graph.package)
    # pprint(code_graph.dependencies, width=200)

    res_parts = plant_uml_header.copy()

    for package in code_graph.package.subpackages.values():
        package_str = package_to_str(package)
        res_parts.append(package_str)

    for dependency in code_graph.dependencies:
        dependency_str = dependency_to_str(dependency)
        res_parts.append(dependency_str)

    res_parts.append('@enduml')

    with open('app.puml', 'w') as f:
        f.write('\n'.join(res_parts))


if __name__ == '__main__':
    main()
