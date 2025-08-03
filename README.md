# GitHub Action Version Lookup

A Python script that looks up the latest version of GitHub Actions using the GitHub API.

## Features

- Look up the latest version of a single GitHub Action
- Process multiple actions from a file
- Support for both authenticated and unauthenticated API requests
- Handles various action formats (with or without version)
- Provides clear output showing current vs latest versions

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

```
actions/checkout@v4 -> actions/checkout@v4
```

### Action without Version

Look up the latest version when no version is specified:

```bash
python main.py "actions/setup-python"
```

Output:

```
actions/setup-python -> actions/setup-python@v5
```

### Process File

Process multiple actions from a file (one per line):

```bash
python main.py -f actions.txt
```

### Authenticated Requests

For better rate limits and access to private repositories, use a GitHub token:

```bash
# Using command line argument
python main.py "actions/checkout@v4" --token YOUR_GITHUB_TOKEN

# Using environment variable
export GITHUB_TOKEN=your_token_here
python main.py "actions/checkout@v4"
```

### Interactive Mode

Run without arguments to enter interactive mode:

```bash
python main.py
```

Then enter action strings one per line (Ctrl+D to finish).

## Input Format

The script accepts action strings in these formats:

- `owner/repo@version` (e.g., `actions/checkout@v4`)
- `owner/repo` (e.g., `actions/setup-python`)

## Output Format

The script outputs results in these formats:

- `owner/repo@current -> owner/repo@latest` (when current version is specified)
- `owner/repo -> owner/repo@latest` (when no version is specified)
- `owner/repo@current -> No releases found` (when no releases are found)

## File Processing

When processing a file, the script:

- Skips empty lines
- Skips lines starting with `#` (comments)
- Shows line numbers for each result
- Continues processing even if some actions fail

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
actions/checkout@v4 -> actions/checkout@v4
```

### Example 2: File Processing

```bash
$ python main.py -f actions.txt
Line 1: actions/checkout@v4 -> actions/checkout@v4
Line 2: actions/setup-python -> actions/setup-python@v5
Line 3: docker/build-push-action@v5 -> docker/build-push-action@v6
```

### Example 3: Interactive Mode

```bash
$ python main.py
Enter action strings (one per line, Ctrl+D to finish):
actions/checkout@v4
actions/setup-python
actions/checkout@v4 -> actions/checkout@v4
actions/setup-python -> actions/setup-python@v5
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

This project is licensed under the MIT License - see the LICENSE file for details.
