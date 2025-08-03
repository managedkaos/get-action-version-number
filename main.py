#!/usr/bin/env python3
"""
GitHub Action Version Lookup Script

This script takes as input either a string describing an action (e.g., actions/checkout@v4)
or a file containing one action per line and looks up the most recent version of each action
using the GitHub API.
"""

import argparse
import os
import re
import sys
from typing import List, Optional, Tuple

import requests
import time


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
    if action_string.startswith('uses:'):
        action_string = action_string[5:].strip()

    # Pattern to match owner/repo@version or owner/repo
    pattern = r'^([^@]+)(?:@(.+))?$'
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
        "X-GitHub-Api-Version": "2022-11-28"
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
                retry_after = int(response.headers.get('Retry-After', base_delay * (2 ** attempt)))
                print(f"Rate limited for {repo}. Retrying in {retry_after} seconds...", file=sys.stderr)
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
            latest_release = max(published_releases, key=lambda x: x.get("published_at", ""))

            return latest_release.get("tag_name")

        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(f"Error fetching releases for {repo} (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {delay} seconds...", file=sys.stderr)
                time.sleep(delay)
            else:
                print(f"Error fetching releases for {repo} after {max_retries} attempts: {e}", file=sys.stderr)
                return None

    return None


def process_action(action_string: str, github_token: Optional[str] = None) -> str:
    """
    Process a single action string and return the latest version.

    Args:
        action_string: Action string to process
        github_token: Optional GitHub token for authenticated requests

    Returns:
        Formatted string with the action and its latest version
    """
    try:
        repo, current_version = parse_action_string(action_string)
        latest_version = get_latest_release(repo, github_token)

        if latest_version:
            if current_version:
                return f"{repo}@{current_version} -> {repo}@{latest_version}"
            else:
                return f"{repo} -> {repo}@{latest_version}"
        else:
            return f"{repo}@{current_version} -> No releases found"

    except ValueError as e:
        return f"Error: {e}"


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
  %(prog)s -f actions.txt --token YOUR_GITHUB_TOKEN
        """,
    )

    parser.add_argument(
        "action",
        nargs="?",
        help="Action string in format 'owner/repo@version' or 'owner/repo'",
    )

    parser.add_argument("-f", "--file", help="File containing one action per line")

    parser.add_argument(
        "--token", help="GitHub token for authenticated requests (optional)"
    )

    args = parser.parse_args()

    # Get GitHub token from environment variable if not provided
    github_token = args.token or os.getenv("GITHUB_TOKEN")

    if args.file:
        # Process file
        results = process_file(args.file, github_token)
    elif args.action:
        # Process single action
        result = process_action(args.action, github_token)
        print(result)
    else:
        # If no arguments provided, read from stdin
        print("Enter action strings (one per line, Ctrl+D to finish):")
        try:
            for line in sys.stdin:
                line = line.strip()
                if line:
                    result = process_action(line, github_token)
                    print(result)
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(1)


if __name__ == "__main__":
    main()
