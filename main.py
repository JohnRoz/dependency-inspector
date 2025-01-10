import importlib
import pathlib
import pkgutil
import sys
from typing import Iterator


def import_all_modules_under_pkg(root_package: str) -> None:
    """Recursively import all modules under `root_package` so that
    the `__subclasses__()` calls see all classes."""
    package = importlib.import_module(root_package)
    for finder, name, is_pkg in pkgutil.walk_packages(
        package.__path__, package.__name__ + "."
    ):
        importlib.import_module(name)


def get_all_python_files_in_dir(root_dir: str) -> list[pathlib.Path]:
    root = pathlib.Path(root_dir)
    return [
        path for path in root.rglob("*.py") if not str(path).endswith("__init__.py")
    ]


def get_all_subclasses_of(cls: type) -> Iterator[type]:
    """
    Recursively find all subclasses of `cls` (including subclasses of subclasses).
    """
    direct_subs = cls.__subclasses__()
    for d in direct_subs:
        yield d
        yield from get_all_subclasses_of(d)


def build_classname_map(base_cls: type) -> dict[str, type]:
    """
    Returns a dict where:
      key = cls.__name__
      val = cls
    for all subclasses of base_cls (including base_cls itself if needed).
    """
    return {subclass.__name__: subclass for subclass in get_all_subclasses_of(base_cls)}


import ast
from collections import defaultdict
from contextlib import contextmanager


class DependencyAnalyzer(ast.NodeVisitor):
    known_subclasses: set[str]
    current_class: str | None
    discovered_classes: defaultdict[str, set[str]]

    def __init__(self, known_subclasses: set[str]):
        super().__init__()
        self.known_subclasses = known_subclasses
        self.current_class = None
        self.discovered_classes = defaultdict(set)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if node.name not in self.known_subclasses:
            self.generic_visit(node)
        else:
            # TODO: Switch to context manager
            # Enter
            old_class = self.current_class
            self.current_class = node.name

            # Visit the internals of the class
            self.generic_visit(node)

            # Exit
            self.current_class = old_class

    def visit_Call(self, node: ast.Call) -> None:
        """
        Called whenever we see a function or constructor call: e.g., SomeConfig(...).
        We want to see if that 'SomeConfig' is in known_configs.
        """
        if self.current_class is not None:
            self.__handle_recognized_class(node)

        self.generic_visit(node)

    def __handle_recognized_class(self, node: ast.Call) -> None:
        if self.current_class is None:
            raise ValueError()

        called_name: str

        if isinstance(node.func, ast.Name):
            called_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            called_name = node.func.attr
        else:
            return

        if called_name in self.known_subclasses:
            self.discovered_classes[self.current_class].add(called_name)

    # @contextmanager
    # def __save_current_class_context(self) -> None:
    #     pass

    @classmethod
    def analyze_dependencies_in_file(
        cls, filename: pathlib.Path, known_configs: set[str]
    ) -> dict[str, set[str]]:
        """
        Parse the given Python file, return discovered references in a dict.
        """
        with open(filename) as f:
            source = f.read()

        tree = ast.parse(source, filename=filename)
        analyzer = cls(known_configs)
        analyzer.visit(tree)
        return analyzer.discovered_classes

    @classmethod
    def analyze_dependencies(
        cls, root_pkg_to_scan: str, baseclass: type
    ) -> dict[str, set[str]]:
        # To make sure all the available subclasses are loaded
        # TODO: Figure out why pkg1 works but root_pkg_to_scan doesn't
        import_all_modules_under_pkg("pkg1")

        cls_map = build_classname_map(baseclass)
        subclasses_names = set(cls_map.keys())

        py_files = get_all_python_files_in_dir(root_pkg_to_scan)

        overall = defaultdict(set)
        for f in py_files:
            discovered = DependencyAnalyzer.analyze_dependencies_in_file(
                f, subclasses_names
            )
            for cls_name, cls_dependencies_names in discovered.items():
                overall[cls_name].update(cls_dependencies_names)
        return overall


def main():
    root_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "pkg1")

    discovered = DependencyAnalyzer.analyze_dependencies(
        root_pkg_to_scan=root_dir, baseclass=BaseConfig
    )
    pass


# Start planning test

import os

import pytest

from pkg1.base_config import BaseConfig

if __name__ == "__main__":
    main()


def test_dependencies_are_declared():
    # 1. Import everything so that subclasses are registered
    import_all_modules_under_pkg("pkg1")  # or adapt if needed

    # 2. Build a map from class name -> class object, and also a set of known config names
    cls_map = build_classname_map(BaseConfig)
    known_config_names = set(cls_map.keys())

    # 3. Find all .py files in your project (adjust root_dir if needed)
    root_dir = os.path.abspath(os.path.dirname(__file__))
    py_files = get_all_python_files_in_dir(root_dir)

    # 4. Collect all discovered references
    discovered = collect_all_discovered_dependencies(py_files, known_config_names)
    # discovered is e.g. { "ConfigA": set(["ConfigB", "ConfigC"]), ... }

    # 5. Compare discovered references to declared references
    mismatches = []
    for class_name, dep_set in discovered.items():
        config_cls = cls_map[class_name]
        # The user-declared dependencies (list of classes)
        declared_cls_list = config_cls.dependencies()
        declared_name_set = set(cls.__name__ for cls in declared_cls_list)

        # We might want to filter out the ones that have is_none_ok == True
        # from discovered references, or from declared references, or both.
        # For now, let's assume everything that is discovered MUST be in declared references:
        missing_in_declared = dep_set - declared_name_set
        # Also check if there are declared references we never discovered
        # (maybe that indicates an unneeded declared dependency).
        extra_in_declared = declared_name_set - dep_set

        if missing_in_declared or extra_in_declared:
            mismatches.append(
                f"{class_name}:\n"
                f"  discovered not in declared: {missing_in_declared}\n"
                f"  declared but not discovered: {extra_in_declared}\n"
            )

    # 6. Fail the test if there are any mismatches
    if mismatches:
        mismatch_msg = "\n".join(mismatches)
        pytest.fail(
            f"Some config classes have mismatched dependencies:\n{mismatch_msg}"
        )
