# Contributing to VOTRYX

Thank you for your interest in contributing to VOTRYX. This document provides guidelines for contributing to this project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and collaborative environment.

## How to Contribute

### Reporting Issues

- Search existing issues before creating a new one
- Use a clear, descriptive title
- Include steps to reproduce the issue
- Provide system information (OS, Python version, Chrome version)
- Include error messages and logs if applicable

### Pull Requests

#### Before Submitting

1. Fork the repository
2. Create a feature branch from `main`
3. Follow the branching strategy outlined below
4. Make atomic commits with clear messages
5. Ensure all checks pass

#### Branching Strategy

Branch names must follow this pattern:
- `feature/description` - New features
- `fix/description` - Bug fixes
- `refactor/description` - Code refactoring
- `docs/description` - Documentation updates
- `tooling/description` - Development tools

Example: `feature/add-vote-scheduling`

#### Commit Message Format

```
<scope>: <precise technical justification>
```

**Scope examples:**
- `config` - Configuration changes
- `validation` - Input validation
- `driver` - Selenium driver management
- `ui` - User interface
- `refactor` - Code refactoring
- `docs` - Documentation
- `tests` - Test additions/changes

**Good commit messages:**
```
config: extract validation into dedicated module
driver: add explicit guard for null chrome path
ui: separate Turkish strings into i18n module
validation: add URL scheme check before processing
```

**Bad commit messages:**
```
misc changes
minor fixes
cleanup
update
```

#### Commit Guidelines

**Allowed per commit:**
- One function change
- One validation guard
- One refactor step
- One bug fix

**Forbidden per commit:**
- Multiple unrelated changes
- Refactor + behavior change together
- Cleanup + feature together
- Generic "misc" or "minor fixes" messages

#### Pull Request Process

1. Update documentation if needed
2. Add tests for new functionality
3. Ensure all tests pass
4. Run linters and formatters
5. Request review from maintainers
6. Address review feedback
7. Wait for approval before merging

### Code Standards

#### Python Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Line length: 100 characters maximum
- Add docstrings to public functions
- Use descriptive variable names

#### Testing

- Write tests for new functionality
- Maintain or improve code coverage
- Tests must pass before merging

#### Code Quality Checks

Run before submitting:

```bash
make format    # Format code
make lint      # Run linter
make type-check # Run type checker
make test      # Run tests
```

### Development Environment

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed setup instructions.

Quick start:
```bash
# Setup
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

# Run checks
make format
make lint
make test
```

## Language Priority

**Python is the primary language.**

You must:
- Attempt a Python-based solution first
- Prefer Python for logic, tooling, and automation
- Explicitly justify any non-Python implementation

Use another language only if:
- Python is technically insufficient
- Performance constraints are proven
- System-level bindings are unavoidable

## Architecture Principles

### Separation of Concerns

- One module = one responsibility
- Clear boundaries between components
- No mixed concerns

### Code Organization

- Configuration in dedicated module
- Validation in separate layer
- UI components modular
- Business logic isolated

### Maintainability

- Optimize for reviewers, not authors
- Assume 6-12 months forward maintenance
- Prefer clarity over cleverness
- Document complex logic

## Review Process

### What Reviewers Look For

- Clear scope and purpose
- Atomic commits
- Proper testing
- Documentation updates
- Code quality standards met
- No mixed concerns
- Safety and robustness

### Response Time

- Maintainers aim to review within 48 hours
- Complex changes may take longer
- Be patient and respectful

## Questions?

- Check [DEVELOPMENT.md](DEVELOPMENT.md) for development guide
- Check [README.md](README.md) for project overview
- Open an issue for clarification

## License

By contributing, you agree that your contributions will be licensed under the project's license.

---

Thank you for helping make VOTRYX better!
