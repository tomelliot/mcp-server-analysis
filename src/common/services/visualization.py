"""Visualization functions for generating plots."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from rich.console import Console

console = Console()


def create_scatter_plot(
    df: pd.DataFrame,
    output_path: str = "mcp_activity_vs_popularity.png",
    title: str = "MCP Server Activity vs Popularity",
    figsize: tuple[int, int] = (12, 8),
    dpi: int = 300,
    use_log_scale: bool = False,
    show_plot: bool = False,
) -> None:
    """Create a scatter plot of repository activity vs popularity.
    
    Args:
        df: DataFrame with columns 'days_since_commit' and 'stars'.
        output_path: Path to save the plot (default: 'mcp_activity_vs_popularity.png').
        title: Plot title (default: 'MCP Server Activity vs Popularity').
        figsize: Figure size as (width, height) in inches (default: (12, 8)).
        dpi: Resolution in dots per inch (default: 300).
        use_log_scale: Whether to use log scale for y-axis (default: False).
        show_plot: Whether to display the plot interactively (default: False).
        
    Raises:
        ValueError: If required columns are missing from DataFrame.
    """
    # Validate required columns
    required_columns = {"days_since_commit", "stars"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f"DataFrame missing required columns: {missing_columns}")
    
    # Filter to only rows with valid data
    valid_df = df.dropna(subset=["days_since_commit", "stars"])
    
    if len(valid_df) == 0:
        raise ValueError("No valid data points to plot")
    
    # Set seaborn style
    sns.set_style("whitegrid")
    sns.set_palette("husl")
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=figsize)
    
    # Create scatter plot
    scatter = ax.scatter(
        valid_df["days_since_commit"],
        valid_df["stars"],
        alpha=0.6,
        s=50,
        c=valid_df["stars"],
        cmap="viridis",
        edgecolors="black",
        linewidth=0.5,
    )
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label("Stars", rotation=270, labelpad=20, fontsize=11)
    
    # Set labels and title
    ax.set_xlabel("Days Since Most Recent Commit", fontsize=12, fontweight="bold")
    ax.set_ylabel("GitHub Stars (Popularity)", fontsize=12, fontweight="bold")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=20)
    
    # Apply log scale if requested
    if use_log_scale:
        ax.set_yscale("log")
        ax.set_ylabel("GitHub Stars (Popularity, log scale)", fontsize=12, fontweight="bold")
    
    # Add grid for better readability
    ax.grid(True, alpha=0.3, linestyle="--")
    
    # Add statistics annotation
    total_points = len(valid_df)
    mean_stars = valid_df["stars"].mean()
    median_stars = valid_df["stars"].median()
    mean_days = valid_df["days_since_commit"].mean()
    
    stats_text = (
        f"n = {total_points}\n"
        f"Mean stars: {mean_stars:.0f}\n"
        f"Median stars: {median_stars:.0f}\n"
        f"Mean days since commit: {mean_days:.1f}"
    )
    
    ax.text(
        0.98,
        0.02,
        stats_text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="bottom",
        horizontalalignment="right",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
    )
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    # Save figure
    output_file = Path(output_path)
    plt.savefig(output_file, dpi=dpi, bbox_inches="tight")
    console.print(f"[green]✓ Plot saved to {output_file}[/green]")
    
    # Show plot if requested
    if show_plot:
        plt.show()
    else:
        plt.close()


def create_enhanced_scatter_plot(
    df: pd.DataFrame,
    output_path: str = "mcp_activity_vs_popularity_enhanced.png",
    title: str = "MCP Server Activity vs Popularity",
    figsize: tuple[int, int] = (14, 10),
    dpi: int = 300,
    show_plot: bool = False,
) -> None:
    """Create an enhanced scatter plot with multiple views and insights.
    
    This creates a 2x2 grid of plots:
    1. Linear scale scatter
    2. Log scale scatter
    3. Distribution of stars
    4. Distribution of days since commit
    
    Args:
        df: DataFrame with columns 'days_since_commit' and 'stars'.
        output_path: Path to save the plot (default: 'mcp_activity_vs_popularity_enhanced.png').
        title: Main title for the figure (default: 'MCP Server Activity vs Popularity').
        figsize: Figure size as (width, height) in inches (default: (14, 10)).
        dpi: Resolution in dots per inch (default: 300).
        show_plot: Whether to display the plot interactively (default: False).
        
    Raises:
        ValueError: If required columns are missing from DataFrame.
    """
    # Validate required columns
    required_columns = {"days_since_commit", "stars"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f"DataFrame missing required columns: {missing_columns}")
    
    # Filter to only rows with valid data
    valid_df = df.dropna(subset=["days_since_commit", "stars"])
    
    if len(valid_df) == 0:
        raise ValueError("No valid data points to plot")
    
    # Set seaborn style
    sns.set_style("whitegrid")
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=figsize)
    fig.suptitle(title, fontsize=16, fontweight="bold", y=0.995)
    
    # Plot 1: Linear scale scatter
    ax1 = axes[0, 0]
    scatter1 = ax1.scatter(
        valid_df["days_since_commit"],
        valid_df["stars"],
        alpha=0.6,
        s=30,
        c=valid_df["stars"],
        cmap="viridis",
        edgecolors="black",
        linewidth=0.3,
    )
    ax1.set_xlabel("Days Since Commit", fontsize=10)
    ax1.set_ylabel("Stars", fontsize=10)
    ax1.set_title("Linear Scale", fontsize=11, fontweight="bold")
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Log scale scatter
    ax2 = axes[0, 1]
    scatter2 = ax2.scatter(
        valid_df["days_since_commit"],
        valid_df["stars"],
        alpha=0.6,
        s=30,
        c=valid_df["stars"],
        cmap="plasma",
        edgecolors="black",
        linewidth=0.3,
    )
    ax2.set_xlabel("Days Since Commit", fontsize=10)
    ax2.set_ylabel("Stars (log scale)", fontsize=10)
    ax2.set_yscale("log")
    ax2.set_title("Log Scale", fontsize=11, fontweight="bold")
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Distribution of stars
    ax3 = axes[1, 0]
    sns.histplot(data=valid_df, x="stars", bins=50, kde=True, ax=ax3, color="skyblue")
    ax3.set_xlabel("Stars", fontsize=10)
    ax3.set_ylabel("Count", fontsize=10)
    ax3.set_title("Star Distribution", fontsize=11, fontweight="bold")
    ax3.grid(True, alpha=0.3, axis="y")
    
    # Plot 4: Distribution of days since commit
    ax4 = axes[1, 1]
    sns.histplot(data=valid_df, x="days_since_commit", bins=50, kde=True, ax=ax4, color="coral")
    ax4.set_xlabel("Days Since Commit", fontsize=10)
    ax4.set_ylabel("Count", fontsize=10)
    ax4.set_title("Activity Distribution", fontsize=11, fontweight="bold")
    ax4.grid(True, alpha=0.3, axis="y")
    
    # Adjust layout
    plt.tight_layout()
    
    # Save figure
    output_file = Path(output_path)
    plt.savefig(output_file, dpi=dpi, bbox_inches="tight")
    console.print(f"[green]✓ Enhanced plot saved to {output_file}[/green]")
    
    # Show plot if requested
    if show_plot:
        plt.show()
    else:
        plt.close()
