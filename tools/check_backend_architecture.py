#!/home/axel/wsl_venv/bin/python
from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"

ALLOWED_BACKEND_ROOT_DIRS = {
    "__pycache__",
    "apps",
    "config",
    "locale",
    "scripts",
    "shared",
    "static",
    "templates",
    "tests",
}
ALLOWED_BACKEND_ROOT_FILES = {
    "README.md",
    "manage.py",
}


@dataclass(frozen=True)
class Violation:
    path: Path
    message: str


def module_name_for_file(path: Path) -> str:
    relative = path.relative_to(BACKEND_ROOT)
    parts = list(relative.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = Path(parts[-1]).stem
    return ".".join(parts)


def resolve_import(current_module: str, node: ast.ImportFrom) -> str | None:
    if node.level == 0:
        return node.module

    current_parts = current_module.split(".")
    if node.level > len(current_parts):
        return node.module

    base_parts = current_parts[: len(current_parts) - node.level]
    if node.module:
        base_parts.extend(node.module.split("."))
    return ".".join(base_parts)


def parse_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    current_module = module_name_for_file(path)
    imports: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            resolved = resolve_import(current_module, node)
            if resolved:
                imports.append(resolved)

    return imports


def layer_for_path(path: Path) -> tuple[str | None, str | None]:
    relative = path.relative_to(BACKEND_ROOT)
    parts = relative.parts
    if len(parts) >= 3 and parts[0] == "apps":
        return parts[1], parts[2]
    if len(parts) >= 1 and parts[0] == "shared":
        return None, "shared"
    return None, None


def imported_app_layer(module_name: str) -> tuple[str | None, str | None]:
    parts = module_name.split(".")
    if len(parts) >= 3 and parts[0] == "apps":
        return parts[1], parts[2]
    if len(parts) >= 4 and parts[0] == "backend" and parts[1] == "apps":
        return parts[2], parts[3]
    if len(parts) >= 1 and parts[0] == "shared":
        return None, "shared"
    if len(parts) >= 3 and parts[0] == "backend" and parts[1] == "shared":
        return None, "shared"
    return None, None


def collect_root_structure_violations() -> list[Violation]:
    violations: list[Violation] = []

    for child in BACKEND_ROOT.iterdir():
        if child.name.startswith("."):
            continue
        if child.is_dir() and child.name not in ALLOWED_BACKEND_ROOT_DIRS:
            violations.append(
                Violation(
                    child,
                    f"unexpected top-level backend directory '{child.name}' "
                    "(allowed: apps, config, shared, tests, scripts, templates, static, locale)",
                )
            )
        elif child.is_file() and child.name not in ALLOWED_BACKEND_ROOT_FILES:
            violations.append(
                Violation(
                    child,
                    f"unexpected top-level backend file '{child.name}' "
                    "(allowed: README.md, manage.py)",
                )
            )

    return violations


def collect_import_violations() -> list[Violation]:
    violations: list[Violation] = []
    python_files = sorted(
        path for path in BACKEND_ROOT.rglob("*.py") if "__pycache__" not in path.parts
    )

    for path in python_files:
        current_app, current_layer = layer_for_path(path)
        for imported in parse_imports(path):
            imported_app, imported_layer = imported_app_layer(imported)

            if imported == "frontend" or imported.startswith("frontend."):
                violations.append(
                    Violation(path, f"backend code must not import frontend modules: '{imported}'")
                )
                continue

            if current_layer == "domain" and imported_layer == "api":
                if imported_app == current_app:
                    violations.append(
                        Violation(
                            path,
                            f"domain layer must not import its own api layer: '{imported}'",
                        )
                    )
                elif imported_app is not None:
                    violations.append(
                        Violation(
                            path,
                            f"domain layer must not import another app's api layer: '{imported}'",
                        )
                    )

            if current_layer == "shared" and imported_layer == "api":
                violations.append(
                    Violation(path, f"shared backend code must not depend on api modules: '{imported}'")
                )

            if current_layer == "api" and imported_layer == "api" and imported_app not in {
                None,
                current_app,
            }:
                violations.append(
                    Violation(
                        path,
                        f"api layer must not import another app's api layer directly: '{imported}'",
                    )
                )

    return violations


def main() -> int:
    violations = [*collect_root_structure_violations(), *collect_import_violations()]

    if not violations:
        print("Backend architecture check passed.")
        return 0

    print("Backend architecture check failed:")
    for violation in violations:
        print(f"- {violation.path.relative_to(REPO_ROOT)}: {violation.message}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
