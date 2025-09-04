# GitHub Action Version Lookup

[![Build and Push Image](https://github.com/managedkaos/get-action-version-number/actions/workflows/publish-image-to-ghcr.yml/badge.svg)](https://github.com/managedkaos/get-action-version-number/actions/workflows/publish-image-to-ghcr.yml)

A Python-based application that looks up the latest version of GitHub Actions using the GitHub API.

## Features

- Look up the latest version of a single GitHub Action
- Process multiple actions from a file
- Extract and process actions directly from GitHub workflow files
- Update workflow files in place with latest action versions
- Support for both authenticated and unauthenticated API requests
- Handles various action formats (with or without version)
- JSON output format with `--json` flag
- Enhanced text output showing both old and new versions

## Installation

1. Clone this repository
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Single Action

Look up the latest version of a single action:

```bash
python main.py "actions/checkout@v4"
```

Output:

```bash
actions/checkout@v4 -> actions/checkout@v5.0.0
```

### Single Action with JSON Output

Get JSON format with action as key and latest version as value:

```bash
python main.py "actions/checkout@v4" --json
```

Output:

```json
{
  "actions/checkout@v4": "actions/checkout@v4.2.2"
}
```

### Action without Version

Look up the latest version when no version is specified:

```bash
python main.py "actions/setup-python"
```

Output:

```bash
actions/setup-python -> actions/setup-python@v6.0.0
```

### Process File

Process multiple actions from a file (one per line):

```bash
python main.py -f actions.txt
```

### Process File with JSON Output

Get JSON format for file processing:

```bash
python main.py -f actions.txt --json
```

Output:

```json
{
  "actions/checkout@v4": "actions/checkout@v4.2.2",
  "actions/setup-python@v5": "actions/setup-python@v5.6.0",
  "docker/build-push-action@v5": "docker/build-push-action@v6.18.0"
}
```

### Process Workflow File

Extract and process actions directly from a GitHub workflow file:

```bash
python main.py -w workflow.yml
```

Output:

```bash
actions/checkout@v4.2.2
actions/setup-go@v5.5.0
```

### Process Workflow File with JSON Output

Get JSON format for workflow processing:

```bash
python main.py -w workflow.yml --json
```

Output:

```json
{
  "actions/checkout@v4": "actions/checkout@v4.2.2",
  "actions/setup-go@v5.5.0": "actions/setup-go@v5.5.0"
}
```

### Update Workflow File In Place

Update a workflow file directly with the latest action versions:

```bash
python main.py -w workflow.yml --update-in-place
```

This will:

1. Read the workflow file
2. Check each action's current version against the latest available version
3. Update the file with newer versions where available
4. Preserve all other content (comments, formatting, etc.)

Output:

```bash
Updated actions/checkout: v4 -> v5.0.0
Updated actions/setup-python: v5 -> v6.0.0

Workflow file updated successfully. 2 action(s) updated.
```

If no updates are needed:

```bash
No updates needed - all actions are already at their latest versions.
```

**Note**: `--update-in-place` can only be used with `--workflow` and cannot be combined with `--json`.

### Authenticated Requests

For better rate limits and access to private repositories, use a GitHub token:

```bash
# Using command line argument
python main.py "actions/checkout@v4" --token YOUR_GITHUB_TOKEN

# Using environment variable
export GITHUB_TOKEN=your_token_here
python main.py "actions/checkout@v4"

# With JSON output
python main.py "actions/checkout@v4" --json --token YOUR_GITHUB_TOKEN

# With workflow file
python main.py -w workflow.yml --token YOUR_GITHUB_TOKEN

# With workflow file and JSON output
python main.py -w workflow.yml --json --token YOUR_GITHUB_TOKEN

# Update workflow file in place
python main.py -w workflow.yml --update-in-place --token YOUR_GITHUB_TOKEN
```

### Interactive Mode

Run with `--stdin` flag to read from stdin:

```bash
python main.py --stdin
```

Then enter action strings one per line (Ctrl+D to finish).

For JSON output in stdin mode:

```bash
python main.py --stdin --json
```

### Piping Input

You can pipe action strings to the script without any flags - it will automatically detect piped input:

```bash
echo -e "actions/checkout@v4\nactions/setup-python" | python main.py
```

Output:

```bash
actions/checkout@v4 -> actions/checkout@v5.0.0
actions/setup-python -> actions/setup-python@v6.0.0
```

With JSON output:

```bash
echo -e "actions/checkout@v4\nactions/setup-python" | python main.py --json
```

Output:

```json
{
  "actions/checkout@v4": "actions/checkout@v4.2.2",
  "actions/setup-python": "actions/setup-python@v5.6.0"
}
```

**Note**: The `--stdin` flag is only needed for interactive mode (typing at the terminal). Piped input is automatically detected.

## Input Format

The script accepts action strings in these formats:

- `owner/repo@version` (e.g., `actions/checkout@v4`)
- `owner/repo` (e.g., `actions/setup-python`)
- `uses: owner/repo@version` (handles GitHub workflow format)

## Output Format

### Standard Output

The script outputs results in these formats:

- `original_version -> latest_version` (shows both old and new versions)
- `original_version -> No releases found` (when no releases are found)
- `Error: message` (when parsing fails)

### JSON Output

With the `--json` flag, the script outputs:

```json
{
  "original_action": "latest_version",
  "actions/checkout@v4": "actions/checkout@v4.2.2",
  "actions/setup-python": "actions/setup-python@v5.6.0"
}
```

## File Processing

When processing a file, the script:

- Skips empty lines
- Skips lines starting with `#` (comments)
- Continues processing even if some actions fail
- Supports both standard and JSON output formats

## Command Line Options

- `action`: Action string in format 'owner/repo@version' or 'owner/repo'
- `-f, --file`: File containing one action per line
- `-w, --workflow`: GitHub workflow file to extract and process actions from
- `--stdin`: Read action strings from stdin (interactive mode only)
- `--token`: GitHub token for authenticated requests (optional)
- `--json`: Output results in JSON format
- `--update-in-place`: Update workflow file in place with latest action versions (only works with --workflow)
- `-h, --help`: Show help message

## Error Handling

The script handles various error conditions:

- Invalid action format
- Network errors
- Missing files
- GitHub API errors
- Rate limiting (with appropriate delays)

## Examples

### Example 1: Single Action

```bash
$ python main.py "actions/checkout@v4"
actions/checkout@v4 -> actions/checkout@v5.0.0

$ python main.py "actions/checkout@v4" --json
{
  "actions/checkout@v4": "actions/checkout@v5.0.0"
}
```

### Example 2: File Processing

```bash
$ python main.py -f actions.txt
actions/checkout@v4 -> actions/checkout@v5.0.0
actions/setup-python@v5 -> actions/setup-python@v6.0.0
docker/build-push-action@v5 -> docker/build-push-action@v6.18.0

$ python main.py -f actions.txt --json
{
  "actions/checkout@v4": "actions/checkout@v5.0.0",
  "actions/setup-python@v5": "actions/setup-python@v6.0.0",
  "docker/build-push-action@v5": "docker/build-push-action@v6.18.0"
}
```

### Example 3: Workflow File Processing

```bash
$ python main.py -w workflow.yml
actions/checkout@v4 -> actions/checkout@v5.0.0
actions/setup-go@v5.5.0 -> actions/setup-go@v6.0.0

$ python main.py -w workflow.yml --json
{
  "actions/checkout@v4": "actions/checkout@v5.0.0",
  "actions/setup-go@v5.5.0": "actions/setup-go@v6.0.0"
}
```

### Example 4: Update Workflow In Place

```bash
$ python main.py -w workflow.yml --update-in-place
Updated actions/checkout: v4 -> v5.0.0
Updated actions/setup-python: v5 -> v6.0.0

Workflow file updated successfully. 2 action(s) updated.

$ python main.py -w workflow.yml --update-in-place
No updates needed - all actions are already at their latest versions.
```

### Example 5: Interactive Mode

```bash
$ python main.py --stdin
Enter action strings (one per line, Ctrl+D to finish):
actions/checkout@v4
actions/setup-python
actions/checkout@v4 -> actions/checkout@v5.0.0
actions/setup-python -> actions/setup-python@v6.0.0

$ python main.py --stdin --json
Enter action strings (one per line, Ctrl+D to finish):
actions/checkout@v4
actions/setup-python
{
  "actions/checkout@v4": "actions/checkout@v5.0.0",
  "actions/setup-python": "actions/setup-python@v6.0.0"
}
```

### Example 6: Piping Input

```bash
$ echo -e "actions/checkout@v4\nactions/setup-python" | python main.py
actions/checkout@v4 -> actions/checkout@v5.0.0
actions/setup-python -> actions/setup-python@v6.0.0

$ echo -e "actions/checkout@v4\nactions/setup-python" | python main.py --json
{
  "actions/checkout@v4": "actions/checkout@v5.0.0",
  "actions/setup-python": "actions/setup-python@v6.0.0"
}
```

## GitHub Token

To get a GitHub token:

1. Go to GitHub Settings > Developer settings > Personal access tokens
2. Generate a new token with `repo` scope for private repositories
3. Use the token with the `--token` argument or set the `GITHUB_TOKEN` environment variable

## Rate Limiting

- Unauthenticated requests: 60 requests per hour
- Authenticated requests: 5,000 requests per hour

The script will handle rate limiting gracefully and continue processing.

## Dependencies

- `requests>=2.31.0` - For HTTP requests to GitHub API

## License

This project is licensed under the MIT License - [see the LICENSE file for details](./LICENSE).
