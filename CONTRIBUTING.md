# Contributing to vCon Server Load Test Application

Thank you for your interest in contributing to the vCon Server Load Test Application! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Code Style](#code-style)
- [Documentation](#documentation)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

This project follows a code of conduct that ensures a welcoming environment for all contributors. Please be respectful and constructive in all interactions.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/vcon-load-test.git
   cd vcon-load-test
   ```
3. **Set up the development environment** (see [Development Setup](#development-setup))

## Development Setup

### Prerequisites

- Python 3.12 or higher
- uv package manager
- Git

### Setup Steps

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Install development dependencies**:
   ```bash
   uv sync --extra dev
   ```

3. **Set up environment configuration**:
   ```bash
   cp .env.example .env
   # Edit .env with your test configuration
   ```

4. **Provide sample vCon files**:
   ```bash
   # Create a directory for your sample vCon files
   mkdir sample_data
   # Add your own .vcon files to this directory
   ```

5. **Verify setup**:
   ```bash
   uv run test_setup.py
   ```

## Making Changes

### Branch Strategy

- Create a **feature branch** from `main` for new features
- Create a **bugfix branch** from `main` for bug fixes
- Use descriptive branch names: `feature/jlinc-integration`, `bugfix/webhook-timeout`

### Commit Messages

Follow conventional commit format:
```
type(scope): description

[optional body]

[optional footer]
```

Examples:
- `feat(webhook): add retry mechanism for failed webhooks`
- `fix(config): resolve environment variable loading issue`
- `docs(readme): update installation instructions`

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

## Testing

### Running Tests

1. **Setup verification**:
   ```bash
   uv run test_setup.py
   ```

2. **Load test with minimal parameters**:
   ```bash
   uv run load_test_app.py --rate 1 --amount 5 --duration 10
   ```

3. **Demo mode**:
   ```bash
   uv run demo.py
   ```

### Test Requirements

- Ensure vCon Server is running and accessible
- Verify sample vCon files are available
- Test both with and without JLINC tracer enabled
- Validate configuration backup and restore functionality

## Submitting Changes

### Pull Request Process

1. **Ensure your changes work**:
   - Run all tests
   - Verify functionality with different configurations
   - Check that documentation is updated

2. **Create a Pull Request**:
   - Use a clear, descriptive title
   - Provide a detailed description of changes
   - Reference any related issues
   - Include screenshots for UI changes

3. **PR Description Template**:
   ```markdown
   ## Description
   Brief description of changes

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Documentation update
   - [ ] Performance improvement
   - [ ] Code refactoring

   ## Testing
   - [ ] Ran test_setup.py successfully
   - [ ] Tested with minimal load test
   - [ ] Verified configuration backup/restore
   - [ ] Tested JLINC integration (if applicable)

   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Documentation updated
   - [ ] No breaking changes (or documented)
   ```

## Code Style

### Python Style

- Follow **PEP 8** guidelines
- Use **Black** for code formatting (configured in `pyproject.toml`)
- Use **isort** for import sorting
- Maximum line length: 88 characters

### Formatting Commands

```bash
# Format code
uv run black .

# Sort imports
uv run isort .

# Check formatting
uv run flake8 .
```

### Type Hints

- Use type hints for function parameters and return values
- Use `typing` module for complex types
- Configure mypy for type checking (see `pyproject.toml`)

## Documentation

### Documentation Standards

- Update README.md for user-facing changes
- Add docstrings to new functions and classes
- Update .env.example for new environment variables
- Keep QUICK_REFERENCE.md current

### Documentation Structure

- **README.md**: Main user documentation
- **QUICK_REFERENCE.md**: Quick start guide
- **CONTRIBUTING.md**: This file
- **.env.example**: Environment configuration template
- **LOAD_TEST_SUMMARY.md**: Test results summary
- **PROGRESS_REPORT.md**: Development progress report

## Reporting Issues

### Bug Reports

Use the GitHub issue template and include:

1. **Environment Information**:
   - Python version
   - Operating system
   - uv version
   - vCon Server version

2. **Steps to Reproduce**:
   - Clear, numbered steps
   - Expected vs actual behavior
   - Error messages or logs

3. **Configuration**:
   - Relevant .env settings
   - Command line arguments used
   - vCon Server configuration

### Feature Requests

- Describe the feature clearly
- Explain the use case and benefits
- Consider implementation complexity
- Check for existing similar requests

## Development Guidelines

### Adding New Features

1. **Plan the feature**:
   - Define requirements
   - Consider backward compatibility
   - Plan configuration options

2. **Implementation**:
   - Follow existing code patterns
   - Add comprehensive error handling
   - Include logging for debugging

3. **Configuration**:
   - Add environment variables to .env.example
   - Update CLI options if needed
   - Document new configuration options

### Error Handling

- Use specific exception types
- Provide helpful error messages
- Log errors with appropriate levels
- Include context information

### Logging

- Use structured logging
- Include relevant context (test_id, vcon_id, etc.)
- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)
- Avoid logging sensitive information

## Release Process

### Versioning

- Follow semantic versioning (MAJOR.MINOR.PATCH)
- Update version in `pyproject.toml`
- Create release notes for significant changes

### Release Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] Version bumped
- [ ] Changelog updated
- [ ] Release notes prepared

## Getting Help

- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and general discussion
- **Documentation**: Check existing docs first

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

Thank you for contributing to the vCon Server Load Test Application!
