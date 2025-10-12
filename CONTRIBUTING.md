# Contributing to Asantiya

Thank you for your interest in contributing to Asantiya! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Issues

Before creating an issue, please:

1. Check if the issue already exists
2. Use the issue templates provided
3. Provide as much detail as possible including:
   - OS and Python version
   - Asantiya version
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages and logs

### Suggesting Features

We welcome feature suggestions! Please:

1. Check existing feature requests
2. Use the feature request template
3. Describe the use case and benefits
4. Consider implementation complexity

### Code Contributions

#### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/asantiya.git
   cd asantiya
   ```

2. **Install development dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

3. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

4. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

#### Development Workflow

1. **Make your changes**
   - Follow the coding standards (see below)
   - Add tests for new functionality
   - Update documentation as needed

2. **Run tests and quality checks**
   ```bash
   # Run all tests
   pytest
   
   # Run with coverage
   pytest --cov=asantiya --cov-report=html
   
   # Run linting
   flake8 asantiya tests
   
   # Format code
   black asantiya tests
   isort asantiya tests
   
   # Type checking
   mypy asantiya
   
   # Run all pre-commit hooks
   pre-commit run --all-files
   ```

3. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add amazing new feature"
   ```

4. **Push and create a Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

## 📋 Coding Standards

### Code Style

- **Formatting**: Use [Black](https://black.readthedocs.io/) with 88 character line length
- **Import sorting**: Use [isort](https://pycqa.github.io/isort/) with Black profile
- **Linting**: Follow [flake8](https://flake8.pycqa.org/) rules
- **Type hints**: Use [mypy](https://mypy.readthedocs.io/) for type checking

### Code Organization

- **Functions**: Keep functions small and focused (max 20 lines)
- **Classes**: Use descriptive names and docstrings
- **Modules**: One class/function per file when possible
- **Imports**: Group imports (standard, third-party, local)

### Documentation

- **Docstrings**: Use Google-style docstrings for all public functions/classes
- **Comments**: Explain complex logic, not obvious code
- **README**: Update examples and usage when adding features
- **Type hints**: Use type hints for all function parameters and return values

### Testing

- **Coverage**: Maintain at least 80% test coverage
- **Test types**: Write unit tests, integration tests, and end-to-end tests
- **Test names**: Use descriptive test names that explain the scenario
- **Fixtures**: Use pytest fixtures for common test data

### Error Handling

- **Specific exceptions**: Use custom exception types from `schemas.models`
- **Error messages**: Provide clear, actionable error messages
- **Logging**: Use structured logging with appropriate levels
- **Graceful degradation**: Handle errors gracefully when possible

## 🧪 Testing Guidelines

### Test Structure

```python
def test_function_name_scenario_expected_result():
    """Test that function_name does X when given Y."""
    # Arrange
    input_data = "test"
    
    # Act
    result = function_name(input_data)
    
    # Assert
    assert result == "expected"
```

### Test Categories

- **Unit tests**: Test individual functions/methods
- **Integration tests**: Test component interactions
- **End-to-end tests**: Test complete workflows
- **Error tests**: Test error conditions and edge cases

### Mocking

- **External services**: Mock Docker, SSH, and file system operations
- **Network calls**: Mock HTTP requests and API calls
- **File operations**: Use temporary directories for file tests

## 📝 Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```
feat: add support for multi-architecture builds
fix: resolve Docker connection timeout issue
docs: update installation instructions
test: add integration tests for deployment flow
```

## 🔍 Pull Request Process

### Before Submitting

1. **Ensure all tests pass**
2. **Run code quality checks**
3. **Update documentation**
4. **Add/update tests for new features**
5. **Check for breaking changes**

### PR Description

Include:

- **Summary**: Brief description of changes
- **Motivation**: Why this change is needed
- **Changes**: What was changed
- **Testing**: How it was tested
- **Breaking changes**: Any breaking changes
- **Screenshots**: For UI changes

### Review Process

1. **Automated checks**: CI/CD pipeline runs tests and quality checks
2. **Code review**: Maintainers review the code
3. **Testing**: Manual testing if needed
4. **Approval**: At least one approval required
5. **Merge**: Squash and merge to main branch

## 🐛 Bug Reports

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
What you expected to happen.

**Environment:**
- OS: [e.g. Ubuntu 20.04]
- Python version: [e.g. 3.9.0]
- Asantiya version: [e.g. 0.1.0]

**Additional context**
Any other context about the problem.
```

## 💡 Feature Requests

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of what the problem is.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
A clear description of any alternative solutions.

**Additional context**
Any other context or screenshots about the feature request.
```

## 🏷️ Release Process

### Version Numbering

We use [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. **Update version** in `pyproject.toml`
2. **Update CHANGELOG.md**
3. **Run full test suite**
4. **Create release tag**
5. **Build and publish package**
6. **Update documentation**

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Email**: shahiddev91@gmail.com for direct contact

## 🙏 Recognition

Contributors will be recognized in:

- **README.md**: Contributors section
- **CHANGELOG.md**: Release notes
- **GitHub**: Contributor statistics

Thank you for contributing to Asantiya! 🎉
