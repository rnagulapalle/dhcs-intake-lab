"""
Enforcement test: No direct provider imports outside platform/.

Phase 1 Hardened requirement:
- NO ChatOpenAI imports allowed anywhere except platform/
- ALL LLM access must go through ModelGateway
- Rollback changes gateway behavior, not agent code
"""
import ast
import os
from pathlib import Path
from typing import List, Tuple, Set


# Only platform/ is allowed to import ChatOpenAI
ALLOWED_DIRECTORIES = {
    "platform",
}


def find_direct_provider_imports(file_path: str) -> List[Tuple[int, str]]:
    """
    Find ANY ChatOpenAI imports in a file (not inside TYPE_CHECKING blocks).

    Returns:
        List of (line_number, import_statement) tuples for violations
    """
    with open(file_path, "r") as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    violations = []

    # Track TYPE_CHECKING blocks
    type_checking_lineno_ranges = []

    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            test = node.test
            if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
                start = node.lineno
                end = node.end_lineno or start
                type_checking_lineno_ranges.append((start, end))

    def is_in_type_checking(lineno: int) -> bool:
        for start, end in type_checking_lineno_ranges:
            if start <= lineno <= end:
                return True
        return False

    # Check all imports
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and "langchain_openai" in node.module:
                for alias in node.names:
                    if alias.name == "ChatOpenAI" or alias.name == "*":
                        if not is_in_type_checking(node.lineno):
                            violations.append((
                                node.lineno,
                                f"from {node.module} import {alias.name}"
                            ))

        if isinstance(node, ast.Import):
            for alias in node.names:
                if "langchain_openai" in alias.name:
                    if not is_in_type_checking(node.lineno):
                        violations.append((
                            node.lineno,
                            f"import {alias.name}"
                        ))

    return violations


def test_no_provider_imports_outside_platform():
    """
    Enforcement: NO ChatOpenAI imports allowed outside platform/.

    Phase 1 Hardened requirement:
    - All provider-specific imports must be in platform/
    - Agents/orchestrators must use ModelGateway exclusively
    - This test fails if ANY ChatOpenAI import exists outside platform/
    """
    project_root = Path(__file__).parent.parent.parent

    # Directories to check (everything except platform/)
    check_dirs = [
        project_root / "agents",
        project_root / "api",
    ]

    all_violations = []

    for check_dir in check_dirs:
        if not check_dir.exists():
            continue

        for py_file in check_dir.rglob("*.py"):
            # Skip __pycache__
            if "__pycache__" in str(py_file):
                continue

            violations = find_direct_provider_imports(str(py_file))

            if violations:
                rel_path = py_file.relative_to(project_root)
                all_violations.append((str(rel_path), violations))

    if all_violations:
        error_msg = "Provider imports found outside platform/ (Phase 1 Hardened violation):\n\n"
        for filepath, violations in all_violations:
            for line_no, import_stmt in violations:
                error_msg += f"  {filepath}:{line_no}: {import_stmt}\n"

        error_msg += "\n"
        error_msg += "ALL LLM access must go through ModelGateway.\n"
        error_msg += "Provider imports are ONLY allowed in platform/.\n"
        error_msg += "Use: from platform.model_gateway import get_default_gateway"

        raise AssertionError(error_msg)


def test_no_direct_chatgpt_in_agents():
    """
    Enforcement: No ChatOpenAI imports in agents/core/*.py

    Phase 1 requirement: All agents must use centralized ModelGateway.
    """
    agents_dir = Path(__file__).parent.parent.parent / "agents" / "core"

    all_violations = []

    for py_file in agents_dir.glob("*.py"):
        if py_file.name.startswith("__"):
            continue

        violations = find_direct_provider_imports(str(py_file))

        if violations:
            all_violations.append((py_file.name, violations))

    if all_violations:
        error_msg = "ChatOpenAI imports found in agents (Phase 1 violation):\n\n"
        for filename, violations in all_violations:
            for line_no, import_stmt in violations:
                error_msg += f"  {filename}:{line_no}: {import_stmt}\n"

        error_msg += "\nAgents must use ModelGateway, not direct ChatOpenAI."

        raise AssertionError(error_msg)


def test_no_direct_chatgpt_in_orchestrators():
    """
    Enforcement: No ChatOpenAI imports in orchestrators.
    """
    agents_dir = Path(__file__).parent.parent.parent / "agents" / "core"

    orchestrator_files = [
        "orchestrator.py",
        "curation_orchestrator.py"
    ]

    all_violations = []

    for filename in orchestrator_files:
        file_path = agents_dir / filename
        if not file_path.exists():
            continue

        violations = find_direct_provider_imports(str(file_path))

        if violations:
            all_violations.append((filename, violations))

    if all_violations:
        error_msg = "ChatOpenAI imports found in orchestrators (Phase 1 violation):\n\n"
        for filename, violations in all_violations:
            for line_no, import_stmt in violations:
                error_msg += f"  {filename}:{line_no}: {import_stmt}\n"

        error_msg += "\nOrchestrators must use ModelGateway."

        raise AssertionError(error_msg)


def test_centralized_gateway_default_enabled():
    """
    Enforcement: BHT_USE_CENTRALIZED_GATEWAY defaults to true.
    """
    import os

    original = os.environ.pop("BHT_USE_CENTRALIZED_GATEWAY", None)

    try:
        from platform.config import PlatformConfig

        config = PlatformConfig()
        assert config.use_centralized_gateway is True, (
            "BHT_USE_CENTRALIZED_GATEWAY should default to True. "
            f"Got: {config.use_centralized_gateway}"
        )

    finally:
        if original is not None:
            os.environ["BHT_USE_CENTRALIZED_GATEWAY"] = original


def test_base_agent_always_uses_gateway():
    """
    Verify BaseAgent ALWAYS uses ModelGateway (no conditional logic).
    """
    import os
    from unittest.mock import patch

    # Even with centralized gateway disabled, agent should still use gateway
    # (the gateway just operates in passthrough mode)
    os.environ["BHT_USE_CENTRALIZED_GATEWAY"] = "false"

    try:
        from platform import config as platform_config
        from platform import model_gateway
        platform_config._platform_config = None
        model_gateway.reset_default_gateway()

        from agents.core.base_agent import BaseAgent

        agent = BaseAgent(
            name="TestAgent",
            role="test",
            goal="test goal"
        )

        # Agent should ALWAYS have a gateway, even when centralized is disabled
        assert agent.has_gateway(), (
            "BaseAgent must ALWAYS use ModelGateway (Phase 1 Hardened)"
        )

    finally:
        os.environ.pop("BHT_USE_CENTRALIZED_GATEWAY", None)


def test_platform_is_only_provider_location():
    """
    Verify that platform/model_gateway.py is the ONLY file with ChatOpenAI import.
    """
    project_root = Path(__file__).parent.parent.parent

    # Find all Python files
    all_violations = []

    for py_file in project_root.rglob("*.py"):
        # Skip __pycache__, tests, and venv
        path_str = str(py_file)
        if any(skip in path_str for skip in ["__pycache__", "venv", ".venv", "site-packages"]):
            continue

        # Get relative path
        try:
            rel_path = py_file.relative_to(project_root)
        except ValueError:
            continue

        # Check if in allowed directory
        parts = rel_path.parts
        if len(parts) > 0 and parts[0] in ALLOWED_DIRECTORIES:
            continue  # OK - platform/ can have provider imports

        # Check for violations
        violations = find_direct_provider_imports(str(py_file))

        if violations:
            all_violations.append((str(rel_path), violations))

    if all_violations:
        error_msg = "Provider imports found outside platform/ directory:\n\n"
        for filepath, violations in all_violations:
            for line_no, import_stmt in violations:
                error_msg += f"  {filepath}:{line_no}: {import_stmt}\n"

        error_msg += "\nOnly platform/ may import provider-specific modules."

        raise AssertionError(error_msg)


if __name__ == "__main__":
    print("Running enforcement tests (Phase 1 Hardened)...")

    tests = [
        ("No provider imports outside platform/", test_no_provider_imports_outside_platform),
        ("No ChatOpenAI in agents/", test_no_direct_chatgpt_in_agents),
        ("No ChatOpenAI in orchestrators", test_no_direct_chatgpt_in_orchestrators),
        ("Centralized gateway default enabled", test_centralized_gateway_default_enabled),
        ("BaseAgent always uses gateway", test_base_agent_always_uses_gateway),
        ("Platform is only provider location", test_platform_is_only_provider_location),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        print(f"\n{name}...")
        try:
            test_func()
            print(f"   PASSED")
            passed += 1
        except AssertionError as e:
            print(f"   FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"   ERROR: {e}")
            failed += 1

    print(f"\n{'=' * 50}")
    print(f"Results: {passed} passed, {failed} failed")
