"""CLI script for analyzing MCP server activity vs popularity."""

import asyncio
import os
import sys
from pathlib import Path

import typer
from rich.console import Console

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.common.services.data_processor import collect_and_save_data, filter_valid_data
from src.common.services.visualization import (
    create_enhanced_scatter_plot,
    create_scatter_plot,
)

app = typer.Typer(
    name="mcp-analyze",
    help="Analyze MCP server activity vs popularity",
    add_completion=False,
)
console = Console()


@app.command()
def analyze(
    output_csv: str = typer.Option(
        "mcp_servers_data.csv",
        "--output-csv",
        "-o",
        help="Path to save collected data CSV",
    ),
    output_plot: str = typer.Option(
        "mcp_activity_vs_popularity.png",
        "--output-plot",
        "-p",
        help="Path to save scatter plot",
    ),
    enhanced_plot: str = typer.Option(
        "mcp_activity_vs_popularity_enhanced.png",
        "--enhanced-plot",
        "-e",
        help="Path to save enhanced plot with multiple views",
    ),
    max_concurrent: int = typer.Option(
        10,
        "--max-concurrent",
        "-c",
        help="Maximum concurrent GitHub API requests",
        min=1,
        max=50,
    ),
    use_log_scale: bool = typer.Option(
        False,
        "--log-scale",
        "-l",
        help="Use log scale for y-axis in basic plot",
    ),
    github_token: str | None = typer.Option(
        None,
        "--github-token",
        "-t",
        help="GitHub API token (or set GITHUB_TOKEN env var)",
        envvar="GITHUB_TOKEN",
    ),
    no_progress: bool = typer.Option(
        False,
        "--no-progress",
        help="Disable progress indicators",
    ),
    skip_enhanced: bool = typer.Option(
        False,
        "--skip-enhanced",
        help="Skip creating enhanced plot",
    ),
) -> None:
    """Analyze MCP server activity vs popularity.
    
    This command:
    1. Fetches all servers from the MCP registry
    2. Retrieves GitHub statistics for each repository
    3. Saves collected data to CSV
    4. Generates scatter plot visualizations
    
    The analysis shows the relationship between repository activity
    (days since last commit) and popularity (GitHub stars).
    """
    try:
        # Display header
        if not no_progress:
            console.print("\n[bold cyan]MCP Server Activity vs Popularity Analysis[/bold cyan]\n")
            console.print("[dim]This may take several minutes...[/dim]\n")
        
        # Run async data collection
        df = asyncio.run(
            collect_and_save_data(
                output_path=output_csv,
                max_concurrent=max_concurrent,
                github_token=github_token,
                show_progress=not no_progress,
            )
        )
        
        # Filter to valid data for plotting
        valid_df = filter_valid_data(df)
        
        if len(valid_df) == 0:
            console.print("[red]✗ No valid data collected for plotting[/red]")
            raise typer.Exit(1)
        
        if not no_progress:
            console.print(f"[bold cyan]Creating visualizations...[/bold cyan]\n")
        
        # Create basic scatter plot
        create_scatter_plot(
            valid_df,
            output_path=output_plot,
            use_log_scale=use_log_scale,
            show_plot=False,
        )
        
        # Create enhanced plot if requested
        if not skip_enhanced:
            create_enhanced_scatter_plot(
                valid_df,
                output_path=enhanced_plot,
                show_plot=False,
            )
        
        # Display summary
        if not no_progress:
            console.print("\n[bold green]✓ Analysis complete![/bold green]\n")
            console.print("[bold]Summary:[/bold]")
            console.print(f"  Total servers: {len(df)}")
            console.print(f"  Servers with GitHub stats: {len(valid_df)}")
            console.print(f"  Data saved to: [cyan]{output_csv}[/cyan]")
            console.print(f"  Plot saved to: [cyan]{output_plot}[/cyan]")
            if not skip_enhanced:
                console.print(f"  Enhanced plot saved to: [cyan]{enhanced_plot}[/cyan]")
            console.print()
        
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Analysis interrupted by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"\n[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def visualize(
    input_csv: str = typer.Argument(
        ...,
        help="Path to CSV file with collected data",
    ),
    output_plot: str = typer.Option(
        "mcp_activity_vs_popularity.png",
        "--output-plot",
        "-p",
        help="Path to save scatter plot",
    ),
    enhanced_plot: str = typer.Option(
        "mcp_activity_vs_popularity_enhanced.png",
        "--enhanced-plot",
        "-e",
        help="Path to save enhanced plot",
    ),
    use_log_scale: bool = typer.Option(
        False,
        "--log-scale",
        "-l",
        help="Use log scale for y-axis in basic plot",
    ),
    skip_enhanced: bool = typer.Option(
        False,
        "--skip-enhanced",
        help="Skip creating enhanced plot",
    ),
) -> None:
    """Create visualizations from existing CSV data.
    
    Use this command to regenerate plots without re-fetching data.
    """
    import pandas as pd
    
    try:
        # Check if file exists
        if not Path(input_csv).exists():
            console.print(f"[red]✗ File not found: {input_csv}[/red]")
            raise typer.Exit(1)
        
        # Load data
        console.print(f"\n[cyan]Loading data from {input_csv}...[/cyan]")
        df = pd.read_csv(input_csv)
        
        # Filter valid data
        valid_df = filter_valid_data(df)
        
        if len(valid_df) == 0:
            console.print("[red]✗ No valid data found in CSV for plotting[/red]")
            raise typer.Exit(1)
        
        console.print(f"[green]✓ Loaded {len(valid_df)} valid data points[/green]\n")
        
        # Create plots
        console.print("[cyan]Creating visualizations...[/cyan]\n")
        
        create_scatter_plot(
            valid_df,
            output_path=output_plot,
            use_log_scale=use_log_scale,
            show_plot=False,
        )
        
        if not skip_enhanced:
            create_enhanced_scatter_plot(
                valid_df,
                output_path=enhanced_plot,
                show_plot=False,
            )
        
        console.print("\n[bold green]✓ Visualizations created![/bold green]\n")
        console.print(f"  Plot saved to: [cyan]{output_plot}[/cyan]")
        if not skip_enhanced:
            console.print(f"  Enhanced plot saved to: [cyan]{enhanced_plot}[/cyan]")
        console.print()
        
    except Exception as e:
        console.print(f"\n[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
