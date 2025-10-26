import ast
import itertools
import os
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import auto, StrEnum
from pathlib import Path
from pprint import pprint
from typing import Iterator


def iter_python_files(path: Path) -> Iterator[Path]:
    for item in path.rglob('*.py'):
        if item.is_file():
            yield item


def _path_to_python_module(path: Path):
    return '.'.join(path.with_suffix('').parts)


def _module_to_path(module: str) -> Path:
    module_parts = module.split('.')
    return Path('.').joinpath(*module_parts)


@dataclass(kw_only=True, repr=False)
class NameLoad:
    stmt: ast.Name
    is_local: bool

    def __repr__(self):
        return f'NameLoad({ast.dump(self.stmt)}, is_local={self.is_local})'


@dataclass(kw_only=True, repr=False)
class Node:
    stmt: ast.stmt
    file_path: Path
    ast_path: tuple[str, ...] = None
    name_loads: list[NameLoad] = field(default_factory=list)

    @property
    def module_path(self) -> str:
        return f'{_path_to_python_module(self.file_path)}.{".".join(self.ast_path)}'

    @property
    def package_path(self) -> str:
        if len(self.ast_path) > 1:
            return f'{_path_to_python_module(self.file_path)}.{".".join(self.ast_path[:-1])}'
        return f'{_path_to_python_module(self.file_path)}'

    @property
    def name(self):
        return self.ast_path[-1]

    @property
    def root(self):
        return self


@dataclass(kw_only=True, repr=False)
class ClassNode(Node):
    stmt: ast.ClassDef
    methods: list['FunctionNode'] = field(default_factory=list)
    inner_classes: list['ClassNode'] = field(default_factory=list)
    parent_class_node: 'ClassNode' = None

    def __repr__(self):
        return f"ClassNode({self.stmt.name})"

    @property
    def root(self):
        return self if self.parent_class_node is None else self.parent_class_node.root


@dataclass(kw_only=True, repr=False)
class FunctionNode(Node):
    stmt: ast.FunctionDef
    inner_functions: list['FunctionNode'] = field(default_factory=list)
    inner_classes: list['ClassNode'] = field(default_factory=list)
    parent_class_node: ClassNode = None

    @property
    def is_method(self) -> bool:
        return self.parent_class_node is not None

    def __repr__(self):
        return f"FunctionNode({self.stmt.name})"

    @property
    def root(self):
        return self if self.parent_class_node is None else self.parent_class_node.root


@dataclass(kw_only=True, repr=False)
class AsyncFunctionNode(FunctionNode):
    stmt: ast.AsyncFunctionDef


class DependencyType(StrEnum):
    unknown = auto()
    association = auto()
    aggregation = auto()
    composition = auto()
    inheritance = auto()


@dataclass
class ImportDependency:
    stmt: ast.Import | ast.ImportFrom


@dataclass(kw_only=True)
class Dependency:  # зависимость
    dependant: 'Node | Package'  # зависимый
    dependent: 'Node | Package'  # от чего зависят
    type: DependencyType = DependencyType.unknown
    rank: int = 1

    def is_same_dependency(self, other):
        return self.dependant is other.dependant and self.dependent is other.dependent and self.type is other.type


@dataclass(kw_only=True)
class DependencyGroup:
    dependencies: list['DependencyGroup | Dependency']


@dataclass(kw_only=True)
class Package:
    name: str
    nodes: list['Node'] = field(default_factory=list)
    subpackages: dict[str, 'Package'] = field(default_factory=dict)
    parent: 'Package' = None

    def add_subpackage(self, package_path: str, nodes: list['Node']) -> None:
        curr_package = self
        for path_part in package_path.split('.'):
            if path_part not in curr_package.subpackages:
                curr_package.subpackages[path_part] = Package(name=path_part, parent=curr_package)
            curr_package = curr_package.subpackages[path_part]
        curr_package.nodes.extend(nodes)

    @property
    def package_path(self) -> str:
        parts = []
        curr_package = self
        while curr_package.parent is not None:
            parts.append(curr_package.name)
            curr_package = curr_package.parent
        return '.'.join(parts)

    def get_node_from_package_path_soft(self, package_path: str) -> Node:
        parts = package_path.split('.')
        curr_package = self

        idx = 0
        for idx, part in enumerate(parts):
            if part in curr_package.subpackages:
                curr_package = curr_package.subpackages[part]
            else:
                break

        root_node_name, *remaining_parts = parts[idx:]
        curr_node = next(iter(n for n in curr_package.nodes if n.name == root_node_name))
        for part in remaining_parts:
            match curr_node:
                case ClassNode() as cn:
                    iterator = itertools.chain(cn.inner_classes, cn.methods)  # noqa
                case FunctionNode() as fn:
                    iterator = itertools.chain(fn.inner_classes, fn.inner_functions)  # noqa
                case _:
                    raise NotImplementedError
            for node in iterator:
                if node.name == part:
                    curr_node = node
                    break
            else:
                # soft behaviour, if inner not found - return parent
                return curr_node
        return curr_node


class CodeGraph:
    def __init__(self, nodes: list[Node], dependencies: list[Dependency]):
        self.package = self._group_nodes_to_packages(nodes)
        self.dependencies = dependencies
        self._group_method_dependencies_to_class_level()
        self._group_dependency_duplicates()

    @staticmethod
    def _group_nodes_to_packages(nodes: list[Node]) -> Package:
        nodes = sorted(nodes, key=lambda node: (node.package_path.count('.'), node.package_path))
        groups = itertools.groupby(nodes, lambda node: node.package_path)
        root_package = Package(name='root', nodes=[])

        for package_path, node_group in groups:
            root_package.add_subpackage(package_path, list(node_group))
        return root_package

    def _group_dependency_duplicates(self):
        deps = sorted(self.dependencies, key=lambda dep: (id(dep.dependant), id(dep.dependent), dep.type))
        groups = itertools.groupby(deps, lambda dep: (id(dep.dependant), id(dep.dependent), dep.type))

        for _, group in groups:
            head, *duplicates = list(group)
            head.rank += len(duplicates)
            for duplicate in duplicates:
                self.dependencies.remove(duplicate)

    def _group_method_dependencies_to_class_level(self):
        method_dependencies = [
            dep
            for dep in self.dependencies
            if isinstance(dep.dependant, FunctionNode) and dep.dependant.parent_class_node is not None
        ]
        # print(method_dependencies)
        groups = itertools.groupby(
            sorted(method_dependencies, key=lambda dep: dep.dependant.parent_class_node.module_path),
            lambda dep: (id(dep.dependant.parent_class_node), id(dep.dependant), dep.type),
        )
        for _, group in groups:
            g = list(group)

            rank = 0
            for item in g:
                rank += item.rank
                self.dependencies.remove(item)

            self.dependencies.append(
                Dependency(
                    dependant=g[0].dependant.parent_class_node, dependent=g[0].dependent, type=g[0].type, rank=rank
                )
            )

    def subgraph(
        self, package_path: str, dependant_depth: int = float('inf'), dependent_depth: int = float('inf')
    ) -> 'CodeGraph':
        """
        package_path like "core.serializer.Serializer" where Serializer is class.
        """
        node = self.package.get_node_from_package_path_soft(package_path)

        dependants_visited = []
        dependants_in_depth = []
        while dependant_depth > 0:
            dependant_depth -= 1
            if not dependants_in_depth:
                new_dependants = self.get_dependants([node])
            else:
                new_dependants = self.get_dependants(dependants_in_depth[-1])
            if not new_dependants:
                break

            new_dependants = [node for node in new_dependants if node not in dependants_visited]
            dependants_visited.extend(new_dependants)
            dependants_in_depth.append(new_dependants)

        dependents_visited = []
        dependents_in_depth = []
        while dependent_depth > 0:
            dependent_depth -= 1
            if not dependents_in_depth:
                new_dependents = self.get_dependents([node])
            else:
                new_dependents = self.get_dependents(dependents_in_depth[-1])
            if not new_dependents:
                break

            new_dependents = [node for node in new_dependents if node not in dependents_visited]
            dependents_visited.extend(new_dependents)
            dependents_in_depth.append(new_dependents)

        seen_ids = set()
        nodes = []

        for n in [node] + dependants_visited + dependents_visited:
            node_id = id(n)
            if node_id not in seen_ids:
                seen_ids.add(node_id)
                nodes.append(n)

        # pprint(nodes)

        dependencies = [dep for dep in self.dependencies if (dep.dependant in nodes) or (dep.dependant in nodes)]
        return CodeGraph(nodes, dependencies)

    def get_dependants(self, nodes: list[Node]) -> list[Node]:
        """dependants - things that depend ON this object."""
        return [dep.dependant for dep in self.dependencies if dep.dependent in nodes]

    def get_dependents(self, nodes: list[Node]) -> list[Node]:
        """dependents - things that this object depends ON."""
        return [dep.dependent for dep in self.dependencies if dep.dependant in nodes]


class ASTVisitor(ast.NodeVisitor):
    def __init__(self, file_path: Path = None):
        self._file_path = file_path
        self.nodes: list[Node] = []
        self._import_dependencies: dict[Path, list[ImportDependency]] = defaultdict(list)
        self.dependencies: list[Dependency] = []
        self._ast_nodes_stack = []

    def set_file_path(self, file_path: Path):
        self._file_path = file_path

    @property
    def import_dependencies(self) -> list[ImportDependency]:
        return self._import_dependencies[self._file_path]

    def visit_Import(self, node: ast.Import):
        self._import_dependencies[self._file_path].append(ImportDependency(node))

    def visit_ImportFrom(self, node: ast.ImportFrom):
        self._import_dependencies[self._file_path].append(ImportDependency(node))

    def visit_ClassDef(self, node: ast.ClassDef):
        parsing_node = ClassNode(**self._collect_stmt_meta(node))
        self._process_parsing_node(parsing_node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        parsing_node = AsyncFunctionNode(**self._collect_stmt_meta(node))
        self._process_parsing_node(parsing_node)

    def visit_FunctionDef(self, node: ast.AsyncFunctionDef):
        parsing_node = FunctionNode(**self._collect_stmt_meta(node))
        self._process_parsing_node(parsing_node)

    def _process_parsing_node(self, parsing_node: AsyncFunctionNode | FunctionNode | ClassNode):
        last_node = self.get_last_node()
        with self.ast_path(parsing_node):
            if not last_node:
                self.nodes.append(parsing_node)
                self.generic_visit(parsing_node.stmt)
                return

            match (last_node, parsing_node):
                case (FunctionNode() as fn, ClassNode() as cn):
                    fn.inner_classes.append(cn)
                case (FunctionNode() as fn1, FunctionNode() as fn2):
                    fn1.inner_functions.append(fn2)
                case (ClassNode() as cn, FunctionNode() as fn):
                    fn.parent_class_node = cn
                    cn.methods.append(fn)
                case (ClassNode() as cn1, ClassNode() as cn2):
                    cn2.parent_class_node = cn1
                    cn1.inner_classes.append(cn2)
                case _:
                    self.nodes.append(parsing_node)

            self.generic_visit(parsing_node.stmt)

    def get_ast_path(self) -> tuple[str]:
        return tuple(node.stmt.name for node in self._ast_nodes_stack)

    @contextmanager
    def ast_path(self, node):
        self._ast_nodes_stack.append(node)
        node.ast_path = self.get_ast_path()
        yield
        self._ast_nodes_stack.pop()

    @property
    def current_node(self) -> Node:
        return self._ast_nodes_stack[-1]

    def get_last_node(self) -> Node | None:
        return self._ast_nodes_stack[-1] if self._ast_nodes_stack else None

    def _collect_stmt_meta(self, stmt: ast.stmt):
        return {'stmt': stmt, 'file_path': self._file_path}

    def visit_path(self, path: Path):
        for python_file_path in iter_python_files(path):
            self.set_file_path(python_file_path)
            content = python_file_path.read_text()
            tree = ast.parse(content)
            # print(ast.dump(tree))
            self.visit(tree)

    def visit_Name(self, node: ast.Name):
        # print(self._file_path)
        # print(ast.dump(node))
        # print([ast.dump(x.stmt) for x in self.import_dependencies if isinstance(x.stmt, ast.ImportFrom)])
        # print()
        match node:
            case ast.Name(id=name_id, ctx=ast.Load()):
                for import_dependency in self.import_dependencies:
                    match import_dependency:
                        case ImportDependency(stmt=ast.Import(names=names) | ast.ImportFrom(names=names)):
                            for alias in names:
                                if name_id == (alias.asname or alias.name):
                                    name_load = NameLoad(stmt=node, is_local=False)
                                    # print(name_load)
                                    if self._ast_nodes_stack:
                                        self.current_node.name_loads.append(name_load)
                                    return
                        case _:
                            raise TypeError(f'Unexpected type {type(node)}')
                else:
                    name_load = NameLoad(stmt=node, is_local=True)
                    # print(name_load)
                    if self._ast_nodes_stack:
                        self.current_node.name_loads.append(name_load)

    def get_code_graph(self) -> CodeGraph:
        dependencies = []
        for node in self.nodes:
            for name_load in node.name_loads:
                self.resolve_dependency(node, name_load, dependencies)
            match node:
                case ClassNode():
                    for inner_class in node.inner_classes:
                        for name_load in inner_class.name_loads:
                            self.resolve_dependency(inner_class, name_load, dependencies)
                    for method in node.methods:
                        for name_load in method.name_loads:
                            self.resolve_dependency(method, name_load, dependencies)
                case FunctionNode():
                    for inner_class in node.inner_classes:
                        for name_load in inner_class.name_loads:
                            self.resolve_dependency(inner_class, name_load, dependencies)
                    for inner_func in node.inner_functions:
                        for name_load in inner_func.name_loads:
                            self.resolve_dependency(inner_func, name_load, dependencies)
        return CodeGraph(self.nodes.copy(), dependencies)

    def resolve_dependency(self, node: Node, name_load: NameLoad, dependencies: list[Dependency]):
        if name_load.is_local:
            dependent_node = self.resolve_node(node.file_path, name_load.stmt.id)
            if dependent_node is None:
                return
        else:
            import_dependency_file_path = self.resolve_import_dependency_path(name_load.stmt.id, node)
            if import_dependency_file_path is None:
                # print(node.stmt.name, name_load.stmt.id)
                # probably third-party library
                return

            dependent_node = self.resolve_node(import_dependency_file_path, name_load.stmt.id)

            if dependent_node is None:
                # raise ValueError(f'Could not resolve node with name {name_load} and path {import_dependency_file_path}')
                return

        dependency_type = self.resolve_dependency_type(name_load, node)
        dependency = Dependency(dependant=node, dependent=dependent_node, type=dependency_type)
        dependencies.append(dependency)

    @staticmethod
    def resolve_dependency_type(name_load: NameLoad, node: Node) -> DependencyType:
        dependency_type = DependencyType.unknown
        match node:
            case ClassNode(stmt=ast.ClassDef(bases=bases)):
                for base in bases:
                    base: ast.Subscript | ast.Name
                    if isinstance(base, ast.Subscript):
                        assert isinstance(base.value, ast.Name)
                        base = base.value
                    # print('base ', ast.dump(base))
                    if name_load.stmt.id == base.id:
                        dependency_type = DependencyType.inheritance
        return dependency_type

    def resolve_import_dependency_path(self, name_id: str, node: Node) -> Path | None:
        for import_dependency in self._import_dependencies[node.file_path]:
            match import_dependency:
                case ImportDependency(stmt=ast.Import(names=names)):
                    for alias in names:
                        if name_id == (alias.asname or alias.name):
                            return None
                case ImportDependency(ast.ImportFrom(names=names, module=module)):
                    for alias in names:
                        if name_id == (alias.asname or alias.name):
                            res = _module_to_path(module).with_suffix('.py')
                            return res
        return None

    def resolve_node(self, path: Path, name: str):
        for node in self.nodes:
            # print(path, node.file_path, node.file_path == path)
            if node.file_path == path and node.stmt.name == name:
                return node
        return None


def main():
    os.chdir(Path('../backend'))
    start_directory = Path('.')
    visitor = ASTVisitor()
    # visitor.visit_path(start_directory / 'tst_module')
    visitor.visit_path(start_directory)
    code_graph = visitor.get_code_graph()
    pprint(code_graph.package)
    pprint(code_graph.dependencies, width=200)


if __name__ == '__main__':
    main()
