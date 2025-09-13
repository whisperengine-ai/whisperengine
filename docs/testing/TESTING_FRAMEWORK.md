# LLM Testing Framework Documentation

This document explains how to use the mock-based testing system for LLM-dependent functionality in the WhisperEngine project.

## Overview

The testing framework provides two modes:
- **Unit Tests**: Use mock LLM clients for fast, reliable tests
- **Integration Tests**: Use real LLM connections for end-to-end testing

## Quick Start

### Running Unit Tests (Recommended)
```bash
# Run all unit tests with mocks
pytest -m unit

# Run specific unit test
pytest tests/test_emotion_system.py::test_emotion_detection_mock -v

# Run unit tests with verbose output
pytest -m unit -v
```

### Running Integration Tests
```bash
# Set environment variable and run integration tests
USE_REAL_LLM=true pytest -m integration

# Run specific integration test  
USE_REAL_LLM=true pytest tests/test_emotion_system.py::test_emotion_detection_real -v
```

## Test Structure

Each LLM-dependent test comes in two flavors:

### Unit Test (Mock)
```python
@pytest.mark.unit
def test_emotion_detection_mock(mock_llm_client, temp_profiles_file):
    """Test emotion detection with mock LLM client"""
    emotion_manager = EmotionManager(temp_profiles_file, llm_client=mock_llm_client)
    _run_emotion_detection_test(emotion_manager)
```

### Integration Test (Real LLM)  
```python
@pytest.mark.integration
def test_emotion_detection_real(real_llm_client, temp_profiles_file):
    """Test emotion detection with real LLM client"""
    emotion_manager = EmotionManager(temp_profiles_file, llm_client=real_llm_client)
    _run_emotion_detection_test(emotion_manager)
```

### Shared Test Logic
```python
def _run_emotion_detection_test(emotion_manager):
    """Common test logic for both mock and real LLM tests"""
    # Test implementation here
```

## Available Fixtures

### Mock Fixtures
- `mock_llm_client`: Basic mock with default responses
- `disconnected_mock_llm_client`: Mock that simulates connection failure  
- `happy_emotion_mock_llm_client`: Mock with predefined happy emotion responses
- `personal_info_mock_llm_client`: Mock with predefined personal info responses
- `comprehensive_mock_llm_client`: Mock with all predefined responses

### Real LLM Fixtures
- `real_llm_client`: Real LMStudioClient (only if USE_REAL_LLM=true)

### Utility Fixtures
- `temp_profiles_file`: Temporary file for user profiles
- `test_environment`: Test-specific environment variables

## Mock LLM Client Features

The `MockLMStudioClient` provides realistic responses for:

### Emotion Analysis
```python
# Detects emotions based on keywords
"I'm so excited!" → {"primary_emotion": "happy", "confidence": 0.85}
"This is frustrating" → {"primary_emotion": "frustrated", "confidence": 0.8}
"I'm feeling sad" → {"primary_emotion": "sad", "confidence": 0.75}
```

### Personal Info Extraction
```python
# Extracts names, occupations, hobbies
"My name is Alice and I work at Google" → {
    "personal_info": {
        "names": ["Alice"],
        "occupation": ["works at Google"]
    }
}
```

### Trust Indicators
```python
# Detects trust-building behaviors
"Thank you for your help!" → {
    "trust_indicators": ["expressing gratitude", "seeking help"]
}
```

### User Facts
```python
# Extracts factual information
"My name is Bob and I love programming" → {
    "extracted_facts": [
        "User's name is Bob",
        "User loves programming"
    ]
}
```

## Custom Mock Responses

You can create custom mock responses for specific test scenarios:

```python
def test_specific_emotion_scenario():
    # Create mock with custom responses
    custom_responses = {
        "I hate this project!": {
            "primary_emotion": "angry",
            "confidence": 0.9,
            "intensity": 0.8,
            "secondary_emotions": ["frustrated"],
            "reasoning": "Strong negative language indicates anger"
        }
    }
    
    mock_client = create_mock_llm_client(
        emotion_responses=custom_responses
    )
    
    # Use in your test
    emotion_manager = EmotionManager(llm_client=mock_client)
    # ... test logic
```

## Environment Configuration

### Unit Tests (Default)
- No special configuration needed
- Always use mocks
- Fast and reliable

### Integration Tests
- Set `USE_REAL_LLM=true` environment variable
- Requires LM Studio running on localhost:1234
- Tests actual LLM responses

### Environment Variables
```bash
# For integration tests
export USE_REAL_LLM=true

# LLM connection settings (optional)
export LLM_API_URL=http://localhost:1234/v1
export LLM_REQUEST_TIMEOUT=90
export LLM_CONNECTION_TIMEOUT=10
```

## Test Markers

Tests are automatically marked based on fixtures used:

- `@pytest.mark.unit`: Tests using mock fixtures
- `@pytest.mark.integration`: Tests using real LLM client
- `@pytest.mark.llm`: All tests dealing with LLM functionality

### Running by Marker
```bash
pytest -m unit           # Only unit tests
pytest -m integration    # Only integration tests  
pytest -m llm            # All LLM-related tests
pytest -m "not integration"  # All tests except integration
```

## Troubleshooting

### Mock Tests Failing
- Check mock response configurations
- Verify test logic doesn't depend on specific LLM behavior
- Use verbose mode: `pytest -v -s`

### Integration Tests Failing
- Ensure LM Studio is running and accessible
- Check environment variables are set correctly
- Verify network connectivity
- Use `pytest -v -s` for detailed output

### Common Issues

1. **Import Errors**: Make sure all test files import pytest
2. **Fixture Not Found**: Check conftest.py is in tests/ directory
3. **Environment Variables**: Use `load_dotenv()` for .env file support

## Best Practices

### For Unit Tests
- Use mocks by default for speed and reliability
- Test business logic, not LLM behavior
- Mock should provide realistic but predictable responses
- Focus on edge cases and error handling

### For Integration Tests  
- Test actual LLM integration
- Verify end-to-end functionality
- Use for final validation before deployment
- Keep these tests separate and optional

### Test Organization
- Keep shared test logic in `_run_*` functions
- Use descriptive test names
- Group related tests in same file
- Use fixtures for setup/teardown

## Example Test File Structure

```python
#!/usr/bin/env python3
"""
Test module for XYZ functionality
"""

import pytest
from your_module import YourClass

@pytest.mark.unit
def test_functionality_mock(mock_llm_client, temp_profiles_file):
    """Test with mock LLM client"""
    instance = YourClass(llm_client=mock_llm_client)
    _run_functionality_test(instance)

@pytest.mark.integration  
def test_functionality_real(real_llm_client, temp_profiles_file):
    """Test with real LLM client"""
    instance = YourClass(llm_client=real_llm_client)
    _run_functionality_test(instance)

def _run_functionality_test(instance):
    """Common test logic"""
    # Your test implementation here
    assert instance.some_method() == expected_result

if __name__ == "__main__":
    print("Use pytest to run these tests")
```

This framework allows you to maintain fast, reliable unit tests while also supporting comprehensive integration testing when needed.
