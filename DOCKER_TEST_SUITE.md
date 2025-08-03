# Docker Test Suite

This document describes the Docker test suite for the GitHub Action Version Lookup Script.

## Overview

The Docker test suite (`test_docker.sh`) is a comprehensive Bash script that tests the Docker container with various scenarios to ensure the packaged application works correctly.

## Test Coverage

### Core Functionality Tests

1. **Help Command** - Tests that help information is displayed
2. **Single Action** - Tests processing a single action with version
3. **Single Action JSON** - Tests JSON output for single actions
4. **File Processing** - Tests processing actions from files
5. **File Processing JSON** - Tests JSON output for file processing
6. **Workflow Processing** - Tests processing actions from workflow files
7. **Workflow Processing JSON** - Tests JSON output for workflow processing

### Input Method Tests

8. **Piped Input** - Tests automatic detection of piped input
9. **Piped Input JSON** - Tests JSON output for piped input
10. **Stdin Mode** - Tests interactive stdin mode
11. **Stdin Mode JSON** - Tests JSON output for stdin mode

### Error Handling Tests

12. **Invalid Action** - Tests handling of invalid action formats
13. **File Not Found** - Tests handling of missing files
14. **Workflow Not Found** - Tests handling of missing workflow files
15. **Empty File** - Tests handling of files with no actions
16. **No Arguments** - Tests that help is shown when no arguments provided
17. **Invalid Argument** - Tests handling of invalid command line arguments

### Authentication Tests

18. **Authentication** - Tests with GitHub token (if available)

## Running the Tests

### Prerequisites

- Docker installed and running
- Docker image built: `get-action-version-number:2025-08-02-1d0b205`
- Bash shell
- Python 3 (for JSON validation)

### Run All Tests

```bash
# Using the Makefile
make docker-test

# Or directly
./test_docker.sh
```

### Run with Authentication

```bash
# Set GitHub token
export GITHUB_TOKEN=your_token_here

# Run tests
./test_docker.sh
```

## Test Environment

The test suite creates a temporary test environment in `/tmp/action-lookup-test/` with:

- `test-actions.txt` - Sample actions file
- `test-workflow.yml` - Sample workflow file
- `empty-file.txt` - Empty file for testing

The environment is automatically cleaned up after tests complete.

## Test Output

### Colored Output

- **Green ✓ PASS** - Test passed
- **Red ✗ FAIL** - Test failed
- **Blue ℹ INFO** - Test information
- **Yellow ⚠ WARN** - Warnings (e.g., missing GITHUB_TOKEN)

### Example Output

```
==========================================
Docker Test Suite for Action Lookup Script
==========================================

ℹ INFO: Setting up test environment...
ℹ INFO: Test environment setup complete
Running tests...

ℹ INFO: Running: Help Command
ℹ INFO: Description: Test that help command works and shows usage information
✓ PASS: Help Command

ℹ INFO: Running: Single Action
ℹ INFO: Description: Test processing a single action with version
✓ PASS: Single Action

...

==========================================
Test Results
==========================================
Total Tests: 18
Passed: 18
Failed: 0
✓ PASS: All tests passed!
```

## Test Functions

### `run_test()`

Runs a test that should succeed and match an expected pattern.

```bash
run_test "Test Name" "command" "expected_pattern" "description"
```

### `run_json_test()`

Runs a test that should produce valid JSON output.

```bash
run_json_test "Test Name" "command" "description"
```

### `run_failure_test()`

Runs a test that should fail with a specific error pattern.

```bash
run_failure_test "Test Name" "command" "expected_error_pattern" "description"
```

## Docker Commands Tested

### Basic Usage

```bash
docker run --rm -e GITHUB_TOKEN get-action-version-number:2025-08-02-1d0b205 --help
docker run --rm -e GITHUB_TOKEN get-action-version-number:2025-08-02-1d0b205 'actions/checkout@v4'
```

### File Processing

```bash
docker run --rm -e GITHUB_TOKEN -v /path/to/file.txt:/work/file.txt get-action-version-number:2025-08-02-1d0b205 --file file.txt
```

### Workflow Processing

```bash
docker run --rm -e GITHUB_TOKEN -v /path/to/workflow.yml:/work/workflow.yml get-action-version-number:2025-08-02-1d0b205 --workflow workflow.yml
```

### JSON Output

```bash
docker run --rm -e GITHUB_TOKEN get-action-version-number:2025-08-02-1d0b205 'actions/checkout@v4' --json
```

### Piped Input

```bash
echo 'actions/checkout@v4' | docker run --rm -e GITHUB_TOKEN -i get-action-version-number:2025-08-02-1d0b205
```

### Authentication

```bash
docker run --rm -e GITHUB_TOKEN get-action-version-number:2025-08-02-1d0b205 'actions/checkout@v4'
```

## Integration with Makefile

The test suite is integrated into the Makefile:

```bash
# Run all tests including Docker tests
make all

# Run only Docker tests
make docker-test

# Run Docker tests with build
make docker-test
```

## Troubleshooting

### Common Issues

1. **Docker not running**

   ```
   Error: Cannot connect to the Docker daemon
   ```

   Solution: Start Docker service

2. **Image not found**

   ```
   Error: No such image: get-action-version-number:2025-08-02-1d0b205
   ```

   Solution: Build the image first with `make build`

3. **Permission denied**

   ```
   Permission denied: ./test_docker.sh
   ```

   Solution: Make script executable with `chmod +x test_docker.sh`

4. **JSON validation fails**

   ```
   Expected: Valid JSON
   ```

   Solution: Ensure Python 3 is installed for JSON validation

### Debug Mode

To see detailed output, run with bash debug:

```bash
bash -x ./test_docker.sh
```

## Extending the Test Suite

### Adding New Tests

1. Create a new test function:

   ```bash
   test_new_feature() {
       run_test \
           "New Feature" \
           "docker run --rm $IMAGE_NAME 'new-command'" \
           "expected_pattern" \
           "Description of the test"
   }
   ```

2. Add the test to the main function:

   ```bash
   main() {
       # ... existing setup ...

       test_new_feature

       # ... existing tests ...
   }
   ```

### Test Categories

- **Functionality Tests**: Core features and commands
- **Input Tests**: Different input methods (file, stdin, pipe)
- **Output Tests**: Standard and JSON output formats
- **Error Tests**: Error handling and edge cases
- **Authentication Tests**: GitHub token functionality

## Best Practices

1. **Use descriptive test names** that clearly indicate what is being tested
2. **Include error testing** for all error conditions
3. **Test both success and failure scenarios**
4. **Use appropriate patterns** for output validation
5. **Clean up resources** in the cleanup function
6. **Provide clear error messages** when tests fail
7. **Test all input methods** (file, stdin, pipe, workflow)
8. **Test all output formats** (standard, JSON)

## Conclusion

The Docker test suite provides comprehensive testing of the packaged application, ensuring that all functionality works correctly in the containerized environment. The suite covers:

- ✅ **Core functionality** - All main features
- ✅ **Input methods** - File, stdin, pipe, workflow
- ✅ **Output formats** - Standard and JSON
- ✅ **Error handling** - Invalid inputs and edge cases
- ✅ **Authentication** - GitHub token support
- ✅ **Integration** - End-to-end functionality

The test suite serves as a quality gate for the Docker container and ensures reliable deployment.
