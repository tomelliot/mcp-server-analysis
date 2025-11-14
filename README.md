# MCP Server Activity vs Popularity Analysis

A Python tool for analyzing the health of the Model Context Protocol (MCP) ecosystem by visualizing the relationship between repository activity and popularity for all MCP servers in the official registry.

## Overview

This project generates scatter plots that show:
- **X-axis:** Days since most recent commit (repository activity)
- **Y-axis:** GitHub star count (popularity)
- **Data points:** Each MCP server with a GitHub repository

The analysis helps identify which popular servers are actively maintained versus those that may be stale.

## Features

- 📊 **Automated Data Collection**: Fetches all servers from the MCP registry with pagination support
- 🔍 **GitHub Integration**: Retrieves star counts and commit dates via GitHub API
- 📈 **Beautiful Visualizations**: Creates high-resolution scatter plots with seaborn
- ⚡ **Concurrent Processing**: Efficient parallel API requests with rate limiting
- 🎨 **Rich CLI**: User-friendly command-line interface with progress indicators
- 🧪 **Well-Tested**: 73% test coverage with comprehensive unit tests
- 📦 **Type-Safe**: Full type annotations with Pydantic models

## Installation

### Prerequisites

- Python 3.14+
- [uv](https://github.com/astral-sh/uv) for package management

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd mcp-server-analysis
```

2. Create and activate virtual environment:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
uv pip install pandas seaborn matplotlib httpx pydantic typer rich
```

4. (Optional) Install development dependencies:
```bash
uv pip install pytest pytest-asyncio pytest-mock pytest-cov ruff
```

## Usage

### Full Analysis

Run the complete analysis pipeline (fetch data + create visualizations):

```bash
python scripts/analyze_mcp_servers.py analyze
```

This will:
1. Fetch all MCP servers from the registry (~1777 servers)
2. Retrieve GitHub statistics for each repository
3. Save data to `mcp_servers_data.csv`
4. Generate two visualizations:
   - `mcp_activity_vs_popularity.png` - Basic scatter plot
   - `mcp_activity_vs_popularity_enhanced.png` - Enhanced 2x2 grid with distributions

### Custom Options

```bash
# Specify custom output paths
python scripts/analyze_mcp_servers.py analyze \
  --output-csv data/servers.csv \
  --output-plot plots/basic.png \
  --enhanced-plot plots/enhanced.png

# Use log scale for y-axis
python scripts/analyze_mcp_servers.py analyze --log-scale

# Adjust concurrent requests (helps with rate limiting)
python scripts/analyze_mcp_servers.py analyze --max-concurrent 5

# Skip enhanced plot creation
python scripts/analyze_mcp_servers.py analyze --skip-enhanced

# Disable progress indicators
python scripts/analyze_mcp_servers.py analyze --no-progress
```

### Using GitHub Token

To avoid rate limiting, provide a GitHub personal access token:

```bash
# Via environment variable (recommended)
export GITHUB_TOKEN="your_token_here"
python scripts/analyze_mcp_servers.py analyze

# Or via command-line option
python scripts/analyze_mcp_servers.py analyze --github-token "your_token_here"
```

**How to get a GitHub token:**
1. Go to https://github.com/settings/tokens
2. Click "Generate new token" (classic)
3. Select scopes: `public_repo` (read-only access)
4. Copy the generated token

### Refetch Missing Data

If your initial data collection was incomplete (e.g., due to rate limiting or interruption), you can refetch missing GitHub statistics:

```bash
# Refetch only missing data
python scripts/analyze_mcp_servers.py refetch mcp_servers_data.csv

# Save to a different file
python scripts/analyze_mcp_servers.py refetch mcp_servers_data.csv -o updated_data.csv

# Use a GitHub token for better success rate
export GITHUB_TOKEN="your_token_here"
python scripts/analyze_mcp_servers.py refetch mcp_servers_data.csv

# Force refetch all data (even rows with existing stats)
python scripts/analyze_mcp_servers.py refetch mcp_servers_data.csv --force
```

The `refetch` command:
- Loads your existing CSV file
- Identifies rows with missing GitHub stats (null values in `stars` or `days_since_commit`)
- Refetches only the missing data
- Updates the CSV with new statistics
- By default, overwrites the input file (use `-o` to save elsewhere)

### Visualize Existing Data

If you already have collected data, regenerate plots without re-fetching:

```bash
python scripts/analyze_mcp_servers.py visualize mcp_servers_data.csv
```

### Getting Help

```bash
# General help
python scripts/analyze_mcp_servers.py --help

# Command-specific help
python scripts/analyze_mcp_servers.py analyze --help
python scripts/analyze_mcp_servers.py refetch --help
python scripts/analyze_mcp_servers.py visualize --help
```

## Project Structure

```
mcp-server-analysis/
├── src/
│   └── common/
│       └── services/
│           ├── mcp_registry.py      # MCP registry API client
│           ├── github_api.py        # GitHub API client
│           ├── data_processor.py    # Data collection pipeline
│           └── visualization.py     # Plotting functions
├── scripts/
│   └── analyze_mcp_servers.py       # CLI interface
├── tests/
│   ├── test_mcp_registry.py
│   ├── test_github_api.py
│   ├── test_data_processor.py
│   └── test_visualization.py
├── main.py                          # Entry point with usage info
├── pyproject.toml                   # Project metadata & dependencies
└── README.md                        # This file
```

## Architecture

The project follows a layered architecture:

- **Services Layer** (`src/common/services/`): Core business logic for data fetching and processing
- **CLI Layer** (`scripts/`): Thin wrappers that parse inputs and call service functions
- **Tests** (`tests/`): Unit tests with mocked external dependencies

All functions use:
- **Type annotations** with modern `Type | None` syntax
- **Google-style docstrings**
- **Pydantic models** for API response validation
- **Async operations** for concurrent API requests

## Output Files

### CSV Data File

The collected data is saved as a CSV with the following columns:

- `server_name`: MCP server identifier
- `server_version`: Server version
- `github_url`: GitHub repository URL (if available)
- `stars`: Number of GitHub stars
- `days_since_commit`: Days elapsed since last commit
- `last_commit_date`: ISO 8601 timestamp of last commit

### Visualization Files

1. **Basic Scatter Plot**: Shows activity vs popularity with optional log scale
2. **Enhanced Plot**: 2x2 grid including:
   - Linear scale scatter
   - Log scale scatter
   - Star distribution histogram
   - Days since commit histogram

Both saved as high-resolution PNG (300 DPI) suitable for presentations.

## Example Results

Based on recent data collection:

- **Total servers**: 1,777
- **Servers with GitHub repos**: 1,393 (78%)
- **Successfully fetched stats**: ~656 repos (47% without token, higher with token)
- **Mean stars**: ~555
- **Mean days since commit**: ~25 days

Top servers by popularity:
- github/github-mcp-server: 24,478 stars
- ohmyposh/oh-my-posh: 20,603 stars
- anthropics/anthropic-quickstarts: 7,070 stars

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_github_api.py -v
```

Current test coverage: **73%**

## Development

### Code Style

The project uses:
- **Ruff** for linting and formatting
- **Type annotations** on all functions
- **Functional programming** style (avoiding classes where possible)
- **Early returns** and guard clauses for error handling

### Adding New Features

1. Implement service functions in `src/common/services/`
2. Write unit tests in `tests/`
3. Add CLI commands in `scripts/` if needed
4. Update this README

## Troubleshooting

### Rate Limiting

If you encounter GitHub API rate limiting:
- Use a GitHub token (see "Using GitHub Token" section)
- Reduce `--max-concurrent` value (default: 10)
- Wait for rate limit reset (check headers in error messages)

### Empty Results

If no GitHub stats are collected:
- Check internet connection
- Verify GitHub API is accessible
- Try with a smaller dataset first (use `--max-concurrent 1` for debugging)

### Module Import Errors

Ensure you're running from the project root directory:
```bash
cd /path/to/mcp-server-analysis
python scripts/analyze_mcp_servers.py analyze
```

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass (`pytest tests/`)
5. Submit a pull request

## License

[Add your license here]

## Acknowledgments

- [Model Context Protocol (MCP)](https://modelcontextprotocol.io) for the server registry
- GitHub API for repository statistics
- The MCP community for building amazing servers

## References

- MCP Registry: https://registry.modelcontextprotocol.io
- MCP Registry API Docs: https://registry.modelcontextprotocol.io/docs
- GitHub API: https://docs.github.com/en/rest
