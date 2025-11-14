"""GitHub API client for fetching repository statistics."""

import os
import re
from datetime import datetime

import httpx
from pydantic import BaseModel, Field


class CommitAuthor(BaseModel):
    """Commit author information.
    
    Attributes:
        date: ISO 8601 timestamp of commit.
    """
    
    date: str


class CommitInfo(BaseModel):
    """Commit information.
    
    Attributes:
        author: Author information including commit date.
    """
    
    author: CommitAuthor


class GitHubCommit(BaseModel):
    """GitHub commit response.
    
    Attributes:
        commit: Commit details.
    """
    
    commit: CommitInfo


class GitHubRepo(BaseModel):
    """GitHub repository information.
    
    Attributes:
        stargazers_count: Number of stars.
        default_branch: Name of default branch.
        pushed_at: ISO 8601 timestamp of last push.
    """
    
    stargazers_count: int
    default_branch: str
    pushed_at: str


class RepoStats(BaseModel):
    """Combined repository statistics.
    
    Attributes:
        owner: Repository owner.
        repo: Repository name.
        stars: Number of stars.
        last_commit_date: ISO 8601 timestamp of most recent commit.
        days_since_commit: Days elapsed since last commit.
    """
    
    owner: str
    repo: str
    stars: int
    last_commit_date: str
    days_since_commit: float


def parse_github_url(url: str) -> tuple[str, str] | None:
    """Parse GitHub URL to extract owner and repo name.
    
    Args:
        url: GitHub repository URL.
        
    Returns:
        Tuple of (owner, repo) if valid GitHub URL, None otherwise.
        
    Examples:
        >>> parse_github_url("https://github.com/user/repo")
        ('user', 'repo')
        >>> parse_github_url("https://github.com/user/repo.git")
        ('user', 'repo')
        >>> parse_github_url("https://gitlab.com/user/repo")
        None
    """
    if not url or "github.com" not in url:
        return None
        
    # Match github.com/owner/repo with optional .git suffix
    pattern = r"github\.com/([^/]+)/([^/\.]+?)(?:\.git)?/?$"
    match = re.search(pattern, url)
    
    if match:
        return match.group(1), match.group(2)
    return None


async def fetch_repo_stats(
    owner: str,
    repo: str,
    github_token: str | None = None,
    timeout: float = 30.0,
) -> RepoStats | None:
    """Fetch repository statistics from GitHub API.
    
    Args:
        owner: Repository owner/organization.
        repo: Repository name.
        github_token: GitHub API token for authentication (optional).
        timeout: Request timeout in seconds (default: 30.0).
        
    Returns:
        RepoStats object with star count and commit information, or None if request fails.
        
    Raises:
        httpx.HTTPError: If the API request fails unexpectedly.
    """
    if not github_token:
        github_token = os.environ.get("GITHUB_TOKEN")
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "MCP-Server-Analysis/1.0",
    }
    
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    
    base_url = "https://api.github.com"
    
    try:
        async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
            # Fetch repository metadata
            repo_url = f"{base_url}/repos/{owner}/{repo}"
            repo_response = await client.get(repo_url)
            
            # Handle common error cases
            if repo_response.status_code == 404:
                return None  # Repo not found or private
            if repo_response.status_code == 403:
                return None  # Rate limited or forbidden
                
            repo_response.raise_for_status()
            repo_data = GitHubRepo.model_validate(repo_response.json())
            
            # Fetch latest commit
            commits_url = f"{base_url}/repos/{owner}/{repo}/commits"
            commits_response = await client.get(commits_url, params={"per_page": 1})
            
            if commits_response.status_code == 409:
                # Empty repository (no commits)
                return None
                
            commits_response.raise_for_status()
            commits_data = commits_response.json()
            
            if not commits_data:
                return None  # No commits found
            
            first_commit = GitHubCommit.model_validate(commits_data[0])
            last_commit_date = first_commit.commit.author.date
            
            # Calculate days since last commit
            commit_dt = datetime.fromisoformat(last_commit_date.replace("Z", "+00:00"))
            now = datetime.now(commit_dt.tzinfo)
            days_since = (now - commit_dt).total_seconds() / 86400  # 86400 seconds per day
            
            return RepoStats(
                owner=owner,
                repo=repo,
                stars=repo_data.stargazers_count,
                last_commit_date=last_commit_date,
                days_since_commit=days_since,
            )
            
    except httpx.HTTPStatusError as e:
        # Return None for HTTP errors (already handled specific cases above)
        return None
    except Exception:
        # Return None for any other errors (network, parsing, etc.)
        return None


async def fetch_repo_stats_from_url(
    github_url: str,
    github_token: str | None = None,
    timeout: float = 30.0,
) -> RepoStats | None:
    """Fetch repository statistics from a GitHub URL.
    
    Args:
        github_url: Full GitHub repository URL.
        github_token: GitHub API token for authentication (optional).
        timeout: Request timeout in seconds (default: 30.0).
        
    Returns:
        RepoStats object with star count and commit information, or None if invalid URL or request fails.
    """
    parsed = parse_github_url(github_url)
    if not parsed:
        return None
        
    owner, repo = parsed
    return await fetch_repo_stats(owner, repo, github_token, timeout)
