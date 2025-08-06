"""
Unit tests for GitHub Action Version Lookup Script
"""

import unittest
from io import StringIO
from unittest.mock import MagicMock, mock_open, patch

import requests

from main import (
    extract_actions_from_workflow,
    get_latest_release,
    is_input_piped,
    is_local_workflow_reference,
    parse_action_string,
    process_action,
    process_action_for_json,
    process_file,
    process_file_json,
    process_stdin,
    process_workflow,
    process_workflow_json,
)


class TestIsLocalWorkflowReference(unittest.TestCase):
    """Test the is_local_workflow_reference function"""

    def test_local_workflow_reference_with_dot_slash(self):
        """Test local workflow reference starting with ./"""
        self.assertTrue(
            is_local_workflow_reference("./.github/workflows/integrate-python-app.yml")
        )

    def test_local_workflow_reference_with_dot_dot_slash(self):
        """Test local workflow reference starting with ../"""
        self.assertTrue(is_local_workflow_reference("../workflows/deploy.yml"))

    def test_github_action_not_local(self):
        """Test that GitHub actions are not identified as local"""
        self.assertFalse(is_local_workflow_reference("actions/checkout@v4"))
        self.assertFalse(is_local_workflow_reference("actions/setup-python"))
        self.assertFalse(is_local_workflow_reference("docker/build-push-action@v5"))

    def test_empty_string(self):
        """Test empty string"""
        self.assertFalse(is_local_workflow_reference(""))

    def test_whitespace_only(self):
        """Test whitespace only string"""
        self.assertFalse(is_local_workflow_reference("   "))


class TestParseActionString(unittest.TestCase):
    """Test the parse_action_string function"""

    def test_action_with_version(self):
        """Test parsing action with version"""
        action = "actions/checkout@v4"
        repo, version = parse_action_string(action)
        self.assertEqual(repo, "actions/checkout")
        self.assertEqual(version, "v4")

    def test_action_without_version(self):
        """Test parsing action without version"""
        action = "actions/setup-python"
        repo, version = parse_action_string(action)
        self.assertEqual(repo, "actions/setup-python")
        self.assertIsNone(version)

    def test_action_with_uses_prefix(self):
        """Test parsing action with 'uses:' prefix"""
        action = "uses: actions/checkout@v4"
        repo, version = parse_action_string(action)
        self.assertEqual(repo, "actions/checkout")
        self.assertEqual(version, "v4")

    def test_action_with_uses_prefix_no_version(self):
        """Test parsing action with 'uses:' prefix but no version"""
        action = "uses: actions/setup-python"
        repo, version = parse_action_string(action)
        self.assertEqual(repo, "actions/setup-python")
        self.assertIsNone(version)

    def test_action_with_whitespace(self):
        """Test parsing action with extra whitespace"""
        action = "  actions/checkout@v4  "
        repo, version = parse_action_string(action)
        self.assertEqual(repo, "actions/checkout")
        self.assertEqual(version, "v4")

    def test_invalid_action_format(self):
        """Test parsing invalid action format"""
        # Test with a format that should raise ValueError
        action = "@invalid"
        with self.assertRaises(ValueError):
            parse_action_string(action)

    def test_local_workflow_reference_raises_error(self):
        """Test that local workflow references raise ValueError"""
        local_refs = [
            "./.github/workflows/integrate-python-app.yml",
            "../workflows/deploy.yml",
            "uses: ./.github/workflows/local-workflow.yml",
            "uses: ../workflows/another-workflow.yml",
        ]

        for local_ref in local_refs:
            with self.assertRaises(ValueError) as context:
                parse_action_string(local_ref)
            self.assertIn(
                "Local workflow reference not supported", str(context.exception)
            )

    def test_invalid_action_returns_no_releases(self):
        """Test that invalid actions return 'No releases found'"""
        result = process_action("invalid-action")
        self.assertEqual(result, "No releases found")

    def test_empty_action(self):
        """Test parsing empty action"""
        action = ""
        with self.assertRaises(ValueError):
            parse_action_string(action)


class TestGetLatestRelease(unittest.TestCase):
    """Test the get_latest_release function"""

    @patch("main.requests.get")
    def test_successful_release_fetch(self, mock_get):
        """Test successful release fetch"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "tag_name": "v4.2.2",
                "draft": False,
                "published_at": "2023-01-01T00:00:00Z",
            },
            {
                "tag_name": "v4.1.0",
                "draft": False,
                "published_at": "2022-12-01T00:00:00Z",
            },
        ]
        mock_get.return_value = mock_response

        result = get_latest_release("actions/checkout")
        self.assertEqual(result, "v4.2.2")

    @patch("main.requests.get")
    def test_no_releases_found(self, mock_get):
        """Test when no releases are found"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        result = get_latest_release("actions/checkout")
        self.assertIsNone(result)

    @patch("main.requests.get")
    def test_draft_releases_filtered(self, mock_get):
        """Test that draft releases are filtered out"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "tag_name": "v4.2.2",
                "draft": True,
                "published_at": "2023-01-01T00:00:00Z",
            },
            {
                "tag_name": "v4.1.0",
                "draft": False,
                "published_at": "2022-12-01T00:00:00Z",
            },
        ]
        mock_get.return_value = mock_response

        result = get_latest_release("actions/checkout")
        self.assertEqual(result, "v4.1.0")

    @patch("main.requests.get")
    def test_rate_limiting_handling(self, mock_get):
        """Test rate limiting handling"""
        # First call returns 429, second call succeeds
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.headers = {"Retry-After": "1"}

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = [
            {
                "tag_name": "v4.2.2",
                "draft": False,
                "published_at": "2023-01-01T00:00:00Z",
            }
        ]

        mock_get.side_effect = [mock_response_429, mock_response_success]

        with patch("main.time.sleep"):  # Mock sleep to speed up test
            result = get_latest_release("actions/checkout")
            self.assertEqual(result, "v4.2.2")

    @patch("main.requests.get")
    def test_network_error_handling(self, mock_get):
        """Test network error handling"""
        # Mock the exception to be raised on all attempts
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        # Mock time.sleep to speed up the test
        with patch("main.time.sleep"):
            result = get_latest_release("actions/checkout")
            self.assertIsNone(result)


class TestProcessAction(unittest.TestCase):
    """Test the process_action function"""

    @patch("main.get_latest_release")
    def test_successful_action_processing(self, mock_get_latest):
        """Test successful action processing"""
        mock_get_latest.return_value = "v4.2.2"

        result = process_action("actions/checkout@v4")
        self.assertEqual(result, "actions/checkout@v4.2.2")

    @patch("main.get_latest_release")
    def test_action_without_version(self, mock_get_latest):
        """Test action processing without version"""
        mock_get_latest.return_value = "v5.6.0"

        result = process_action("actions/setup-python")
        self.assertEqual(result, "actions/setup-python@v5.6.0")

    @patch("main.get_latest_release")
    def test_no_releases_found(self, mock_get_latest):
        """Test when no releases are found"""
        mock_get_latest.return_value = None

        result = process_action("actions/checkout@v4")
        self.assertEqual(result, "No releases found")

    def test_invalid_action_format(self):
        """Test invalid action format"""
        result = process_action("invalid-action")
        self.assertEqual(result, "No releases found")


class TestProcessActionForJson(unittest.TestCase):
    """Test the process_action_for_json function"""

    @patch("main.get_latest_release")
    def test_successful_action_processing(self, mock_get_latest):
        """Test successful action processing for JSON"""
        mock_get_latest.return_value = "v4.2.2"

        original, latest = process_action_for_json("actions/checkout@v4")
        self.assertEqual(original, "actions/checkout@v4")
        self.assertEqual(latest, "actions/checkout@v4.2.2")

    @patch("main.get_latest_release")
    def test_action_without_version(self, mock_get_latest):
        """Test action processing without version for JSON"""
        mock_get_latest.return_value = "v5.6.0"

        original, latest = process_action_for_json("actions/setup-python")
        self.assertEqual(original, "actions/setup-python")
        self.assertEqual(latest, "actions/setup-python@v5.6.0")

    def test_invalid_action_format(self):
        """Test invalid action format for JSON"""
        original, latest = process_action_for_json("invalid-action")
        self.assertEqual(original, "invalid-action")
        self.assertEqual(latest, "No releases found")


class TestProcessFile(unittest.TestCase):
    """Test the process_file function"""

    def test_successful_file_processing(self):
        """Test successful file processing"""
        file_content = """actions/checkout@v4
actions/setup-python@v5
# This is a comment
docker/build-push-action@v5
"""

        with patch("builtins.open", mock_open(read_data=file_content)):
            with patch("main.process_action") as mock_process:
                mock_process.side_effect = [
                    "actions/checkout@v4.2.2",
                    "actions/setup-python@v5.6.0",
                    "docker/build-push-action@v6.18.0",
                ]

                results = process_file("test.txt")
                self.assertEqual(len(results), 3)
                self.assertIn("actions/checkout@v4.2.2", results[0])
                self.assertIn("actions/setup-python@v5.6.0", results[1])
                self.assertIn("docker/build-push-action@v6.18.0", results[2])

    def test_file_not_found(self):
        """Test file not found handling"""
        with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
            results = process_file("nonexistent.txt")
            self.assertEqual(len(results), 1)
            self.assertIn("Error: File 'nonexistent.txt' not found", results[0])


class TestProcessFileJson(unittest.TestCase):
    """Test the process_file_json function"""

    def test_successful_file_processing_json(self):
        """Test successful file processing with JSON output"""
        file_content = """actions/checkout@v4
actions/setup-python@v5
# This is a comment
docker/build-push-action@v5
"""

        with patch("builtins.open", mock_open(read_data=file_content)):
            with patch("main.process_action_for_json") as mock_process:
                mock_process.side_effect = [
                    ("actions/checkout@v4", "actions/checkout@v4.2.2"),
                    ("actions/setup-python@v5", "actions/setup-python@v5.6.0"),
                    ("docker/build-push-action@v5", "docker/build-push-action@v6.18.0"),
                ]

                results = process_file_json("test.txt")
                self.assertEqual(len(results), 3)
                self.assertEqual(
                    results["actions/checkout@v4"], "actions/checkout@v4.2.2"
                )
                self.assertEqual(
                    results["actions/setup-python@v5"], "actions/setup-python@v5.6.0"
                )
                self.assertEqual(
                    results["docker/build-push-action@v5"],
                    "docker/build-push-action@v6.18.0",
                )


class TestExtractActionsFromWorkflow(unittest.TestCase):
    """Test the extract_actions_from_workflow function"""

    def test_extract_actions_from_workflow(self):
        """Test extracting actions from workflow file"""
        workflow_content = """
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
"""

        with patch("builtins.open", mock_open(read_data=workflow_content)):
            actions = extract_actions_from_workflow("workflow.yml")
            self.assertEqual(len(actions), 3)
            self.assertIn("uses: actions/checkout@v4", actions)
            self.assertIn("uses: actions/setup-python@v5", actions)
            self.assertIn("uses: docker/build-push-action@v5", actions)

    def test_extract_actions_without_versions(self):
        """Test extracting actions without versions"""
        workflow_content = """
      - name: Checkout code
        uses: actions/checkout

      - name: Set up Python
        uses: actions/setup-python
"""

        with patch("builtins.open", mock_open(read_data=workflow_content)):
            actions = extract_actions_from_workflow("workflow.yml")
            self.assertEqual(len(actions), 2)
            self.assertIn("uses: actions/checkout", actions)
            self.assertIn("uses: actions/setup-python", actions)

    def test_filter_local_workflow_references(self):
        """Test that local workflow references are filtered out"""
        workflow_content = """
name: Test Workflow
on: [push]

jobs:
  integration:
    uses: ./.github/workflows/integrate-python-app.yml
    permissions:
      contents: read

  delivery:
    uses: ./.github/workflows/deliver-container-image.yml
    permissions:
      contents: read

  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5

      - name: Deploy
        uses: ../workflows/deploy-aws-app-runner.yml
"""

        with patch("builtins.open", mock_open(read_data=workflow_content)):
            actions = extract_actions_from_workflow("workflow.yml")
            # Should only extract GitHub actions, not local workflow references
            self.assertEqual(len(actions), 2)
            self.assertIn("uses: actions/checkout@v4", actions)
            self.assertIn("uses: actions/setup-python@v5", actions)

            # Verify local workflow references are NOT included
            self.assertNotIn(
                "uses: ./.github/workflows/integrate-python-app.yml", actions
            )
            self.assertNotIn(
                "uses: ./.github/workflows/deliver-container-image.yml", actions
            )
            self.assertNotIn("uses: ../workflows/deploy-aws-app-runner.yml", actions)

    def test_mixed_workflow_with_local_and_github_actions(self):
        """Test workflow with both local references and GitHub actions"""
        workflow_content = """
name: Mixed Workflow
on: [push]

jobs:
  local-job:
    uses: ./.github/workflows/local-workflow.yml

  github-job:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
"""

        with patch("builtins.open", mock_open(read_data=workflow_content)):
            actions = extract_actions_from_workflow("workflow.yml")
            # Should only extract GitHub actions
            self.assertEqual(len(actions), 2)
            self.assertIn("uses: actions/checkout@v4", actions)
            self.assertIn("uses: actions/setup-python@v4", actions)

            # Verify local workflow reference is NOT included
            self.assertNotIn("uses: ./.github/workflows/local-workflow.yml", actions)

    def test_only_local_workflow_references(self):
        """Test workflow with only local workflow references"""
        workflow_content = """
name: Local Only Workflow
on: [push]

jobs:
  integration:
    uses: ./.github/workflows/integrate-python-app.yml
    permissions:
      contents: read

  delivery:
    uses: ./.github/workflows/deliver-container-image.yml
    permissions:
      contents: read

  deploy-staging:
    uses: ./.github/workflows/deploy-aws-app-runner.yml
    with:
      environment: Staging
    permissions:
      packages: read
    secrets: inherit

  deploy-production:
    uses: ./.github/workflows/deploy-aws-app-runner.yml
    with:
      environment: Production
    permissions:
      packages: read
    secrets: inherit
"""

        with patch("builtins.open", mock_open(read_data=workflow_content)):
            actions = extract_actions_from_workflow("workflow.yml")
            # Should return empty list since all are local workflow references
            self.assertEqual(len(actions), 0)

    def test_file_not_found(self):
        """Test workflow file not found"""
        with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
            actions = extract_actions_from_workflow("nonexistent.yml")
            self.assertEqual(len(actions), 0)


class TestProcessWorkflow(unittest.TestCase):
    """Test the process_workflow function"""

    @patch("main.extract_actions_from_workflow")
    @patch("main.process_action")
    def test_successful_workflow_processing(self, mock_process, mock_extract):
        """Test successful workflow processing"""
        mock_extract.return_value = [
            "uses: actions/checkout@v4",
            "uses: actions/setup-python@v5",
        ]
        mock_process.side_effect = [
            "actions/checkout@v4.2.2",
            "actions/setup-python@v5.6.0",
        ]

        results = process_workflow("workflow.yml")
        self.assertEqual(len(results), 2)
        self.assertIn("actions/checkout@v4.2.2", results[0])
        self.assertIn("actions/setup-python@v5.6.0", results[1])

    @patch("main.extract_actions_from_workflow")
    def test_no_actions_found(self, mock_extract):
        """Test when no actions are found in workflow"""
        mock_extract.return_value = []

        results = process_workflow("workflow.yml")
        self.assertEqual(len(results), 1)
        self.assertIn("No actions found in workflow file", results[0])

    @patch("main.extract_actions_from_workflow")
    @patch("main.process_action")
    def test_workflow_with_only_local_references(self, mock_process, mock_extract):
        """Test workflow processing when only local workflow references are found"""
        # Simulate a workflow with only local workflow references
        mock_extract.return_value = []  # No GitHub actions found

        results = process_workflow("workflow.yml")
        self.assertEqual(len(results), 1)
        self.assertIn("No actions found in workflow file", results[0])

        # Verify that process_action was not called since no actions were extracted
        mock_process.assert_not_called()


class TestProcessWorkflowJson(unittest.TestCase):
    """Test the process_workflow_json function"""

    @patch("main.extract_actions_from_workflow")
    @patch("main.process_action_for_json")
    def test_successful_workflow_processing_json(self, mock_process, mock_extract):
        """Test successful workflow processing with JSON output"""
        mock_extract.return_value = [
            "uses: actions/checkout@v4",
            "uses: actions/setup-python@v5",
        ]
        mock_process.side_effect = [
            ("actions/checkout@v4", "actions/checkout@v4.2.2"),
            ("actions/setup-python@v5", "actions/setup-python@v5.6.0"),
        ]

        results = process_workflow_json("workflow.yml")
        self.assertEqual(len(results), 2)
        self.assertEqual(results["actions/checkout@v4"], "actions/checkout@v4.2.2")
        self.assertEqual(
            results["actions/setup-python@v5"], "actions/setup-python@v5.6.0"
        )

    @patch("main.extract_actions_from_workflow")
    @patch("main.process_action_for_json")
    def test_workflow_json_with_only_local_references(self, mock_process, mock_extract):
        """Test workflow JSON processing when only local workflow references are found"""
        # Simulate a workflow with only local workflow references
        mock_extract.return_value = []  # No GitHub actions found

        results = process_workflow_json("workflow.yml")
        self.assertEqual(len(results), 1)
        self.assertIn("error", results)
        self.assertIn("No actions found in workflow file", results["error"])

        # Verify that process_action_for_json was not called since no actions were extracted
        mock_process.assert_not_called()


class TestProcessStdin(unittest.TestCase):
    """Test the process_stdin function"""

    @patch("sys.stdin", StringIO("actions/checkout@v4\nactions/setup-python\n"))
    @patch("main.process_action")
    def test_stdin_processing(self, mock_process):
        """Test stdin processing"""
        mock_process.side_effect = [
            "actions/checkout@v4.2.2",
            "actions/setup-python@v5.6.0",
        ]

        with patch("builtins.print") as mock_print:
            process_stdin()
            # Check that print was called for the prompt + each result
            self.assertEqual(mock_print.call_count, 3)  # 1 for prompt + 2 for results

    @patch("sys.stdin", StringIO("actions/checkout@v4\nactions/setup-python\n"))
    @patch("main.process_action_for_json")
    def test_stdin_processing_json(self, mock_process):
        """Test stdin processing with JSON output"""
        mock_process.side_effect = [
            ("actions/checkout@v4", "actions/checkout@v4.2.2"),
            ("actions/setup-python", "actions/setup-python@v5.6.0"),
        ]

        with patch("builtins.print") as mock_print:
            process_stdin(json_output=True)
            # Check that print was called for the prompt + JSON output
            self.assertEqual(mock_print.call_count, 2)  # 1 for prompt + 1 for JSON


class TestIsInputPiped(unittest.TestCase):
    """Test the is_input_piped function"""

    @patch("sys.stdin.isatty")
    def test_piped_input(self, mock_isatty):
        """Test detection of piped input"""
        mock_isatty.return_value = False
        self.assertTrue(is_input_piped())

    @patch("sys.stdin.isatty")
    def test_terminal_input(self, mock_isatty):
        """Test detection of terminal input"""
        mock_isatty.return_value = True
        self.assertFalse(is_input_piped())


class TestIntegration(unittest.TestCase):
    """Integration tests"""

    def test_parse_and_process_workflow(self):
        """Test parsing and processing a workflow file"""
        workflow_content = """
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
"""

        with patch("builtins.open", mock_open(read_data=workflow_content)):
            actions = extract_actions_from_workflow("workflow.yml")
            self.assertEqual(len(actions), 2)

            # Test parsing each action
            for action in actions:
                repo, version = parse_action_string(action)
                self.assertIsNotNone(repo)
                # Version might be None for some actions


if __name__ == "__main__":
    unittest.main()
