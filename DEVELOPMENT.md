# VOTRYX Development Guide

## Development Environment Setup

### Prerequisites
- Python 3.9 or higher
- Google Chrome browser
- Git

### Initial Setup

1. Clone the repository:
```bash
git clone https://github.com/Rtur2003/VOTRYX.git
cd VOTRYX
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

4. Install pre-commit hooks:
```bash
pre-commit install
```

## Development Workflow

### Code Formatting

Format code before committing:
```bash
make format
```

This runs:
- `black` for code formatting
- `isort` for import sorting

### Linting

Check code quality:
```bash
make lint
```

### Type Checking

Run type checker:
```bash
make type-check
```

### Testing

Run tests:
```bash
make test
```

### Running the Application

```bash
make run
```

## Code Standards

### Python Style
- Follow PEP 8 guidelines
- Line length: 100 characters
- Use type hints where appropriate
- Add docstrings to public functions

### Import Order
1. Standard library imports
2. Third-party imports
3. Local application imports

### Naming Conventions
- Classes: PascalCase
- Functions/methods: snake_case
- Constants: UPPER_SNAKE_CASE
- Private members: _leading_underscore

## Git Workflow

### Branch Naming
- Feature branches: `feature/description`
- Bug fixes: `fix/description`
- Refactoring: `refactor/description`
- Documentation: `docs/description`

### Commit Messages
Format:
```
<scope>: <precise technical justification>
```

Examples:
- `config: extract validation into dedicated module`
- `driver: add explicit guard for null chrome path`
- `ui: separate Turkish strings into i18n module`

### Pull Request Process
1. Create feature branch from main
2. Make atomic commits
3. Ensure all checks pass
4. Request review
5. Address feedback
6. Merge when approved

## Project Structure

```
VOTRYX/
├── Code_EXE/
│   └── Votryx/
│       ├── VotryxApp.py       # Main application
│       └── config.json         # Configuration
├── docs/                       # Documentation and assets
├── logs/                       # Runtime logs
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── pyproject.toml             # Python project configuration
├── Makefile                   # Development commands
└── README.md                  # Project overview
```

## Debugging

### Enable Verbose Logging
Set logging level to DEBUG in the application configuration.

### ChromeDriver Issues
- Check Chrome version: `chrome --version`
- Match ChromeDriver version
- Use Selenium Manager: set `use_selenium_manager = true`

## Common Tasks

### Add a New Dependency
1. Add to `requirements.txt` or `requirements-dev.txt`
2. Run `pip install -r requirements.txt`
3. Update `pyproject.toml` if needed

### Clean Build Artifacts
```bash
make clean
```

## Resources

- [Python Style Guide (PEP 8)](https://pep8.org/)
- [Selenium Documentation](https://selenium-python.readthedocs.io/)
- [Black Code Formatter](https://black.readthedocs.io/)
- [Type Hints (PEP 484)](https://peps.python.org/pep-0484/)
