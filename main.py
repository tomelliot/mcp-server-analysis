"""Main entry point for MCP server analysis.

Run the CLI with:
    python scripts/analyze_mcp_servers.py analyze --help
    
Or run a full analysis:
    python scripts/analyze_mcp_servers.py analyze
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def main() -> None:
    """Display usage information."""
    print("MCP Server Activity vs Popularity Analysis")
    print("=" * 50)
    print("\nUsage:")
    print("  Run full analysis:")
    print("    python scripts/analyze_mcp_servers.py analyze")
    print("\n  Create plots from existing CSV:")
    print("    python scripts/analyze_mcp_servers.py visualize <csv_file>")
    print("\n  Get help:")
    print("    python scripts/analyze_mcp_servers.py --help")
    print("    python scripts/analyze_mcp_servers.py analyze --help")
    print()


if __name__ == "__main__":
    main()
