"""Tests for data processor."""

import pandas as pd
import pytest

from src.common.services.data_processor import (
    ServerData,
    create_dataframe,
    filter_valid_data,
)


def test_server_data_model() -> None:
    """Test ServerData model validation."""
    data = ServerData(
        server_name="test.server",
        server_version="1.0.0",
        github_url="https://github.com/test/repo",
        stars=100,
        days_since_commit=5.0,
        last_commit_date="2025-11-09T00:00:00Z",
    )
    
    assert data.server_name == "test.server"
    assert data.stars == 100
    assert data.days_since_commit == 5.0


def test_server_data_model_with_nulls() -> None:
    """Test ServerData model with null values."""
    data = ServerData(
        server_name="test.server",
        server_version="1.0.0",
        github_url=None,
        stars=None,
        days_since_commit=None,
        last_commit_date=None,
    )
    
    assert data.server_name == "test.server"
    assert data.stars is None
    assert data.github_url is None


def test_create_dataframe() -> None:
    """Test DataFrame creation from ServerData list."""
    server_data = [
        ServerData(
            server_name="server1",
            server_version="1.0.0",
            github_url="https://github.com/test/repo1",
            stars=100,
            days_since_commit=5.0,
            last_commit_date="2025-11-09T00:00:00Z",
        ),
        ServerData(
            server_name="server2",
            server_version="2.0.0",
            github_url="https://github.com/test/repo2",
            stars=50,
            days_since_commit=10.0,
            last_commit_date="2025-11-04T00:00:00Z",
        ),
    ]
    
    df = create_dataframe(server_data)
    
    assert len(df) == 2
    assert "server_name" in df.columns
    assert "stars" in df.columns
    assert "days_since_commit" in df.columns
    # Check sorting (descending by stars)
    assert df.iloc[0]["stars"] == 100
    assert df.iloc[1]["stars"] == 50


def test_filter_valid_data() -> None:
    """Test filtering DataFrame for valid data."""
    df = pd.DataFrame({
        "server_name": ["server1", "server2", "server3"],
        "stars": [100, None, 50],
        "days_since_commit": [5.0, 10.0, None],
    })
    
    valid_df = filter_valid_data(df)
    
    assert len(valid_df) == 1
    assert valid_df.iloc[0]["server_name"] == "server1"


def test_filter_valid_data_empty() -> None:
    """Test filtering with no valid data."""
    df = pd.DataFrame({
        "server_name": ["server1", "server2"],
        "stars": [None, None],
        "days_since_commit": [None, None],
    })
    
    valid_df = filter_valid_data(df)
    
    assert len(valid_df) == 0
