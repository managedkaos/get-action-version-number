# Test Suite Documentation

This document provides a comprehensive overview of the test suite for the GitHub Action Version Lookup Script (`main.py`). The test suite consists of **34 tests** covering all major functionality and edge cases.

## Test Structure

### Test Classes

#### 1. `TestParseActionString` (8 tests)

Tests the `parse_action_string()` function which parses GitHub action strings.

**Test Cases:**

- `test_action_with_version`: Parses actions with version (e.g., `actions/checkout@v4`)
- `test_action_without_version`: Parses actions without version (e.g., `actions/setup-python`)
- `test_action_with_uses_prefix`: Handles `uses:` prefix in workflow format
- `test_action_with_uses_prefix_no_version`: Handles `uses:` prefix without version
- `test_action_with_whitespace`: Handles extra whitespace in action strings
- `test_invalid_action_format`: Tests invalid format that raises ValueError
- `test_invalid_action_returns_no_releases`: Tests invalid actions return "No releases found"
- `test_empty_action`: Tests empty action string raises ValueError

#### 2. `TestGetLatestRelease` (5 tests)

Tests the `get_latest_release()` function which fetches releases from GitHub API.

**Test Cases:**

- `test_successful_release_fetch`: Tests successful API response with releases
- `test_no_releases_found`: Tests when no releases are available
- `test_draft_releases_filtered`: Tests that draft releases are filtered out
- `test_rate_limiting_handling`: Tests retry logic for 429 rate limit errors
- `test_network_error_handling`: Tests network error handling and retry logic

#### 3. `TestProcessAction` (4 tests)

Tests the `process_action()` function which processes single actions.

**Test Cases:**

- `test_successful_action_processing`: Tests successful action processing
- `test_action_without_version`: Tests actions without version specification
- `test_no_releases_found`: Tests when no releases are found
- `test_invalid_action_format`: Tests invalid action format handling

#### 4. `TestProcessActionForJson` (3 tests)

Tests the `process_action_for_json()` function for JSON output format.

**Test Cases:**

- `test_successful_action_processing`: Tests successful JSON processing
- `test_action_without_version`: Tests JSON processing without version
- `test_invalid_action_format`: Tests invalid action format in JSON mode

#### 5. `TestProcessFile` (2 tests)

Tests the `process_file()` function which processes files containing actions.

**Test Cases:**

- `test_successful_file_processing`: Tests processing files with multiple actions
- `test_file_not_found`: Tests file not found error handling

#### 6. `TestProcessFileJson` (1 test)

Tests the `process_file_json()` function for JSON file processing.

**Test Cases:**

- `test_successful_file_processing_json`: Tests JSON file processing with multiple actions

#### 7. `TestExtractActionsFromWorkflow` (3 tests)

Tests the `extract_actions_from_workflow()` function which extracts actions from workflow files.

**Test Cases:**

- `test_extract_actions_from_workflow`: Tests extracting actions from workflow files
- `test_extract_actions_without_versions`: Tests extracting actions without versions
- `test_file_not_found`: Tests workflow file not found handling

#### 8. `TestProcessWorkflow` (2 tests)

Tests the `process_workflow()` function which processes workflow files.

**Test Cases:**

- `test_successful_workflow_processing`: Tests successful workflow processing
- `test_no_actions_found`: Tests when no actions are found in workflow

#### 9. `TestProcessWorkflowJson` (1 test)

Tests the `process_workflow_json()` function for JSON workflow processing.

**Test Cases:**

- `test_successful_workflow_processing_json`: Tests JSON workflow processing

#### 10. `TestProcessStdin` (2 tests)

Tests the `process_stdin()` function which handles stdin input.

**Test Cases:**

- `test_stdin_processing`: Tests standard stdin processing
- `test_stdin_processing_json`: Tests JSON stdin processing

#### 11. `TestIsInputPiped` (2 tests)

Tests the `is_input_piped()` function which detects piped input.

**Test Cases:**

- `test_piped_input`: Tests detection of piped input
- `test_terminal_input`: Tests detection of terminal input

#### 12. `TestIntegration` (1 test)

Integration tests that test multiple functions together.

**Test Cases:**

- `test_parse_and_process_workflow`: Tests end-to-end workflow processing

## Test Coverage

### Function Coverage

- ✅ `parse_action_string()` - 8 tests
- ✅ `get_latest_release()` - 5 tests
- ✅ `process_action()` - 4 tests
- ✅ `process_action_for_json()` - 3 tests
- ✅ `process_file()` - 2 tests
- ✅ `process_file_json()` - 1 test
- ✅ `extract_actions_from_workflow()` - 3 tests
- ✅ `process_workflow()` - 2 tests
- ✅ `process_workflow_json()` - 1 test
- ✅ `process_stdin()` - 2 tests
- ✅ `is_input_piped()` - 2 tests

### Scenario Coverage

- ✅ **Valid Inputs**: Normal action strings, versions, workflow files
- ✅ **Invalid Inputs**: Malformed actions, empty strings, invalid formats
- ✅ **Error Handling**: Network errors, file not found, API errors
- ✅ **Edge Cases**: Rate limiting, draft releases, no releases found
- ✅ **Output Formats**: Standard output and JSON output
- ✅ **Input Methods**: Single actions, files, workflows, stdin, piped input

### Mock Strategy

The test suite uses comprehensive mocking to ensure:

- **No Real API Calls**: All GitHub API calls are mocked
- **Fast Execution**: No network delays or real file I/O
- **Predictable Results**: Controlled test scenarios
- **Error Simulation**: Network errors, rate limiting, file errors

## Key Testing Features

### Mocking Strategy

- **`unittest.mock.patch`**: Mocks external dependencies
- **`MagicMock`**: Creates mock objects for API responses
- **`mock_open`**: Mocks file operations
- **`StringIO`**: Mocks stdin input

### Error Testing

- **Network Errors**: Simulates API failures
- **Rate Limiting**: Tests 429 error handling with retry logic
- **File Errors**: Tests missing files and read errors
- **Invalid Inputs**: Tests malformed action strings

### Edge Case Testing

- **Empty Inputs**: Empty strings, empty files
- **Whitespace**: Extra spaces in action strings
- **Comments**: Lines starting with `#` in files
- **Draft Releases**: GitHub releases marked as drafts
- **No Releases**: Repositories with no releases

## Running the Tests

### Prerequisites

```bash
pip install pytest requests
```

### Run All Tests

```bash
python -m pytest test_main.py -v
```

### Run Specific Test Class

```bash
python -m pytest test_main.py::TestParseActionString -v
```

### Run Specific Test

```bash
python -m pytest test_main.py::TestParseActionString::test_action_with_version -v
```

### Run with Coverage (if coverage is installed)

```bash
python -m pytest test_main.py --cov=main --cov-report=html
```

## Test Results

### Expected Output

```
============================================== test session starts ===============================================
platform darwin -- Python 3.9.6, pytest-8.3.5, pluggy-1.5.0
collected 34 items

test_main.py ..................................                                                            [100%]

========================================= 34 passed, 1 warning in 10.78s =========================================
```

### Test Categories

- **Unit Tests**: 33 tests covering individual functions
- **Integration Tests**: 1 test covering end-to-end functionality
- **Error Tests**: 8 tests covering error conditions
- **Edge Case Tests**: 6 tests covering boundary conditions
- **Mock Tests**: 34 tests using mocked dependencies

## Quality Metrics

### Test Quality Indicators

- **Comprehensive Coverage**: All major functions tested
- **Edge Case Coverage**: Invalid inputs, error conditions
- **Mock Usage**: No real external dependencies
- **Fast Execution**: All tests complete in under 15 seconds
- **Clear Documentation**: Each test has descriptive docstrings
- **Maintainable**: Well-structured test classes and methods

### Reliability Features

- **Isolated Tests**: Each test is independent
- **Mocked Dependencies**: No external service calls
- **Predictable Results**: Controlled test scenarios
- **Error Simulation**: Realistic error conditions
- **Retry Logic Testing**: Rate limiting and network error handling

## Maintenance

### Adding New Tests

1. Create test method in appropriate test class
2. Use descriptive method name starting with `test_`
3. Add docstring explaining test purpose
4. Use appropriate mocking for external dependencies
5. Test both success and failure scenarios

### Updating Tests

- Update tests when function signatures change
- Maintain mock responses to match actual API responses
- Keep error handling tests current with implementation
- Update integration tests for new features

### Best Practices

- **Mock External Dependencies**: Never make real API calls
- **Test Error Conditions**: Include failure scenarios
- **Use Descriptive Names**: Clear test method names
- **Document Test Purpose**: Include docstrings
- **Test Edge Cases**: Boundary conditions and invalid inputs
- **Keep Tests Fast**: Use mocking to avoid delays

## Conclusion

The test suite provides comprehensive coverage of the GitHub Action Version Lookup Script, ensuring reliability and maintainability. With 34 tests covering all major functions and edge cases, the test suite validates:

- ✅ **Functionality**: All features work as expected
- ✅ **Error Handling**: Graceful handling of errors
- ✅ **Edge Cases**: Boundary conditions and invalid inputs
- ✅ **Output Formats**: Both standard and JSON output
- ✅ **Input Methods**: All supported input methods
- ✅ **Integration**: End-to-end functionality

The test suite serves as a foundation for continuous development and ensures the script remains reliable as new features are added.
