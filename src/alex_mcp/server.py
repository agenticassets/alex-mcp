#!/usr/bin/env python3
"""
OpenAlex Author Disambiguation MCP Server

Provides a FastMCP-compliant API for author disambiguation and institution resolution
using the OpenAlex API and pyalex client.

Features:
- Author search and disambiguation with rich metadata
- Institution name resolution
- ORCID integration
- Publication and citation metrics
- Full MCP protocol compliance

See https://docs.openalex.org/api-entities/authors/author-object for the Author object specification.
"""

import logging
from typing import Optional
from fastmcp import FastMCP
from alex_mcp.data_objects import SearchResponse, AuthorResult
import pyalex
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("OpenAlex Academic Research")

def configure_pyalex(email: str):
    """
    Configure pyalex for OpenAlex API usage.

    Args:
        email (str): The email to use for OpenAlex API requests.
    """
    pyalex.config.email = email

# Example: load from environment or config file in production
configure_pyalex("jorge.abreu@embo.org")

def search_authors_core(
    name: str,
    institution: Optional[str] = None,
    topic: Optional[str] = None,
    country_code: Optional[str] = None,
    limit: int = 20
) -> SearchResponse:
    """
    Core logic for searching authors using OpenAlex.

    Args:
        name: Author name to search for.
        institution: (Optional) Institution name filter.
        topic: (Optional) Topic filter.
        country_code: (Optional) Country code filter.
        limit: Maximum number of results to return.

    Returns:
        SearchResponse: Structured response with author results.
    """
    query = pyalex.Authors().search_filter(display_name=name)
    # Add additional filters as needed...
    results = query.get(per_page=limit)
    authors = list(results)
    author_list = []
    for a in authors:
        author_result = AuthorResult(
            id=a.get("id"),
            orcid=a.get("orcid"),
            display_name=a.get("display_name"),
            display_name_alternatives=a.get("display_name_alternatives"),
            affiliations=a.get("affiliations"),
            cited_by_count=a.get("cited_by_count"),
            counts_by_year=a.get("counts_by_year"),
            ids=a.get("ids"),
            summary_stats=a.get("summary_stats"),
            updated_date=a.get("updated_date"),
            works_api_url=a.get("works_api_url"),
            works_count=a.get("works_count"),
            x_concepts=a.get("x_concepts"),
            topics=a.get("topics"),
        )
        author_list.append(author_result)
    return SearchResponse(
        query=name,
        total_count=len(author_list),
        results=author_list
    )

@mcp.tool(
    annotations={
        "title": "Search Authors",
        "readOnlyHint": True,
        "openWorldHint": True
    }
)
async def search_authors(
    name: str,
    institution: Optional[str] = None,
    topic: Optional[str] = None,
    country_code: Optional[str] = None,
    limit: int = 20
) -> dict:
    """
    MCP tool wrapper for searching authors.

    Args:
        name: Author name to search for.
        institution: (Optional) Institution name filter.
        topic: (Optional) Topic filter.
        country_code: (Optional) Country code filter.
        limit: Maximum number of results to return.

    Returns:
        dict: Serialized SearchResponse.
    """
    response = search_authors_core(
        name=name,
        institution=institution,
        topic=topic,
        country_code=country_code,
        limit=limit
    )
    return response.dict()

def retrieve_author_works_core(
    author_id: str,
    limit: int = 20
) -> dict:
    """
    Core logic to retrieve works for a given OpenAlex Author ID.

    Args:
        author_id: The OpenAlex Author ID (e.g., 'https://openalex.org/A5058921480').
        limit: Maximum number of works to return.

    Returns:
        dict: Dictionary with a list of works and metadata.
    """

    # Extract the short author ID (e.g., 'A5058921480')
    if author_id.startswith("https://openalex.org/"):
        author_id_short = author_id.split("/")[-1]
    else:
        author_id_short = author_id

    try:
        works_query = pyalex.Works().filter(author={"id": f"https://openalex.org/{author_id_short}"})
        works = list(works_query.get(per_page=limit))
        return {
            "author_id": author_id,
            "works_count": len(works),
            "works": works
        }
    except Exception as e:
        logger.error(f"Error retrieving works for author {author_id}: {e}")
        return {
            "author_id": author_id,
            "works_count": 0,
            "works": [],
            "error": str(e)
        }

@mcp.tool(
    annotations={
        "title": "Retrieve Author Works",
        "description": "Given an OpenAlex Author ID, retrieve the list of works (publications) for that author.",
        "readOnlyHint": True,
        "openWorldHint": True
    }
)
async def retrieve_author_works(
    author_id: str,
    limit: int = 20
) -> dict:
    """
    MCP tool wrapper for retrieving works for a given author.

    Args:
        author_id: The OpenAlex Author ID (e.g., 'https://openalex.org/A5058921480').
        limit: Maximum number of works to return.

    Returns:
        dict: Dictionary with a list of works and metadata.
    """
    return retrieve_author_works_core(author_id=author_id, limit=limit)

def main():
    """
    Entry point for the alex-mcp server.
    """
    import asyncio
    logger.info("OpenAlex Author Disambiguation MCP Server starting...")
    asyncio.run(mcp.run())

if __name__ == "__main__":
    main()