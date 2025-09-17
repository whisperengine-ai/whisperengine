# 🧪 WhisperEngine Testing Framework

## Overview

WhisperEngine includes a comprehensive, production-ready testing framework designed to ensure system reliability, performance, and security across all deployment modes.

## Test Categories

### 🏗️ **Unit Tests** (`pytest -m unit`)
Fast, isolated tests with no external dependencies.
- **Focus**: Core functionality, business logic, data structures
- **Dependencies**: Mock/stub all external services
- **Speed**: < 5 seconds total execution time
- **Coverage**: Target 90%+ code coverage

**Example:**
```bash
# Run all unit tests
pytest -m unit -v

# Run with coverage
pytest -m unit --cov=src --cov-report=html
```

### 🔗 **Integration Tests** (`pytest -m integration`)
End-to-end workflows testing component interactions.
- **Focus**: API integrations, database operations, cross-component workflows
- **Dependencies**: May use real services (LLM, databases)
- **Speed**: < 2 minutes total execution time
- **Coverage**: Critical user journeys

**Example:**
```bash
# Run integration tests
pytest -m integration -v

# Skip slow integration tests
pytest -m "integration and not slow"
```

### 🏃 **Performance Tests** (`pytest -m performance`)
System performance, scalability, and resource usage validation.
- **Focus**: Response times, throughput, memory usage, concurrent handling
- **Dependencies**: Performance monitoring tools
- **Speed**: < 5 minutes total execution time
- **Metrics**: Latency, throughput, resource utilization

**Example:**
```bash
# Run performance tests with benchmarking
pytest -m performance --benchmark-only
```

### 🔒 **Security Tests** (`pytest -m security`)
Security validation and vulnerability testing.
- **Focus**: Input validation, authentication, authorization, data protection
- **Dependencies**: Security testing tools
- **Speed**: < 3 minutes total execution time
- **Coverage**: Common attack vectors, data protection

**Example:**
```bash
# Run security validation tests
pytest -m security -v
```

## Test Suites Structure

```
tests/
├── test_suites/                    # Organized test suites
│   ├── test_core_functionality.py  # Unit tests for core components
│   ├── test_integration.py         # Integration tests
│   ├── test_performance.py         # Performance benchmarks
│   └── test_security.py           # Security validation
├── ci_test_runner.py              # Comprehensive test runner
├── conftest.py                    # Shared fixtures and configuration
└── test_mocks.py                  # Mock objects and test data
```

## Running Tests

### 🚀 **Quick Start**
```bash
# Run all tests with our simplified script
./scripts/run_tests.sh

# Run specific category
./scripts/run_tests.sh unit

# Run without parallel execution
./scripts/run_tests.sh all false

# Run with custom report location
./scripts/run_tests.sh integration true true
```

### 🔧 **Advanced Usage**
```bash
# Using the comprehensive test runner directly
python tests/ci_test_runner.py --category all --report test_report.json

# Run specific test files
pytest tests/test_suites/test_core_functionality.py -v

# Run with custom markers
pytest -m "unit and not slow" --tb=short

# Parallel execution with coverage
pytest -m unit -n 4 --cov=src --cov-report=term-missing
```

### 🐳 **Docker Testing**
```bash
# Test in Docker environment
docker-compose -f docker-compose.dev.yml run whisperengine-bot python tests/ci_test_runner.py

# Test with production-like setup
docker-compose -f docker-compose.prod.yml run whisperengine-bot ./scripts/run_tests.sh
```

## Test Configuration

### Environment Variables
```bash
# Test environment mode
export ENV_MODE=testing

# Mock LLM service for testing
export LLM_CHAT_API_URL=http://mock-llm-server

# Test Discord token (for integration tests)
export DISCORD_BOT_TOKEN=test_token_for_integration
```

### pytest Configuration (`pyproject.toml`)
```toml
[tool.pytest.ini_options]
minversion = "6.0"
addopts = "-ra -q --strict-markers --strict-config"
testpaths = ["tests"]
pythonpath = ["."]
asyncio_mode = "auto"
markers = [
    "unit: Fast unit tests with no external dependencies",
    "integration: Integration tests with real services",
    "performance: Performance and benchmark tests", 
    "security: Security validation tests",
    "slow: Slow-running tests",
    "llm: Tests requiring LLM service integration",
]
```

## Coverage Requirements

### Minimum Coverage Targets
- **Overall**: 85%
- **Core Components**: 90%
- **Critical Paths**: 95%
- **Security Functions**: 100%

### Coverage Reports
```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html

# View coverage in terminal
pytest --cov=src --cov-report=term-missing

# Fail if coverage below threshold
pytest --cov=src --cov-fail-under=85
```

## Performance Benchmarking

### Benchmark Categories
- **Memory Operations**: Store, retrieve, search performance
- **LLM Integration**: Response times, concurrent handling
- **API Throughput**: Requests per second, latency
- **System Resources**: CPU, memory, disk usage

### Benchmark Example
```python
import pytest

@pytest.mark.performance
def test_memory_storage_performance(benchmark):
    def store_memory():
        # Memory storage operation
        pass
    
    result = benchmark(store_memory)
    assert result.duration < 0.1  # < 100ms
```

## Security Testing

### Security Test Categories
- **Input Validation**: XSS, SQL injection, command injection
- **Authentication**: Token validation, privilege escalation
- **Data Protection**: Encryption, PII detection, data isolation
- **System Security**: Path traversal, deserialization attacks

### Security Test Example
```python
@pytest.mark.security
def test_xss_prevention():
    dangerous_input = "<script>alert('xss')</script>"
    assert not validate_user_input(dangerous_input)
```

## CI/CD Integration

### GitHub Actions Workflow
The testing framework integrates with GitHub Actions for:
- **Automated Testing**: Run on every PR and commit
- **Multi-Category Execution**: Parallel test execution by category
- **Coverage Reporting**: Automatic coverage upload to Codecov
- **Performance Tracking**: Benchmark results over time
- **Security Validation**: Security tests in CI pipeline

### Workflow Triggers
- **Pull Requests**: Full test suite
- **Main Branch**: Full test suite + deployment
- **Scheduled**: Nightly comprehensive testing
- **Manual**: On-demand test execution

## Test Data Management

### Mock Data
- **LLM Responses**: Predefined AI responses for consistent testing
- **User Data**: Sanitized test user profiles and conversations
- **System Data**: Mock configuration and environment data

### Test Isolation
- **Database**: Isolated test databases for each test run
- **File System**: Temporary directories for file operations
- **Network**: Mock network services to prevent external dependencies

## Debugging Test Failures

### Common Issues
1. **Environment Setup**: Check virtual environment and dependencies
2. **Mock Configuration**: Verify mock objects are properly configured
3. **Async Operations**: Ensure proper async/await patterns
4. **Resource Cleanup**: Check for proper cleanup in test teardown

### Debug Commands
```bash
# Verbose output with full tracebacks
pytest -vvv --tb=long

# Drop into debugger on failure
pytest --pdb

# Run only failed tests from last run
pytest --lf

# Show test durations
pytest --durations=10
```

## Performance Optimization

### Test Execution Speed
- **Parallel Execution**: Use `pytest-xdist` for parallel test running
- **Test Isolation**: Minimize test dependencies and setup time
- **Mock Usage**: Mock external services to eliminate network delays
- **Selective Running**: Use markers to run only relevant tests

### Resource Management
- **Memory**: Monitor memory usage in long-running test suites
- **Database**: Use transaction rollback for test isolation
- **File System**: Clean up temporary files after tests
- **Network**: Mock network calls to avoid timeouts

## Best Practices

### Test Writing
1. **AAA Pattern**: Arrange, Act, Assert structure
2. **Single Responsibility**: One test, one assertion focus
3. **Descriptive Names**: Clear test method and fixture names
4. **Independent Tests**: No test dependencies or order requirements

### Mock Usage
1. **Strategic Mocking**: Mock at the right boundaries
2. **Realistic Data**: Use realistic mock data and responses
3. **Error Scenarios**: Test both success and failure paths
4. **Async Mocking**: Proper async mock configuration

### Performance Testing
1. **Baseline Metrics**: Establish performance baselines
2. **Consistent Environment**: Use consistent test environments
3. **Statistical Significance**: Run multiple iterations for accuracy
4. **Resource Monitoring**: Monitor system resources during tests

## Troubleshooting

### Common Problems

**Tests Not Found**
```bash
# Check test discovery
pytest --collect-only

# Verify PYTHONPATH
export PYTHONPATH=.
```

**Import Errors**
```bash
# Install in development mode
pip install -e .

# Check dependencies
pip install -r requirements-dev.txt
```

**Async Test Issues**
```bash
# Ensure pytest-asyncio is installed
pip install pytest-asyncio

# Check asyncio mode in pytest config
```

**Coverage Issues**
```bash
# Include source directory
pytest --cov=src

# Check .coveragerc configuration
```

### Getting Help

- **Documentation**: Check this file and inline test documentation
- **Examples**: Review existing tests for patterns and best practices
- **Community**: Ask questions in GitHub discussions
- **Issues**: Report bugs and feature requests in GitHub issues

## Future Enhancements

### Planned Features
- **Property-Based Testing**: Hypothesis integration for property-based tests
- **Mutation Testing**: Automated test quality assessment
- **Visual Testing**: UI component testing for desktop app
- **Load Testing**: Comprehensive load and stress testing
- **Contract Testing**: API contract validation