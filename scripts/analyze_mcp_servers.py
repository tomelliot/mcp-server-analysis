"""CLI script for analyzing MCP server activity vs popularity."""

import asyncio
import os
import sys
from pathlib import Path

import typer
from rich.console import Console

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.common.services.data_processor import (
    collect_and_save_data,
    filter_valid_data,
)
from src.common.services.github_api import fetch_repo_stats_from_url
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


@app.command()
def refetch(
    input_csv: str = typer.Argument(
        ...,
        help="Path to existing CSV file with incomplete data",
    ),
    output_csv: str | None = typer.Option(
        None,
        "--output-csv",
        "-o",
        help="Path to save updated CSV (defaults to overwriting input file)",
    ),
    max_concurrent: int = typer.Option(
        10,
        "--max-concurrent",
        "-c",
        help="Maximum concurrent GitHub API requests",
        min=1,
        max=50,
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
    force_refetch: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Refetch all GitHub data, even for rows with existing stats",
    ),
) -> None:
    """Refetch missing GitHub statistics from existing CSV data.
    
    This command:
    1. Loads an existing CSV file
    2. Identifies rows with missing GitHub stats (null stars/days_since_commit)
    3. Refetches GitHub data for those rows
    4. Updates the CSV with the new data
    
    Useful for:
    - Completing incomplete datasets (when initial fetch was interrupted)
    - Updating stale data
    - Retrying failed fetches with a GitHub token
    """
    import pandas as pd
    from rich.progress import (
        BarColumn,
        MofNCompleteColumn,
        Progress,
        SpinnerColumn,
        TextColumn,
        TimeElapsedColumn,
    )
    
    try:
        # Check if file exists
        if not Path(input_csv).exists():
            console.print(f"[red]✗ File not found: {input_csv}[/red]")
            raise typer.Exit(1)
        
        # Default output to input file
        if output_csv is None:
            output_csv = input_csv
        
        # Display header
        if not no_progress:
            console.print("\n[bold cyan]Refetching GitHub Statistics[/bold cyan]\n")
        
        # Load existing CSV
        console.print(f"[cyan]Loading data from {input_csv}...[/cyan]")
        df = pd.read_csv(input_csv)
        
        total_rows = len(df)
        console.print(f"[green]✓ Loaded {total_rows} rows[/green]\n")
        
        # Identify rows to refetch
        if force_refetch:
            # Refetch all rows with GitHub URLs
            to_refetch = df[df['github_url'].notna()].copy()
            console.print(f"[yellow]Force mode: Refetching all {len(to_refetch)} rows with GitHub URLs[/yellow]\n")
        else:
            # Only refetch rows with missing data
            to_refetch = df[
                (df['github_url'].notna()) & 
                (df['stars'].isna() | df['days_since_commit'].isna())
            ].copy()
            existing_stats = len(df[(df['stars'].notna()) & (df['days_since_commit'].notna())])
            console.print(f"[dim]Rows with existing stats: {existing_stats}[/dim]")
            console.print(f"[cyan]Rows to refetch: {len(to_refetch)}[/cyan]\n")
        
        if len(to_refetch) == 0:
            console.print("[green]✓ All rows already have GitHub stats! Nothing to refetch.[/green]\n")
            raise typer.Exit(0)
        
        # Refetch GitHub stats
        async def refetch_stats() -> int:
            """Refetch GitHub stats for missing rows."""
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def fetch_with_semaphore(idx: int, url: str) -> tuple[int, dict | None]:
                """Fetch stats for a single row."""
                async with semaphore:
                    stats = await fetch_repo_stats_from_url(
                        url,
                        github_token=github_token,
                    )
                    
                    if stats:
                        return idx, {
                            'stars': stats.stars,
                            'days_since_commit': stats.days_since_commit,
                            'last_commit_date': stats.last_commit_date,
                        }
                    return idx, None
            
            if no_progress:
                # Without progress display
                tasks = [
                    fetch_with_semaphore(idx, row['github_url'])
                    for idx, row in to_refetch.iterrows()
                ]
                results = await asyncio.gather(*tasks)
            else:
                # With progress display
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    MofNCompleteColumn(),
                    TimeElapsedColumn(),
                    console=console,
                ) as progress:
                    task_id = progress.add_task(
                        "Fetching GitHub stats...",
                        total=len(to_refetch),
                    )
                    
                    tasks = [
                        fetch_with_semaphore(idx, row['github_url'])
                        for idx, row in to_refetch.iterrows()
                    ]
                    
                    results = []
                    for coro in asyncio.as_completed(tasks):
                        result = await coro
                        results.append(result)
                        progress.update(task_id, advance=1)
            
            # Update DataFrame with results
            updated = 0
            for idx, stats_dict in results:
                if stats_dict:
                    df.loc[idx, 'stars'] = stats_dict['stars']
                    df.loc[idx, 'days_since_commit'] = stats_dict['days_since_commit']
                    df.loc[idx, 'last_commit_date'] = stats_dict['last_commit_date']
                    updated += 1
            
            return updated
        
        updated_count = asyncio.run(refetch_stats())
        
        # Save updated CSV
        df.to_csv(output_csv, index=False)
        
        # Display summary
        if not no_progress:
            console.print()
        
        console.print("[bold green]✓ Refetch complete![/bold green]\n")
        console.print("[bold]Summary:[/bold]")
        console.print(f"  Total rows: {total_rows}")
        console.print(f"  Attempted to refetch: {len(to_refetch)}")
        console.print(f"  Successfully updated: {updated_count}")
        console.print(f"  Failed: {len(to_refetch) - updated_count}")
        
        # Calculate final statistics
        final_stats = len(df[(df['stars'].notna()) & (df['days_since_commit'].notna())])
        console.print(f"  [cyan]Total with stats now: {final_stats}/{total_rows}[/cyan]")
        console.print(f"  Updated CSV saved to: [cyan]{output_csv}[/cyan]")
        console.print()
        
        if updated_count > 0:
            console.print("[dim]💡 Tip: Run 'visualize' command to create plots with updated data[/dim]\n")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Refetch interrupted by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"\n[red]✗ Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
