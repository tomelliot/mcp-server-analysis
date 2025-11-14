"""MCP Registry API client for fetching server data."""

import httpx
from pydantic import BaseModel, Field


class Repository(BaseModel):
    """Repository information for an MCP server.
    
    Attributes:
        url: GitHub repository URL (optional).
        source: Source type (e.g., 'github') (optional).
    """
    
    url: str | None = None
    source: str | None = None


class ServerInfo(BaseModel):
    """MCP server information.
    
    Attributes:
        name: Server name/identifier.
        description: Server description.
        repository: Repository information.
        version: Server version.
    """
    
    name: str
    description: str | None = None
    repository: Repository = Field(default_factory=Repository)
    version: str


class ServerEntry(BaseModel):
    """MCP server entry from registry.
    
    Attributes:
        server: Server information.
    """
    
    server: ServerInfo


class RegistryMetadata(BaseModel):
    """Pagination metadata from registry response.
    
    Attributes:
        next_cursor: Cursor for next page of results.
        count: Number of items in current page.
    """
    
    next_cursor: str | None = Field(None, alias="nextCursor")
    count: int


class RegistryResponse(BaseModel):
    """Response from MCP registry API.
    
    Attributes:
        servers: List of server entries.
        metadata: Pagination metadata.
    """
    
    servers: list[ServerEntry]
    metadata: RegistryMetadata


async def fetch_servers_page(
    limit: int = 100,
    cursor: str | None = None,
    timeout: float = 30.0,
) -> RegistryResponse:
    """Fetch a single page of servers from the MCP registry.
    
    Args:
        limit: Maximum number of servers to fetch (default: 100).
        cursor: Pagination cursor for fetching next page (optional).
        timeout: Request timeout in seconds (default: 30.0).
        
    Returns:
        RegistryResponse containing servers and pagination metadata.
        
    Raises:
        httpx.HTTPError: If the API request fails.
        pydantic.ValidationError: If the response format is invalid.
    """
    base_url = "https://registry.modelcontextprotocol.io/v0/servers"
    params = {"limit": limit}
    
    if cursor:
        params["cursor"] = cursor
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
    return RegistryResponse.model_validate(data)
