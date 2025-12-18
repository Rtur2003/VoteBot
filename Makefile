.PHONY: help install install-dev format lint type-check test clean run validate-dev check-all

help:
	@echo "VOTRYX Development Commands"
	@echo ""
	@echo "  make install       - Install production dependencies"
	@echo "  make install-dev   - Install development dependencies"
	@echo "  make format        - Format code with black and isort"
	@echo "  make lint          - Run flake8 linter"
	@echo "  make type-check    - Run mypy type checker"
	@echo "  make test          - Run pytest tests"
	@echo "  make clean         - Remove build artifacts and cache"
	@echo "  make run           - Run the application"
	@echo "  make validate-dev  - Validate development environment"
	@echo "  make check-all     - Run all quality checks (format, lint, type-check, test)"

install:
	pip install -r requirements.txt

install-dev:
	pip install -e ".[dev]"

format:
	black Code_EXE/Votryx/
	isort Code_EXE/Votryx/

lint:
	flake8 Code_EXE/Votryx/

type-check:
	mypy Code_EXE/Votryx/

test:
	pytest

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/

run:
	python Code_EXE/Votryx/VotryxApp.py

validate-dev:
	@python scripts/validate_dev_setup.py

check-all: format lint type-check test
	@echo ""
	@echo "✓ All quality checks passed!"
