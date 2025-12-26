# GitHub Extension for InKCre

This extension provides GitHub Stars source functionality for InKCre.

## Features

- Collect starred repositories from GitHub
- Track repository metadata (stars, forks, languages, topics)
- Automatic tracking of processed stars
- Support for incremental updates

## Configuration

The extension requires the following configuration:

- `github_token`: GitHub personal access token for API access
  - Create one at https://github.com/settings/tokens
  - Required scopes: `public_repo` (or `repo` for private starred repos)
- `username`: GitHub username to fetch starred repos for
- `include_private`: Whether to include private repositories (default: `false`)

## Usage

1. Install the extension in the InKCre database
2. Configure GitHub settings with your token and username
3. Create a GitHub Stars source via the API endpoint: `POST /github/stars`
4. Stars will be collected based on the configured schedule

## Dependencies

This extension requires the `PyGithub` package:
```bash
pip install PyGithub
```

## Notes

- The extension tracks the last processed star ID to avoid duplicates
- Repository data includes owner information, description, topics, and statistics
- Respects GitHub API rate limits with built-in delays
- For accessing private starred repositories, ensure your token has appropriate permissions
