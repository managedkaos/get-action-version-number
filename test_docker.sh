#!/bin/bash

# Docker Test Suite for GitHub Action Version Lookup Script
# This script tests the Docker container with various scenarios

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="get-action-version-number:2025-08-02-1d0b205"
CONTAINER_NAME="test-action-lookup"
TEST_DIR="/tmp/action-lookup-test"
RESULTS_FILE="$TEST_DIR/test-results.txt"

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "PASS")
            echo -e "${GREEN}✓ PASS${NC}: $message"
            ;;
        "FAIL")
            echo -e "${RED}✗ FAIL${NC}: $message"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ INFO${NC}: $message"
            ;;
        "WARN")
            echo -e "${YELLOW}⚠ WARN${NC}: $message"
            ;;
    esac
}

# Function to run a test
run_test() {
    local test_name="$1"
    local command="$2"
    local expected_pattern="$3"
    local description="$4"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    print_status "INFO" "Running: $test_name"
    print_status "INFO" "Description: $description"

    # Run the command and capture output
    local output
    local exit_code
    output=$(eval "$command" 2>&1)
    exit_code=$?

    # Check if command succeeded and output matches expected pattern
    if [ $exit_code -eq 0 ] && echo "$output" | grep -q "$expected_pattern"; then
        print_status "PASS" "$test_name"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        print_status "FAIL" "$test_name"
        print_status "FAIL" "Exit code: $exit_code"
        print_status "FAIL" "Output: $output"
        print_status "FAIL" "Expected pattern: $expected_pattern"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# Function to run a test with JSON output
run_json_test() {
    local test_name="$1"
    local command="$2"
    local description="$3"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    print_status "INFO" "Running: $test_name"
    print_status "INFO" "Description: $description"

    # Run the command and capture output
    local output
    local exit_code
    output=$(eval "$command" 2>&1)
    exit_code=$?

    # Check if command succeeded and output is valid JSON
    if [ $exit_code -eq 0 ] && echo "$output" | python3 -m json.tool >/dev/null 2>&1; then
        print_status "PASS" "$test_name"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        print_status "FAIL" "$test_name"
        print_status "FAIL" "Exit code: $exit_code"
        print_status "FAIL" "Output: $output"
        print_status "FAIL" "Expected: Valid JSON"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# Function to run a test that should fail
run_failure_test() {
    local test_name="$1"
    local command="$2"
    local expected_error_pattern="$3"
    local description="$4"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    print_status "INFO" "Running: $test_name"
    print_status "INFO" "Description: $description"

    # Run the command and capture output
    local output
    local exit_code
    output=$(eval "$command" 2>&1)
    exit_code=$?

    # Check if command failed and output matches expected error pattern
    if [ $exit_code -ne 0 ] && echo "$output" | grep -q "$expected_error_pattern"; then
        print_status "PASS" "$test_name"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        print_status "FAIL" "$test_name"
        print_status "FAIL" "Exit code: $exit_code"
        print_status "FAIL" "Output: $output"
        print_status "FAIL" "Expected error pattern: $expected_error_pattern"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# Setup function
setup() {
    print_status "INFO" "Setting up test environment..."

    # Create test directory
    mkdir -p "$TEST_DIR"

    # Create test files
    cat > "$TEST_DIR/test-actions.txt" << 'EOF'
actions/checkout@v4
actions/setup-python@v5
docker/build-push-action@v5
# This is a comment
actions/setup-go@v5
EOF

    cat > "$TEST_DIR/test-workflow.yml" << 'EOF'
name: Test Workflow
on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.9'

      - name: Build
        uses: docker/build-push-action@v5
EOF

    cat > "$TEST_DIR/empty-file.txt" << 'EOF'
# This file has no actions
EOF

    print_status "INFO" "Test environment setup complete"
}

# Cleanup function
cleanup() {
    print_status "INFO" "Cleaning up test environment..."
    rm -rf "$TEST_DIR"
}

# Test functions
test_help() {
    run_test \
        "Help Command" \
        "docker run --rm -e GITHUB_TOKEN $IMAGE_NAME --help" \
        "Look up the latest version of GitHub Actions" \
        "Test that help command works and shows usage information"
}

test_single_action() {
    run_test \
        "Single Action" \
        "docker run --rm -e GITHUB_TOKEN $IMAGE_NAME 'actions/checkout@v4'" \
        "actions/checkout@" \
        "Test processing a single action with version"
}

test_single_action_json() {
    run_json_test \
        "Single Action JSON" \
        "docker run --rm -e GITHUB_TOKEN $IMAGE_NAME 'actions/checkout@v4' --json" \
        "Test processing a single action with JSON output"
}

test_file_processing() {
    run_test \
        "File Processing" \
        "docker run --rm -e GITHUB_TOKEN -v $TEST_DIR/test-actions.txt:/work/test-actions.txt $IMAGE_NAME --file test-actions.txt" \
        "actions/checkout@" \
        "Test processing actions from a file"
}

test_file_processing_json() {
    run_json_test \
        "File Processing JSON" \
        "docker run --rm -e GITHUB_TOKEN -v $TEST_DIR/test-actions.txt:/work/test-actions.txt $IMAGE_NAME --file test-actions.txt --json" \
        "Test processing actions from a file with JSON output"
}

test_workflow_processing() {
    run_test \
        "Workflow Processing" \
        "docker run --rm -e GITHUB_TOKEN -v $TEST_DIR/test-workflow.yml:/work/test-workflow.yml $IMAGE_NAME --workflow test-workflow.yml" \
        "actions/checkout@" \
        "Test processing actions from a workflow file"
}

test_workflow_processing_json() {
    run_json_test \
        "Workflow Processing JSON" \
        "docker run --rm -e GITHUB_TOKEN -v $TEST_DIR/test-workflow.yml:/work/test-workflow.yml $IMAGE_NAME --workflow test-workflow.yml --json" \
        "Test processing actions from a workflow file with JSON output"
}

test_piped_input() {
    run_test \
        "Piped Input" \
        "echo 'actions/checkout@v4' | docker run --rm -e GITHUB_TOKEN -i $IMAGE_NAME" \
        "actions/checkout@" \
        "Test processing piped input"
}

test_piped_input_json() {
    run_json_test \
        "Piped Input JSON" \
        "echo 'actions/checkout@v4' | docker run --rm -e GITHUB_TOKEN -i $IMAGE_NAME --json" \
        "Test processing piped input with JSON output"
}

test_stdin_mode() {
    run_test \
        "Stdin Mode" \
        "echo -e 'actions/checkout@v4\n' | docker run --rm -e GITHUB_TOKEN -i $IMAGE_NAME --stdin" \
        "actions/checkout@" \
        "Test interactive stdin mode"
}

# TODO: Review and fix this test
# test_stdin_mode_json() {
#     run_json_test \
#         "Stdin Mode JSON" \
#         "echo -e 'actions/checkout@v4\n' | docker run --rm -e GITHUB_TOKEN -i $IMAGE_NAME --stdin --json" \
#         "Test interactive stdin mode with JSON output"
# }

test_invalid_action() {
    run_test \
        "Invalid Action" \
        "docker run --rm -e GITHUB_TOKEN $IMAGE_NAME 'invalid-action'" \
        "No releases found" \
        "Test handling of invalid action format"
}

# test_file_not_found() {
#     run_failure_test \
#         "File Not Found" \
#         "docker run --rm -e GITHUB_TOKEN $IMAGE_NAME --file nonexistent.txt" \
#         "Error: File 'nonexistent.txt' not found" \
#         "Test handling of missing file"
# }

# test_workflow_not_found() {
#     run_failure_test \
#         "Workflow Not Found" \
#         "docker run --rm -e GITHUB_TOKEN $IMAGE_NAME --workflow nonexistent.yml" \
#         "Error: Workflow file 'nonexistent.yml' not found" \
#         "Test handling of missing workflow file"
# }

# test_empty_file() {
#     run_test \
#         "Empty File" \
#         "docker run --rm -e GITHUB_TOKEN -v $TEST_DIR/empty-file.txt:/work/empty-file.txt $IMAGE_NAME --file empty-file.txt" \
#         "No actions found" \
#         "Test handling of file with no actions"
# }

# test_no_arguments() {
#     run_test \
#         "No Arguments" \
#         "docker run --rm -e GITHUB_TOKEN $IMAGE_NAME" \
#         "usage:" \
#         "Test that no arguments shows help"
# }

# test_invalid_argument() {
#     run_failure_test \
#         "Invalid Argument" \
#         "docker run --rm -e GITHUB_TOKEN $IMAGE_NAME --invalid-flag" \
#         "error:" \
#         "Test handling of invalid command line arguments"
# }

test_authentication() {
    if [ -n "$GITHUB_TOKEN" ]; then
        run_test \
            "Authentication" \
            "docker run --rm -e GITHUB_TOKEN $IMAGE_NAME 'actions/checkout@v4'" \
            "actions/checkout@" \
            "Test with GitHub token authentication"
    else
        print_status "WARN" "Skipping authentication test - GITHUB_TOKEN not set"
    fi
}

# Main test runner
main() {
    echo "=========================================="
    echo "Docker Test Suite for Action Lookup Script"
    echo "=========================================="
    echo

    # Setup
    setup

    # Run tests
    echo "Running tests..."
    echo

    test_help
    test_single_action
    test_single_action_json
    test_file_processing
    test_file_processing_json
    test_workflow_processing
    test_workflow_processing_json
    test_piped_input
    test_piped_input_json
    test_stdin_mode
    #test_stdin_mode_json
    test_invalid_action
    #test_file_not_found
    #test_workflow_not_found
    #test_empty_file
    #test_no_arguments
    #test_invalid_argument
    test_authentication

    # Results
    echo
    echo "=========================================="
    echo "Test Results"
    echo "=========================================="
    echo "Total Tests: $TOTAL_TESTS"
    echo "Passed: $PASSED_TESTS"
    echo "Failed: $FAILED_TESTS"

    if [ $FAILED_TESTS -eq 0 ]; then
        print_status "PASS" "All tests passed!"
        exit 0
    else
        print_status "FAIL" "$FAILED_TESTS test(s) failed"
        exit 1
    fi
}

# Cleanup on exit
trap cleanup EXIT

# Run main function
main "$@"
