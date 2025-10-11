# Contributing to Cirrostrats Backend

Thank you for your interest in contributing to the Cirrostrats Backend! We welcome contributions from the community and are grateful for your support.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Project Structure](#project-structure)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Issue Guidelines](#issue-guidelines)
- [Community](#community)

## 🤝 Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please be respectful, inclusive, and professional in all interactions.

### Our Standards

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+**
- **pip** (Python package manager)
- **Git**
- **MongoDB** (for database operations)
- **Virtual Environment** (recommended)

### Fork and Clone

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/cirrostrats-backend.git
   cd cirrostrats-backend
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/ujazishere/cirrostrats-backend.git
   ```

## 🛠️ Development Setup

### 1. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your configuration
# Add your MongoDB connection string, API keys, etc.
```

### 4. Database Setup

```bash
# Ensure MongoDB is running
# Import any required seed data (if applicable)
```

### 5. Run the Application

```bash
# Start the FastAPI server
uvicorn main:app --reload

# The API will be available at http://localhost:8000
# API documentation at http://localhost:8000/docs
```

## 🤝 How to Contribute

### Types of Contributions

We welcome various types of contributions:

- 🐛 **Bug fixes**
- ✨ **New features**
- 📚 **Documentation improvements**
- 🧪 **Tests**
- 🎨 **Code refactoring**
- 🔧 **Configuration improvements**
- 📊 **Performance optimizations**

### Before You Start

1. **Check existing issues** to avoid duplicate work
2. **Create an issue** for new features or major changes
3. **Discuss your approach** with maintainers
4. **Keep changes focused** - one feature/fix per PR

## 📝 Pull Request Process

### 1. Create a Branch

```bash
# Update your fork
git fetch upstream
git checkout main
git merge upstream/main

# Create a feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

### 2. Make Your Changes

- Follow our [coding standards](#coding-standards)
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass

### 3. Commit Your Changes

```bash
# Stage your changes
git add .

# Commit with a descriptive message
git commit -m "feat: add new weather data processing endpoint

- Implement weather data aggregation
- Add input validation
- Include comprehensive error handling
- Add unit tests for new functionality"
```

### 4. Push and Create PR

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create a Pull Request on GitHub
```

### 5. PR Requirements

Your PR should include:

- **Clear description** of changes
- **Link to related issue** (if applicable)
- **Screenshots** (for UI changes)
- **Test coverage** for new code
- **Updated documentation**
- **No breaking changes** (unless discussed)

## 📏 Coding Standards

### Python Style Guide

We follow **PEP 8** with some project-specific conventions:

```python
# Use descriptive variable names
weather_data = fetch_weather_data()
airport_codes = get_airport_codes()

# Add docstrings to functions
def process_flight_data(flight_id: str) -> dict:
    """
    Process flight data for the given flight ID.
    
    Args:
        flight_id: The unique identifier for the flight
        
    Returns:
        dict: Processed flight information
        
    Raises:
        ValueError: If flight_id is invalid
    """
    pass

# Use type hints
def calculate_delay(scheduled: datetime, actual: datetime) -> int:
    return (actual - scheduled).total_seconds()
```

### File Organization

- **Imports**: Standard library → Third-party → Local imports
- **Functions**: Group related functions together
- **Classes**: One class per file (unless closely related)
- **Constants**: Use UPPER_CASE for constants

### Code Quality

- **Line length**: Maximum 88 characters
- **Indentation**: 4 spaces (no tabs)
- **Trailing whitespace**: Remove all trailing whitespace
- **Blank lines**: Use blank lines to separate logical sections

## 🏗️ Project Structure

Understanding our project structure:

```
cirrostrats-backend/
├── core/                   # Core business logic
│   ├── api/               # External API integrations
│   ├── search/            # Search functionality
│   ├── tests/             # Unit tests
│   └── pkl/               # Core-specific data files
├── routes/                # API route definitions
├── services/              # Business service layer
├── models/                # Data models
├── schema/                # API schemas
├── utils/                 # Utility functions
├── data/                  # General data files
├── docs/                  # Documentation
├── notebooks/             # Development notebooks
├── config/                # Configuration files
├── main.py               # FastAPI application entry
└── requirements.txt      # Dependencies
```

### Key Principles

- **Separation of concerns**: Keep business logic separate from API routes
- **Data organization**: General data in `data/`, core-specific in `core/pkl/`
- **Documentation**: All major changes should be documented
- **Testing**: New features should include tests

## 🧪 Testing Guidelines

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest core/tests/test_weather.py

# Run tests with verbose output
pytest -v
```

### Writing Tests

```python
import pytest
from your_module import your_function

def test_your_function():
    """Test that your_function works correctly."""
    # Arrange
    input_data = "test_input"
    expected_output = "expected_result"
    
    # Act
    result = your_function(input_data)
    
    # Assert
    assert result == expected_output

def test_your_function_with_invalid_input():
    """Test that your_function handles invalid input."""
    with pytest.raises(ValueError):
        your_function(None)
```

### Test Coverage

- Aim for **80%+ test coverage**
- Test both **happy path** and **error cases**
- Include **integration tests** for API endpoints
- Mock external dependencies

## 📚 Documentation

### Code Documentation

- **Docstrings**: All public functions and classes
- **Comments**: Explain complex logic, not obvious code
- **Type hints**: Use for all function parameters and returns
- **README updates**: Update if you change setup/usage

### API Documentation

- FastAPI automatically generates docs at `/docs`
- Ensure all endpoints have proper descriptions
- Include example requests/responses
- Document error codes and responses

## 🐛 Issue Guidelines

### Reporting Bugs

When reporting bugs, please include:

- **Clear title** describing the issue
- **Steps to reproduce** the bug
- **Expected behavior** vs **actual behavior**
- **Environment details** (OS, Python version, etc.)
- **Error messages** or logs
- **Screenshots** if applicable

### Feature Requests

For feature requests, please include:

- **Clear description** of the feature
- **Use case** - why is this needed?
- **Proposed implementation** (if you have ideas)
- **Alternatives considered**
- **Additional context**

### Issue Labels

We use labels to categorize issues:

- `bug` - Something isn't working
- `enhancement` - New feature or request
- `documentation` - Improvements to docs
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `priority: high/medium/low` - Issue priority

## 🌟 Community

### Getting Help

- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and general discussion
- **Email**: Contact maintainers directly for sensitive issues

### Recognition

We recognize contributors in:

- **README**: Major contributors listed
- **Release notes**: Contributors mentioned in releases
- **GitHub**: Contributor graphs and statistics

### Maintainer Responsibilities

Maintainers will:

- **Review PRs** within 7 days
- **Respond to issues** within 48 hours
- **Provide feedback** on contributions
- **Maintain project direction** and quality

## 📋 Checklist for Contributors

Before submitting your contribution:

- [ ] Code follows project style guidelines
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Documentation updated (if applicable)
- [ ] Commit messages are descriptive
- [ ] PR description is clear and complete
- [ ] No sensitive information in code
- [ ] Changes are focused and atomic

## 🙏 Thank You

Thank you for contributing to Cirrostrats Backend! Your contributions help make this project better for everyone.

---

**Questions?** Feel free to reach out to the maintainers or create an issue for clarification.

**Happy coding!** 🚀
