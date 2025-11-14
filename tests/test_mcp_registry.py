"""Tests for MCP registry client."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.common.services.mcp_registry import (
    fetch_servers_page,
    fetch_all_servers,
    RegistryResponse,
)


@pytest.mark.asyncio
async def test_fetch_servers_page_success(mocker: MagicMock) -> None:
    """Test successful page fetch."""
    # Mock httpx.AsyncClient
    mock_client = AsyncMock()
    mock_context = AsyncMock()
    mock_context.__aenter__ = AsyncMock(return_value=mock_client)
    mock_context.__aexit__ = AsyncMock()
    
    # Mock response
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "servers": [
            {
                "server": {
                    "name": "test.server/one",
                    "version": "1.0.0",
                    "repository": {
                        "url": "https://github.com/test/one",
                        "source": "github"
                    }
                }
            },
            {
                "server": {
                    "name": "test.server/two",
                    "version": "2.0.0",
                    "repository": {}
                }
            }
        ],
        "metadata": {
            "nextCursor": "test.server/two:2.0.0",
            "count": 2
        }
    }
    
    mock_client.get = AsyncMock(return_value=mock_response)
    
    mocker.patch("src.common.services.mcp_registry.httpx.AsyncClient", return_value=mock_context)
    
    # Test
    response = await fetch_servers_page(limit=2)
    
    assert len(response.servers) == 2
    assert response.servers[0].server.name == "test.server/one"
    assert response.servers[0].server.repository.url == "https://github.com/test/one"
    assert response.servers[1].server.repository.url is None
    assert response.metadata.next_cursor == "test.server/two:2.0.0"


@pytest.mark.asyncio
async def test_fetch_all_servers(mocker: MagicMock) -> None:
    """Test fetching all servers with pagination."""
    # Mock fetch_servers_page to return two pages
    page1 = RegistryResponse.model_validate({
        "servers": [
            {
                "server": {
                    "name": "server1",
                    "version": "1.0.0",
                    "repository": {}
                }
            }
        ],
        "metadata": {
            "nextCursor": "cursor1",
            "count": 1
        }
    })
    
    page2 = RegistryResponse.model_validate({
        "servers": [
            {
                "server": {
                    "name": "server2",
                    "version": "2.0.0",
                    "repository": {}
                }
            }
        ],
        "metadata": {
            "nextCursor": None,
            "count": 1
        }
    })
    
    mocker.patch(
        "src.common.services.mcp_registry.fetch_servers_page",
        side_effect=[page1, page2]
    )
    
    # Test
    servers = await fetch_all_servers(show_progress=False)
    
    assert len(servers) == 2
    assert servers[0].server.name == "server1"
    assert servers[1].server.name == "server2"
