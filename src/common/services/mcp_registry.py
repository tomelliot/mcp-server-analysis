"""MCP Registry API client for fetching server data."""

import httpx
from pydantic import BaseModel, Field
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


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


async def fetch_all_servers(
    limit: int = 100,
    timeout: float = 30.0,
    show_progress: bool = True,
) -> list[ServerEntry]:
    """Fetch all servers from the MCP registry using pagination.
    
    Args:
        limit: Maximum number of servers per page (default: 100).
        timeout: Request timeout in seconds (default: 30.0).
        show_progress: Whether to show progress indicator (default: True).
        
    Returns:
        List of all server entries from the registry.
        
    Raises:
        httpx.HTTPError: If an API request fails.
        pydantic.ValidationError: If a response format is invalid.
    """
    all_servers: list[ServerEntry] = []
    cursor: str | None = None
    page_count = 0
    
    if show_progress:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Fetching servers from MCP registry...", total=None)
            
            while True:
                response = await fetch_servers_page(
                    limit=limit,
                    cursor=cursor,
                    timeout=timeout,
                )
                
                all_servers.extend(response.servers)
                page_count += 1
                
                progress.update(
                    task,
                    description=f"Fetched {len(all_servers)} servers ({page_count} pages)...",
                )
                
                # Check if there are more pages
                if not response.metadata.next_cursor:
                    break
                    
                cursor = response.metadata.next_cursor
                
            progress.update(
                task,
                description=f"✓ Fetched {len(all_servers)} servers from {page_count} pages",
            )
    else:
        while True:
            response = await fetch_servers_page(
                limit=limit,
                cursor=cursor,
                timeout=timeout,
            )
            
            all_servers.extend(response.servers)
            page_count += 1
            
            # Check if there are more pages
            if not response.metadata.next_cursor:
                break
                
            cursor = response.metadata.next_cursor
    
    return all_servers
