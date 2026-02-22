# RAG System Tests

This directory contains the test suite for the RAG (Retrieval-Augmented Generation) chatbot system.

## Test Structure

```
backend/tests/
├── conftest.py          # Shared test fixtures and configuration
├── test_api.py          # API endpoint tests (FastAPI)
├── test_rag_system.py   # RAG system orchestrator tests
├── test_models.py       # Pydantic model validation tests
└── README.md           # This file
```

## Running Tests

### Install Test Dependencies

```bash
# Install all development dependencies including pytest
uv sync --extra dev
```

### Run All Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with coverage report
uv run pytest --cov=backend --cov-report=html
```

### Run Specific Test Categories

```bash
# Run only API tests
uv run pytest -m api

# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration
```

### Run Specific Test Files

```bash
# Run API endpoint tests
uv run pytest backend/tests/test_api.py

# Run RAG system tests
uv run pytest backend/tests/test_rag_system.py

# Run model tests
uv run pytest backend/tests/test_models.py
```

### Run Specific Test Classes or Methods

```bash
# Run a specific test class
uv run pytest backend/tests/test_api.py::TestQueryEndpoint

# Run a specific test method
uv run pytest backend/tests/test_api.py::TestQueryEndpoint::test_query_without_session_id
```

## Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.unit` - Unit tests for individual components
- `@pytest.mark.integration` - Integration tests across components

## Test Fixtures

The `conftest.py` file provides shared fixtures:

### Configuration Fixtures
- `test_config` - Test configuration with temporary database path

### Data Fixtures
- `sample_course` - Sample course with lessons
- `sample_course_chunks` - Sample course chunks for testing
- `sample_query_response` - Sample API query response
- `sample_course_stats` - Sample course statistics response

### Mock Fixtures
- `mock_vector_store` - Mock vector store for testing
- `mock_ai_generator` - Mock AI generator for testing
- `mock_session_manager` - Mock session manager for testing
- `mock_document_processor` - Mock document processor for testing
- `mock_tool_manager` - Mock tool manager for testing
- `mock_rag_system` - Complete mock RAG system with all dependencies

### API Test Fixtures
- `test_app` - FastAPI test application
- `client` - FastAPI test client

## Writing New Tests

### Unit Tests

Unit tests should test individual components in isolation using mocks:

```python
@pytest.mark.unit
def test_my_component(mock_dependency):
    """Test description"""
    # Arrange
    component = MyComponent(mock_dependency)

    # Act
    result = component.do_something()

    # Assert
    assert result == expected_value
    mock_dependency.some_method.assert_called_once()
```

### API Tests

API tests should test FastAPI endpoints using the test client:

```python
@pytest.mark.api
def test_my_endpoint(client, mock_rag_system):
    """Test description"""
    # Make request
    response = client.post("/api/endpoint", json={"key": "value"})

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "expected_field" in data
```

### Integration Tests

Integration tests should test multiple components working together:

```python
@pytest.mark.integration
def test_end_to_end_flow(test_config):
    """Test description"""
    # Setup real components (not mocks)
    rag_system = RAGSystem(test_config)

    # Execute flow
    result = rag_system.query("test query")

    # Verify result
    assert result is not None
```

## Test Design Principles

1. **Isolation** - Tests should be independent and not rely on external state
2. **Clarity** - Test names should clearly describe what is being tested
3. **AAA Pattern** - Organize tests as Arrange, Act, Assert
4. **DRY** - Use fixtures to avoid code duplication
5. **Fast** - Use mocks to avoid slow operations (API calls, database queries)
6. **Deterministic** - Tests should always produce the same result

## Continuous Integration

Tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    uv sync --extra dev
    uv run pytest --verbose
```

## Debugging Tests

### Run with Debug Output

```bash
# Show print statements and logging
uv run pytest -s

# Show local variables on failure
uv run pytest -l

# Drop into debugger on failure
uv run pytest --pdb
```

### Run Failed Tests Only

```bash
# Re-run only failed tests from last run
uv run pytest --lf

# Re-run failed tests first, then all others
uv run pytest --ff
```

## Coverage

Generate coverage reports to identify untested code:

```bash
# Generate HTML coverage report
uv run pytest --cov=backend --cov-report=html

# Open coverage report (macOS)
open htmlcov/index.html

# Generate terminal coverage report
uv run pytest --cov=backend --cov-report=term-missing
```

## Known Issues

### Static Files in Tests

The main `app.py` mounts static files from the `frontend/` directory, which may not exist in test environments. The test suite uses a separate test app (`create_test_app` in `test_api.py`) that defines API endpoints inline without mounting static files.

### ChromaDB Warnings

ChromaDB may produce resource tracker warnings during tests. These are suppressed in the main app and don't affect test functionality.

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [FastAPI testing guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest-asyncio documentation](https://pytest-asyncio.readthedocs.io/)
