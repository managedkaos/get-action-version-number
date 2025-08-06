#!/usr/bin/env python3
"""
GitHub Action Version Lookup Script

This script takes as input either a string describing an action (e.g., actions/checkout@v4)
or a file containing one action per line and looks up the most recent version of each action
using the GitHub API.
"""

import argparse
import json
import os
import re
import sys
import time
from typing import List, Optional, Tuple

import requests


def parse_action_string(action_string: str) -> Tuple[str, Optional[str]]:
    """
    Parse an action string to extract the repository and version.

    Args:
        action_string: Action string in format 'owner/repo@version' or 'owner/repo'
                     Can also include 'uses:' prefix

    Returns:
        Tuple of (repository, version) where version can be None
    """
    # Remove any leading/trailing whitespace
    action_string = action_string.strip()

    # Remove 'uses:' prefix if present
    if action_string.startswith("uses:"):
        action_string = action_string[5:].strip()

    # Check for local workflow references
    if is_local_workflow_reference(action_string):
        raise ValueError(f"Local workflow reference not supported: {action_string}")

    # Pattern to match owner/repo@version or owner/repo
    pattern = r"^([^@]+)(?:@(.+))?$"
    match = re.match(pattern, action_string)

    if not match:
        raise ValueError(f"Invalid action format: {action_string}")

    repo = match.group(1)
    version = match.group(2) if match.group(2) else None

    return repo, version


def get_latest_release(repo: str, github_token: Optional[str] = None) -> Optional[str]:
    """
    Get the latest release version for a GitHub repository.

    Args:
        repo: Repository in format 'owner/repo'
        github_token: Optional GitHub token for authenticated requests

    Returns:
        Latest release version or None if no releases found
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    url = f"https://api.github.com/repos/{repo}/releases"

    # Retry logic for rate limiting
    max_retries = 3
    base_delay = 1

    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(
                    response.headers.get("Retry-After", base_delay * (2**attempt))
                )
                print(
                    f"Rate limited for {repo}. Retrying in {retry_after} seconds...",
                    file=sys.stderr,
                )
                time.sleep(retry_after)
                continue

            response.raise_for_status()

            releases = response.json()

            if not releases:
                return None

            # Filter out draft releases and get the most recent published release
            published_releases = [r for r in releases if not r.get("draft", False)]

            if not published_releases:
                return None

            # Sort by published_at date and get the most recent
            latest_release = max(
                published_releases, key=lambda x: x.get("published_at", "")
            )

            return latest_release.get("tag_name")

        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt)
                print(
                    f"Error fetching releases for {repo} (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {delay} seconds...",
                    file=sys.stderr,
                )
                time.sleep(delay)
            else:
                print(
                    f"Error fetching releases for {repo} after {max_retries} attempts: {e}",
                    file=sys.stderr,
                )
                return None

    return None


def process_action(action_string: str, github_token: Optional[str] = None) -> str:
    """
    Process a single action string and return the latest version.

    Args:
        action_string: Action string to process
        github_token: Optional GitHub token for authenticated requests

    Returns:
        Latest version string or error message
    """
    try:
        repo, current_version = parse_action_string(action_string)
        latest_version = get_latest_release(repo, github_token)

        if latest_version:
            return f"{repo}@{latest_version}"
        else:
            return "No releases found"

    except ValueError as e:
        return f"Error: {e}"


def process_action_for_json(
    action_string: str, github_token: Optional[str] = None
) -> Tuple[str, str]:
    """
    Process a single action string and return the original action and latest version.

    Args:
        action_string: Action string to process
        github_token: Optional GitHub token for authenticated requests

    Returns:
        Tuple of (original_action, latest_version)
    """
    try:
        repo, current_version = parse_action_string(action_string)
        latest_version = get_latest_release(repo, github_token)

        # Reconstruct the original action string
        original_action = action_string.strip()
        if current_version:
            original_action = f"{repo}@{current_version}"
        else:
            original_action = repo

        if latest_version:
            return original_action, f"{repo}@{latest_version}"
        else:
            return original_action, "No releases found"

    except ValueError as e:
        return action_string.strip(), f"Error: {e}"


def process_file(file_path: str, github_token: Optional[str] = None) -> List[str]:
    """
    Process a file containing one action per line.

    Args:
        file_path: Path to the file containing actions
        github_token: Optional GitHub token for authenticated requests

    Returns:
        List of formatted results
    """
    results = []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                if line and not line.startswith("#"):  # Skip empty lines and comments
                    result = process_action(line, github_token)
                    print(f"{result}")
                    results.append(f"{result}")
    except FileNotFoundError:
        results.append(f"Error: File '{file_path}' not found")
    except Exception as e:
        results.append(f"Error reading file: {e}")

    return results


def process_file_json(file_path: str, github_token: Optional[str] = None) -> dict:
    """
    Process a file containing one action per line and return JSON format.

    Args:
        file_path: Path to the file containing actions
        github_token: Optional GitHub token for authenticated requests

    Returns:
        Dictionary with action as key and latest version as value
    """
    results = {}

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                if line and not line.startswith("#"):  # Skip empty lines and comments
                    original_action, latest_version = process_action_for_json(
                        line, github_token
                    )
                    results[original_action] = latest_version
    except FileNotFoundError:
        results["error"] = f"File '{file_path}' not found"
    except Exception as e:
        results["error"] = f"Error reading file: {e}"

    return results


def is_local_workflow_reference(action: str) -> bool:
    """
    Check if an action string is a local workflow reference.

    Args:
        action: Action string to check

    Returns:
        True if it's a local workflow reference, False otherwise
    """
    return action.startswith("./") or action.startswith("../")


def extract_actions_from_workflow(workflow_file: str) -> List[str]:
    """
    Extract action strings from a GitHub workflow file.

    Note: Local workflow references (those starting with ./ or ../) are filtered out
    as they cannot be versioned through GitHub releases.

    Args:
        workflow_file: Path to the workflow file

    Returns:
        List of action strings found in the workflow
    """
    actions = []

    try:
        # Read the workflow file as text to use regex
        with open(workflow_file, "r", encoding="utf-8") as file:
            content = file.read()

        # Pattern to match "uses: owner/repo@version" or "uses: owner/repo"
        # This pattern handles multi-line and single-line uses statements
        pattern = r"uses:\s*([^@\s]+(?:@[^\s]+)?)"

        matches = re.findall(pattern, content)

        for match in matches:
            # Clean up the match
            action = match.strip()

            # Skip local workflow references (those starting with ./ or ../)
            if is_local_workflow_reference(action):
                continue

            # Skip if empty after stripping
            if action:
                actions.append(f"uses: {action}")

        return actions

    except FileNotFoundError:
        print(f"Error: Workflow file '{workflow_file}' not found", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Error reading workflow file: {e}", file=sys.stderr)
        return []


def process_workflow(
    workflow_file: str, github_token: Optional[str] = None
) -> List[str]:
    """
    Process a workflow file and return results for all actions found.

    Args:
        workflow_file: Path to the workflow file
        github_token: Optional GitHub token for authenticated requests

    Returns:
        List of formatted results
    """
    actions = extract_actions_from_workflow(workflow_file)
    results = []

    if not actions:
        results.append("No actions found in workflow file")
        return results

    for action in actions:
        result = process_action(action, github_token)
        results.append(result)

    return results


def process_workflow_json(
    workflow_file: str, github_token: Optional[str] = None
) -> dict:
    """
    Process a workflow file and return JSON results for all actions found.

    Args:
        workflow_file: Path to the workflow file
        github_token: Optional GitHub token for authenticated requests

    Returns:
        Dictionary with action as key and latest version as value
    """
    actions = extract_actions_from_workflow(workflow_file)
    results = {}

    if not actions:
        results["error"] = "No actions found in workflow file"
        return results

    for action in actions:
        original_action, latest_version = process_action_for_json(action, github_token)
        results[original_action] = latest_version

    return results


def process_stdin(
    github_token: Optional[str] = None, json_output: bool = False
) -> None:
    """
    Process action strings from stdin.
    TODO: Need to check the format of each line as its entered before processing.  Malformed lines should _not_ be used for requests.

    Args:
        github_token: Optional GitHub token for authenticated requests
        json_output: Whether to output in JSON format
    """
    print("Enter action strings (one per line, Ctrl+D to finish):")
    try:
        if json_output:
            results = {}
            for line in sys.stdin:
                line = line.strip()
                if line:
                    original_action, latest_version = process_action_for_json(
                        line, github_token
                    )
                    results[original_action] = latest_version
            print(json.dumps(results, indent=2))
        else:
            for line in sys.stdin:
                line = line.strip()
                if line:
                    result = process_action(line, github_token)
                    print(result)
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(1)


def is_input_piped() -> bool:
    """
    Check if input is coming from a pipe (not a terminal).

    Returns:
        True if input is piped, False if it's from a terminal
    """
    return not sys.stdin.isatty()


def main():
    """Main function to handle command line arguments and execute the script."""
    parser = argparse.ArgumentParser(
        description="Look up the latest version of GitHub Actions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "actions/checkout@v4"
  %(prog)s "actions/setup-python"
  %(prog)s -f actions.txt
  %(prog)s -f actions.txt --json
  %(prog)s -w workflow.yml
  %(prog)s -w workflow.yml --json
  %(prog)s -w workflow.yml --token YOUR_GITHUB_TOKEN
  %(prog)s --stdin
  %(prog)s --stdin --json
  echo "actions/checkout@v4" | %(prog)s
  echo "actions/checkout@v4" | %(prog)s --json
        """,
    )

    parser.add_argument(
        "action",
        nargs="?",
        help="Action string in format 'owner/repo@version' or 'owner/repo'",
    )

    parser.add_argument("-f", "--file", help="File containing one action per line")

    parser.add_argument(
        "-w",
        "--workflow",
        help="GitHub workflow file to extract and process actions from",
    )

    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read action strings from stdin (interactive mode)",
    )

    parser.add_argument(
        "--token", help="GitHub token for authenticated requests (optional)"
    )

    parser.add_argument(
        "--json", action="store_true", help="Output results in JSON format"
    )

    args = parser.parse_args()

    # Get GitHub token from environment variable if not provided
    github_token = args.token or os.getenv("GITHUB_TOKEN")

    # Check for piped input first (before checking for no arguments)
    if (
        is_input_piped()
        and not args.action
        and not args.file
        and not args.workflow
        and not args.stdin
    ):
        # Automatically process piped input
        if args.json:
            results = {}
            for line in sys.stdin:
                line = line.strip()
                if line:
                    original_action, latest_version = process_action_for_json(
                        line, github_token
                    )
                    results[original_action] = latest_version
            print(json.dumps(results, indent=2))
        else:
            for line in sys.stdin:
                line = line.strip()
                if line:
                    result = process_action(line, github_token)
                    print(result)
        return

    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    if args.workflow:
        # Process workflow file
        if args.json:
            results = process_workflow_json(args.workflow, github_token)
            print(json.dumps(results, indent=2))
        else:
            results = process_workflow(args.workflow, github_token)
            for result in results:
                print(result)
    elif args.file:
        # Process file
        if args.json:
            results = process_file_json(args.file, github_token)
            print(json.dumps(results, indent=2))
        else:
            results = process_file(args.file, github_token)
    elif args.stdin:
        # Process stdin (interactive mode)
        process_stdin(github_token, args.json)
    elif args.action:
        # Process single action
        if args.json:
            original_action, latest_version = process_action_for_json(
                args.action, github_token
            )
            result = {original_action: latest_version}
            print(json.dumps(result, indent=2))
        else:
            result = process_action(args.action, github_token)
            print(result)
    else:
        # If no specific input method provided, show help
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
