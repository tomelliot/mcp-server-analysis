"""Tests for visualization functions."""

import pandas as pd
import pytest
from pathlib import Path

from src.common.services.visualization import (
    create_scatter_plot,
    create_enhanced_scatter_plot,
)


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        "server_name": [f"server{i}" for i in range(10)],
        "stars": [100, 200, 150, 300, 50, 400, 250, 175, 125, 350],
        "days_since_commit": [5.0, 10.0, 3.0, 15.0, 1.0, 20.0, 8.0, 12.0, 6.0, 18.0],
    })


def test_create_scatter_plot(sample_dataframe: pd.DataFrame, tmp_path: Path) -> None:
    """Test basic scatter plot creation."""
    output_file = tmp_path / "test_plot.png"
    
    create_scatter_plot(
        sample_dataframe,
        output_path=str(output_file),
        show_plot=False,
    )
    
    assert output_file.exists()
    assert output_file.stat().st_size > 0


def test_create_scatter_plot_log_scale(sample_dataframe: pd.DataFrame, tmp_path: Path) -> None:
    """Test scatter plot with log scale."""
    output_file = tmp_path / "test_plot_log.png"
    
    create_scatter_plot(
        sample_dataframe,
        output_path=str(output_file),
        use_log_scale=True,
        show_plot=False,
    )
    
    assert output_file.exists()
    assert output_file.stat().st_size > 0


def test_create_scatter_plot_missing_columns() -> None:
    """Test scatter plot with missing required columns."""
    df = pd.DataFrame({
        "server_name": ["server1", "server2"],
        "stars": [100, 200],
        # Missing days_since_commit
    })
    
    with pytest.raises(ValueError, match="missing required columns"):
        create_scatter_plot(df, output_path="test.png")


def test_create_scatter_plot_no_valid_data() -> None:
    """Test scatter plot with no valid data points."""
    df = pd.DataFrame({
        "server_name": ["server1", "server2"],
        "stars": [None, None],
        "days_since_commit": [None, None],
    })
    
    with pytest.raises(ValueError, match="No valid data points"):
        create_scatter_plot(df, output_path="test.png")


def test_create_enhanced_scatter_plot(sample_dataframe: pd.DataFrame, tmp_path: Path) -> None:
    """Test enhanced scatter plot creation."""
    output_file = tmp_path / "test_plot_enhanced.png"
    
    create_enhanced_scatter_plot(
        sample_dataframe,
        output_path=str(output_file),
        show_plot=False,
    )
    
    assert output_file.exists()
    assert output_file.stat().st_size > 0
