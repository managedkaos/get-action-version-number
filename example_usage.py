#!/usr/bin/env python3
"""
Example usage of the GitHub Action Version Lookup Script

This script demonstrates various ways to use the main script.
"""

import subprocess


def run_command(cmd):
    """Run a command and return the output."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        return None


def main():
    """Demonstrate various usage examples."""
    print("GitHub Action Version Lookup - Usage Examples")
    print("=" * 50)

    # Example 1: Single action with version
    print("\n1. Single action with version:")
    print("Command: python3 main.py 'actions/checkout@v4'")
    result = run_command("python3 main.py 'actions/checkout@v4'")
    if result:
        print(f"Output: {result}")

    # Example 2: Single action without version
    print("\n2. Single action without version:")
    print("Command: python3 main.py 'actions/setup-python'")
    result = run_command("python3 main.py 'actions/setup-python'")
    if result:
        print(f"Output: {result}")

    # Example 3: Action with 'uses:' prefix
    print("\n3. Action with 'uses:' prefix:")
    print("Command: python3 main.py 'uses: actions/checkout@v4'")
    result = run_command("python3 main.py 'uses: actions/checkout@v4'")
    if result:
        print(f"Output: {result}")

    # Example 4: Process file
    print("\n4. Process actions from file:")
    print("Command: python3 main.py -f actions.txt")
    result = run_command("python3 main.py -f actions.txt | head -5")
    if result:
        print("Output (first 5 lines):")
        for line in result.split("\n"):
            print(f"  {line}")

    # Example 5: Show help
    print("\n5. Help information:")
    print("Command: python3 main.py --help")
    result = run_command("python3 main.py --help")
    if result:
        print("Help output:")
        for line in result.split("\n")[:10]:  # Show first 10 lines
            print(f"  {line}")
        print("  ...")

    print("\n" + "=" * 50)
    print("Note: To use with real GitHub API, install requests:")
    print("pip install requests")
    print("\nFor authenticated requests, set GITHUB_TOKEN environment variable:")
    print("export GITHUB_TOKEN=your_token_here")


if __name__ == "__main__":
    main()
