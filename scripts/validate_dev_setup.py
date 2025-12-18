#!/usr/bin/env python3
"""Development environment validation script.

Validates that development environment is properly configured
with all required tools and dependencies.
"""

import subprocess
import sys
from pathlib import Path


def check_command(cmd: str, name: str) -> bool:
    """Check if a command is available."""
    try:
        subprocess.run(
            [cmd, "--version"],
            capture_output=True,
            check=True,
            timeout=5,
        )
        print(f"✓ {name} is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        print(f"✗ {name} is not installed or not in PATH")
        return False


def check_python_version() -> bool:
    """Validate Python version is 3.9+."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    print(f"✗ Python 3.9+ required, found {version.major}.{version.minor}.{version.micro}")
    return False


def check_file_exists(path: Path, name: str) -> bool:
    """Check if required file exists."""
    if path.exists():
        print(f"✓ {name} exists")
        return True
    print(f"✗ {name} not found at {path}")
    return False


def check_pre_commit_installed() -> bool:
    """Check if pre-commit hooks are installed."""
    git_dir = Path(".git")
    if not git_dir.exists():
        print("⚠ Not in a git repository")
        return False

    hook_file = git_dir / "hooks" / "pre-commit"
    if hook_file.exists():
        print("✓ Pre-commit hooks are installed")
        return True
    print("✗ Pre-commit hooks not installed - run: pre-commit install")
    return False


def main() -> int:
    """Run all validation checks."""
    print("Validating VOTRYX development environment...\n")

    checks = []

    # Python version
    checks.append(check_python_version())

    # Required commands
    checks.append(check_command("black", "Black formatter"))
    checks.append(check_command("flake8", "Flake8 linter"))
    checks.append(check_command("isort", "isort"))
    checks.append(check_command("mypy", "mypy type checker"))
    checks.append(check_command("pytest", "pytest"))
    checks.append(check_command("pre-commit", "pre-commit"))

    # Required files
    base = Path(".")
    checks.append(check_file_exists(base / "pyproject.toml", "pyproject.toml"))
    checks.append(check_file_exists(base / "requirements.txt", "requirements.txt"))
    checks.append(check_file_exists(base / "requirements-dev.txt", "requirements-dev.txt"))
    checks.append(check_file_exists(base / ".pre-commit-config.yaml", ".pre-commit-config.yaml"))
    checks.append(check_file_exists(base / "Makefile", "Makefile"))

    # Pre-commit hooks
    checks.append(check_pre_commit_installed())

    print("\n" + "=" * 60)
    passed = sum(checks)
    total = len(checks)

    if passed == total:
        print(f"✓ All checks passed ({passed}/{total})")
        print("\nDevelopment environment is properly configured!")
        return 0
    else:
        print(f"✗ Some checks failed ({passed}/{total})")
        print("\nPlease install missing dependencies:")
        print("  pip install -r requirements-dev.txt")
        print("  pre-commit install")
        return 1


if __name__ == "__main__":
    sys.exit(main())
