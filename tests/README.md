# Scribes Backend - Test Suite

Comprehensive test coverage for all backend services and features.

## 📁 Directory Structure

```
tests/
├── unit/              # Unit tests for individual services/components
├── integration/       # Integration tests for multiple components
├── e2e/              # End-to-end tests for complete workflows
└── utilities/        # Test utilities and helper scripts
```

## 🧪 Test Categories

### Unit Tests (`unit/`)

Tests for individual services in isolation with mocked dependencies.

- **`test_assistant_service.py`** - AI Assistant service tests
  - Query validation
  - RAG pipeline steps
  - Error handling
  - Token budget enforcement
  - 13 comprehensive test cases

- **`test_hf_textgen_service.py`** - Hugging Face text generation tests
  - API integration
  - Prompt formatting
  - Response parsing
  - Error handling

- **`test_chunking.py`** - Text chunking service tests
  - Token-aware splitting
  - Overlap handling
  - Edge cases (empty text, long documents)

- **`test_prompt_engine.py`** - Prompt assembly tests
  - Template rendering
  - Context injection
  - Token counting
  - System message formatting

**Run unit tests:**
```bash
pytest tests/unit/ -v
```

---

### Integration Tests (`integration/`)

Tests for multiple components working together.

- **`test_background_jobs.py`** - Background job system tests
  - Job creation and queueing
  - Job execution
  - Status updates
  - Error handling and retries

- **`test_arq_queue.py`** - ARQ queue integration tests
  - Redis connection
  - Job serialization
  - Queue operations

- **`test_job_system.py`** - Complete job system workflow tests
  - End-to-end job processing
  - Worker coordination
  - Result retrieval

**Run integration tests:**
```bash
pytest tests/integration/ -v
```

**Requirements:**
- Redis server running
- Database connection configured
- Environment variables set

---

### End-to-End Tests (`e2e/`)

Complete workflow tests simulating real user scenarios.

- **`e2e_test_jobs.py`** - Full job processing workflows
  - Export job creation → execution → download
  - Embedding generation jobs
  - Multi-step workflows

**Run e2e tests:**
```bash
pytest tests/e2e/ -v
```

**Requirements:**
- Full application stack running
- Test database seeded
- All services available

---

### Utilities (`utilities/`)

Helper scripts and test utilities (not executed by pytest).

- **`database_connection.py`** - Database connection helpers for tests
  - Test database setup
  - Connection pooling
  - Cleanup utilities

- **`verify_semantic_v2.py`** - Semantic search verification
  - Manual verification of embeddings
  - Search quality checks
  - Performance benchmarks

**Usage:**
```bash
python tests/utilities/verify_semantic_v2.py
```

---

## 🚀 Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test Category
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# E2E tests only
pytest tests/e2e/
```

### Run Specific Test File
```bash
pytest tests/unit/test_assistant_service.py -v
```

### Run Specific Test Function
```bash
pytest tests/unit/test_assistant_service.py::test_query_with_valid_context -v
```

### Run with Coverage
```bash
pytest --cov=app --cov-report=html
```

### Run with Detailed Output
```bash
pytest -vv -s
```

---

## ⚙️ Test Configuration

### `pytest.ini` (Project Root)
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

### Environment Setup
Tests use separate test database and configuration:
```bash
# .env.test file
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/scribes_test
REDIS_URL=redis://localhost:6379/1
HF_API_KEY=your_test_api_key
```

---

## 📊 Test Coverage

Current coverage by service:

| Service | Coverage | Test File |
|---------|----------|-----------|
| AssistantService | 95% | `unit/test_assistant_service.py` |
| HFTextGenService | 90% | `unit/test_hf_textgen_service.py` |
| TokenizerService | 92% | `unit/test_chunking.py` |
| PromptEngine | 88% | `unit/test_prompt_engine.py` |
| Background Jobs | 85% | `integration/test_background_jobs.py` |

**Target:** 90%+ coverage across all services

---

## 🎯 Testing Best Practices

### 1. Arrange-Act-Assert Pattern
```python
def test_example():
    # Arrange: Set up test data and mocks
    service = MyService()
    mock_data = {"key": "value"}
    
    # Act: Execute the function being tested
    result = service.process(mock_data)
    
    # Assert: Verify the outcome
    assert result == expected_value
```

### 2. Use Fixtures for Common Setup
```python
@pytest.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()
```

### 3. Mock External Dependencies
```python
@patch('app.services.hf_textgen_service.requests.post')
def test_api_call(mock_post):
    mock_post.return_value.json.return_value = {"result": "success"}
    # Test code here
```

### 4. Test Edge Cases
- Empty inputs
- Invalid data types
- Boundary conditions
- Error scenarios

### 5. Keep Tests Independent
- Each test should run in isolation
- No dependencies between tests
- Clean up after each test

---

## 🐛 Debugging Failed Tests

### View Full Error Traceback
```bash
pytest --tb=long
```

### Run Failed Tests Only
```bash
pytest --lf  # last-failed
```

### Stop on First Failure
```bash
pytest -x
```

### Print Debug Output
```bash
pytest -s  # Shows print statements
```

### Run with Python Debugger
```bash
pytest --pdb  # Drops into debugger on failure
```

---

## 📝 Writing New Tests

### Unit Test Template
```python
import pytest
from unittest.mock import Mock, patch
from app.services.my_service import MyService

class TestMyService:
    """Test suite for MyService"""
    
    @pytest.fixture
    def service(self):
        """Fixture providing service instance"""
        return MyService()
    
    def test_basic_functionality(self, service):
        """Test basic service operation"""
        # Arrange
        input_data = "test"
        
        # Act
        result = service.process(input_data)
        
        # Assert
        assert result is not None
        assert isinstance(result, str)
    
    @patch('app.services.my_service.external_api')
    def test_with_mock(self, mock_api, service):
        """Test with mocked external dependency"""
        # Arrange
        mock_api.return_value = {"status": "ok"}
        
        # Act
        result = service.call_external()
        
        # Assert
        mock_api.assert_called_once()
        assert result["status"] == "ok"
```

### Integration Test Template
```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_api_endpoint():
    """Test complete API endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/endpoint",
            json={"data": "test"}
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
```

---

## 🔍 Test Data

For manual testing and data generation:
- **Script:** `scripts/testing/create_test_data.py`
- **Documentation:** `docs/services/ai-assistant/ASSISTANT_MANUAL_TESTING_GUIDE.md`

---

## 📚 Related Documentation

- **Manual Testing Guide:** `docs/services/ai-assistant/ASSISTANT_MANUAL_TESTING_GUIDE.md`
- **Unit Test Documentation:** `docs/guides/backend implementations/ASSISTANT_UNIT_TESTS_COMPLETE.md`
- **CI/CD Testing:** `docs/TESTING_DEPLOYMENT_CHECKLIST.md`

---

## ✅ Pre-Deployment Checklist

Before deploying to production:

- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Code coverage > 90%
- [ ] E2E tests validated
- [ ] No skipped tests without documentation
- [ ] Performance benchmarks met
- [ ] Security tests passed

---

**Last Updated:** December 12, 2025
