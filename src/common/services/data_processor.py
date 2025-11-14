"""Data processing and transformation utilities."""

import asyncio
from datetime import datetime

import pandas as pd
from pydantic import BaseModel
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from src.common.services.github_api import fetch_repo_stats_from_url
from src.common.services.mcp_registry import ServerEntry, fetch_all_servers

console = Console()


class ServerData(BaseModel):
    """Data for a single MCP server.
    
    Attributes:
        server_name: Name/identifier of the server.
        server_version: Version of the server.
        github_url: GitHub repository URL (if available).
        stars: Number of GitHub stars (None if no GitHub repo or fetch failed).
        days_since_commit: Days since last commit (None if unavailable).
        last_commit_date: ISO 8601 timestamp of last commit (None if unavailable).
    """
    
    server_name: str
    server_version: str
    github_url: str | None
    stars: int | None
    days_since_commit: float | None
    last_commit_date: str | None


async def collect_server_data(
    max_concurrent: int = 10,
    github_token: str | None = None,
    show_progress: bool = True,
) -> list[ServerData]:
    """Collect data for all MCP servers from registry and GitHub.
    
    This function:
    1. Fetches all servers from the MCP registry
    2. Extracts GitHub URLs
    3. Fetches GitHub statistics concurrently with rate limiting
    4. Returns structured data for all servers
    
    Args:
        max_concurrent: Maximum concurrent GitHub API requests (default: 10).
        github_token: GitHub API token for authentication (optional).
        show_progress: Whether to show progress indicator (default: True).
        
    Returns:
        List of ServerData objects with collected information.
    """
    # Step 1: Fetch all servers from MCP registry
    if show_progress:
        console.print("\n[bold cyan]Step 1: Fetching MCP servers...[/bold cyan]")
    
    servers = await fetch_all_servers(show_progress=show_progress)
    
    if show_progress:
        console.print(f"[green]✓ Found {len(servers)} servers[/green]\n")
    
    # Step 2: Extract servers with GitHub URLs
    servers_with_github = [
        s for s in servers
        if s.server.repository.url and "github.com" in s.server.repository.url
    ]
    
    if show_progress:
        console.print(f"[bold cyan]Step 2: Fetching GitHub statistics...[/bold cyan]")
        console.print(f"[dim]Servers with GitHub repos: {len(servers_with_github)}/{len(servers)}[/dim]\n")
    
    # Step 3: Fetch GitHub stats concurrently
    server_data_list: list[ServerData] = []
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def fetch_with_semaphore(server: ServerEntry) -> ServerData:
        """Fetch GitHub stats with semaphore for rate limiting."""
        github_url = server.server.repository.url
        
        async with semaphore:
            if github_url and "github.com" in github_url:
                stats = await fetch_repo_stats_from_url(
                    github_url,
                    github_token=github_token,
                )
                
                if stats:
                    return ServerData(
                        server_name=server.server.name,
                        server_version=server.server.version,
                        github_url=github_url,
                        stars=stats.stars,
                        days_since_commit=stats.days_since_commit,
                        last_commit_date=stats.last_commit_date,
                    )
            
            # Return server data without GitHub stats
            return ServerData(
                server_name=server.server.name,
                server_version=server.server.version,
                github_url=github_url,
                stars=None,
                days_since_commit=None,
                last_commit_date=None,
            )
    
    if show_progress:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                "Fetching GitHub stats...",
                total=len(servers_with_github),
            )
            
            # Create tasks for all servers with GitHub URLs
            tasks = [fetch_with_semaphore(server) for server in servers_with_github]
            
            # Process tasks as they complete
            for coro in asyncio.as_completed(tasks):
                result = await coro
                server_data_list.append(result)
                progress.update(task, advance=1)
    else:
        # Without progress display
        tasks = [fetch_with_semaphore(server) for server in servers_with_github]
        server_data_list = await asyncio.gather(*tasks)
    
    # Add servers without GitHub repos
    for server in servers:
        if not server.server.repository.url or "github.com" not in server.server.repository.url:
            server_data_list.append(
                ServerData(
                    server_name=server.server.name,
                    server_version=server.server.version,
                    github_url=None,
                    stars=None,
                    days_since_commit=None,
                    last_commit_date=None,
                )
            )
    
    # Count successful GitHub fetches
    successful_fetches = sum(1 for s in server_data_list if s.stars is not None)
    
    if show_progress:
        console.print(f"\n[green]✓ Successfully fetched GitHub stats for {successful_fetches}/{len(servers_with_github)} repos[/green]")
    
    return server_data_list


def create_dataframe(server_data: list[ServerData]) -> pd.DataFrame:
    """Create a pandas DataFrame from collected server data.
    
    Args:
        server_data: List of ServerData objects.
        
    Returns:
        DataFrame with columns: server_name, server_version, github_url, stars, 
        days_since_commit, last_commit_date.
    """
    # Convert to DataFrame
    df = pd.DataFrame([data.model_dump() for data in server_data])
    
    # Sort by stars (descending), with NaN values last
    df = df.sort_values("stars", ascending=False, na_position="last")
    
    return df


def filter_valid_data(df: pd.DataFrame) -> pd.DataFrame:
    """Filter DataFrame to only include rows with valid GitHub stats.
    
    Args:
        df: DataFrame with server data.
        
    Returns:
        DataFrame with only rows that have both stars and days_since_commit.
    """
    return df.dropna(subset=["stars", "days_since_commit"])


async def collect_and_save_data(
    output_path: str = "mcp_servers_data.csv",
    max_concurrent: int = 10,
    github_token: str | None = None,
    show_progress: bool = True,
) -> pd.DataFrame:
    """Collect all data and save to CSV.
    
    This is the main pipeline function that:
    1. Collects data from MCP registry and GitHub
    2. Creates a DataFrame
    3. Saves to CSV
    4. Returns the DataFrame
    
    Args:
        output_path: Path to save CSV file (default: 'mcp_servers_data.csv').
        max_concurrent: Maximum concurrent GitHub API requests (default: 10).
        github_token: GitHub API token for authentication (optional).
        show_progress: Whether to show progress indicator (default: True).
        
    Returns:
        DataFrame with all collected data.
    """
    # Collect data
    server_data = await collect_server_data(
        max_concurrent=max_concurrent,
        github_token=github_token,
        show_progress=show_progress,
    )
    
    # Create DataFrame
    df = create_dataframe(server_data)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    
    if show_progress:
        console.print(f"\n[green]✓ Saved data to {output_path}[/green]")
        console.print(f"[dim]Total servers: {len(df)}[/dim]")
        console.print(f"[dim]With GitHub stats: {len(filter_valid_data(df))}[/dim]\n")
    
    return df
