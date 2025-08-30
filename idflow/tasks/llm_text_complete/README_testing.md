# LLM Text Complete - Testing Guide

This document explains how to run the unit tests for the LLM text completion functionality.

## Test Structure

The test suite consists of two main parts:

1. **Unit Tests** (`TestLLMTextComplete`): Test the functionality using mocked responses
2. **Integration Tests** (`TestLLMTextCompleteIntegration`): Test with real OpenAI API calls (optional)

## Running Tests

### Unit Tests Only (Recommended for CI/CD)

Run only the unit tests that don't require API connections:

```bash
# Run all unit tests
pytest tasks/llm_text_complete/test_llm_text_complete.py -v

# Run only unit tests (exclude integration tests)
pytest tasks/llm_text_complete/test_llm_text_complete.py -v -m "not integration"

# Run with coverage
pytest tasks/llm_text_complete/test_llm_text_complete.py --cov=tasks.llm_text_complete -v
```

### Integration Tests (Optional)

To run tests with real OpenAI API calls, you need to set up an API key:

1. **Get an OpenAI API Key**:
   - Visit [OpenAI Platform](https://platform.openai.com/api-keys)
   - Create a new API key

2. **Set the Environment Variable**:
   ```bash
   export OPENAI_API_KEY="your_api_key_here"
   ```

3. **Run Integration Tests**:
   ```bash
   # Run all tests including integration tests
   pytest tasks/llm_text_complete/test_llm_text_complete.py -v

   # Run only integration tests
   pytest tasks/llm_text_complete/test_llm_text_complete.py -v -m "integration"
   ```

## Test Categories

### Unit Tests (Mocked)

- **Basic Functionality**: Tests basic text completion without variables
- **Prompt Variables**: Tests prompt variable substitution
- **Parameters**: Tests temperature, top_p, max_tokens, and stop words
- **Error Handling**: Tests various error scenarios
- **Edge Cases**: Tests None values, empty dictionaries, etc.

### Integration Tests (Real API)

- **Real OpenAI Calls**: Tests actual API responses
- **Variable Substitution**: Tests real API with prompt variables

## Test Markers

- `@pytest.mark.integration`: Marks tests that require real API calls
- `@pytest.mark.skipif`: Automatically skips integration tests if no API key is set

## Example Test Output

```
============================= test session starts ==============================
platform linux -- Python 3.11.0, pytest-7.4.0, pluggy-1.2.0
rootdir: /home/user/idflow
plugins: cov-4.1.0
collected 20 items

tasks/llm_text_complete/test_llm_text_complete.py::TestLLMTextComplete::test_basic_completion_without_variables PASSED
tasks/llm_text_complete/test_llm_text_complete.py::TestLLMTextComplete::test_completion_with_prompt_variables PASSED
...
tasks/llm_text_complete/test_llm_text_complete.py::TestLLMTextCompleteIntegration::test_real_openai_completion SKIPPED
tasks/llm_text_complete/test_llm_text_complete.py::TestLLMTextCompleteIntegration::test_real_openai_completion_with_variables SKIPPED

============================== 18 passed, 2 skipped ==============================
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're running tests from the project root directory
2. **Mock Issues**: Unit tests use `unittest.mock` to mock the `litellm.completion` function
3. **API Key Issues**: Integration tests will be skipped if `OPENAI_API_KEY` is not set

### Debug Mode

Run tests with more verbose output:

```bash
pytest tasks/llm_text_complete/test_llm_text_complete.py -v -s --tb=long
```

### Running Individual Tests

```bash
# Run a specific test method
pytest tasks/llm_text_complete/test_llm_text_complete.py::TestLLMTextComplete::test_basic_completion_without_variables -v

# Run a specific test class
pytest tasks/llm_text_complete/test_llm_text_complete.py::TestLLMTextComplete -v
```

## Continuous Integration

For CI/CD pipelines, the tests will automatically:
- Run all unit tests
- Skip integration tests (no API key available)
- Provide comprehensive coverage reporting

The test suite is designed to be reliable and fast for automated testing while still allowing developers to test against real APIs when needed.
