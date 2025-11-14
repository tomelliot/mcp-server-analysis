"""Tests for GitHub API client."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.common.services.github_api import (
    fetch_repo_stats,
    fetch_repo_stats_from_url,
    parse_github_url,
)


def test_parse_github_url_valid() -> None:
    """Test parsing valid GitHub URLs."""
    # Standard URL
    assert parse_github_url("https://github.com/user/repo") == ("user", "repo")
    
    # With .git suffix
    assert parse_github_url("https://github.com/user/repo.git") == ("user", "repo")
    
    # With trailing slash
    assert parse_github_url("https://github.com/user/repo/") == ("user", "repo")
    
    # Organization
    assert parse_github_url("https://github.com/my-org/my-project") == ("my-org", "my-project")


def test_parse_github_url_invalid() -> None:
    """Test parsing invalid URLs."""
    # Not GitHub
    assert parse_github_url("https://gitlab.com/user/repo") is None
    
    # Empty string
    assert parse_github_url("") is None
    
    # None
    assert parse_github_url(None) is None
    
    # Invalid format
    assert parse_github_url("https://github.com/user") is None


@pytest.mark.asyncio
async def test_fetch_repo_stats_success(mocker: MagicMock) -> None:
    """Test successful repo stats fetching."""
    # Mock httpx.AsyncClient
    mock_client = AsyncMock()
    mock_context = AsyncMock()
    mock_context.__aenter__ = AsyncMock(return_value=mock_client)
    mock_context.__aexit__ = AsyncMock()
    
    # Mock responses
    mock_repo_response = MagicMock()
    mock_repo_response.status_code = 200
    mock_repo_response.json.return_value = {
        "stargazers_count": 100,
        "default_branch": "main",
        "pushed_at": "2025-11-10T00:00:00Z",
    }
    
    mock_commits_response = MagicMock()
    mock_commits_response.status_code = 200
    mock_commits_response.json.return_value = [
        {
            "commit": {
                "author": {
                    "date": "2025-11-10T00:00:00Z"
                }
            }
        }
    ]
    
    mock_client.get = AsyncMock(side_effect=[mock_repo_response, mock_commits_response])
    
    mocker.patch("src.common.services.github_api.httpx.AsyncClient", return_value=mock_context)
    
    # Test
    stats = await fetch_repo_stats("user", "repo")
    
    assert stats is not None
    assert stats.owner == "user"
    assert stats.repo == "repo"
    assert stats.stars == 100
    assert stats.days_since_commit >= 0


@pytest.mark.asyncio
async def test_fetch_repo_stats_not_found(mocker: MagicMock) -> None:
    """Test fetching stats for non-existent repo."""
    # Mock httpx.AsyncClient
    mock_client = AsyncMock()
    mock_context = AsyncMock()
    mock_context.__aenter__ = AsyncMock(return_value=mock_client)
    mock_context.__aexit__ = AsyncMock()
    
    # Mock 404 response
    mock_repo_response = MagicMock()
    mock_repo_response.status_code = 404
    
    mock_client.get = AsyncMock(return_value=mock_repo_response)
    
    mocker.patch("src.common.services.github_api.httpx.AsyncClient", return_value=mock_context)
    
    # Test
    stats = await fetch_repo_stats("nonexistent", "repo")
    
    assert stats is None


@pytest.mark.asyncio
async def test_fetch_repo_stats_from_url(mocker: MagicMock) -> None:
    """Test fetching stats from URL."""
    # Mock the underlying fetch_repo_stats function
    mock_stats = MagicMock()
    mock_stats.owner = "user"
    mock_stats.repo = "repo"
    mock_stats.stars = 50
    
    mocker.patch(
        "src.common.services.github_api.fetch_repo_stats",
        return_value=mock_stats
    )
    
    # Test
    stats = await fetch_repo_stats_from_url("https://github.com/user/repo")
    
    assert stats is not None
    assert stats.owner == "user"
    assert stats.repo == "repo"


@pytest.mark.asyncio
async def test_fetch_repo_stats_from_invalid_url() -> None:
    """Test fetching stats from invalid URL."""
    stats = await fetch_repo_stats_from_url("https://gitlab.com/user/repo")
    assert stats is None
