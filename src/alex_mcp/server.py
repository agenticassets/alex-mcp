#!/usr/bin/env python3
"""
Optimized OpenAlex Author Disambiguation MCP Server

Provides a FastMCP-compliant API for author disambiguation and institution resolution
using the OpenAlex API with streamlined output to minimize token usage.

Key optimizations:
- Simplified author objects (~70% token reduction)
- Streamlined work objects (~80% token reduction)
- Focused on essential disambiguation and retrieval information
- Maintains full functionality with minimal data

Features:
- Author search and disambiguation with essential metadata
- Institution name resolution (simplified to strings)
- ORCID integration
- Key publication and citation metrics
- Full MCP protocol compliance

See https://docs.openalex.org/api-entities/authors/author-object for the full Author object specification.
"""

import logging
from typing import Optional
from fastmcp import FastMCP
from alex_mcp.data_objects import (
    OptimizedAuthorResult,
    OptimizedSearchResponse,
    OptimizedWorksSearchResponse,
    OptimizedWorkResult,
    optimize_author_data,
    optimize_work_data
)
import pyalex
import os
import sys

def get_config():
    mailto = os.environ.get("OPENALEX_MAILTO")
    if not mailto:
        print(
            "ERROR: The environment variable OPENALEX_MAILTO must be set to your email address "
            "to use the OpenAlex MCP server. Example: export OPENALEX_MAILTO='your-email@example.com'",
            file=sys.stderr
        )
        sys.exit(1)
    return {
        "OPENALEX_MAILTO": mailto,
        "OPENALEX_USER_AGENT": os.environ.get(
            "OPENALEX_USER_AGENT",
            f"alex-mcp (+{mailto})"
        ),
        "OPENALEX_MAX_AUTHORS": int(os.environ.get("OPENALEX_MAX_AUTHORS", 50)),  # Reduced default
        "OPENALEX_RATE_PER_SEC": int(os.environ.get("OPENALEX_RATE_PER_SEC", 10)),
        "OPENALEX_RATE_PER_DAY": int(os.environ.get("OPENALEX_RATE_PER_DAY", 100000)),
        "OPENALEX_USE_DAILY_API": os.environ.get("OPENALEX_USE_DAILY_API", "true").lower() == "true",
        "OPENALEX_SNAPSHOT_INTERVAL_DAYS": int(os.environ.get("OPENALEX_SNAPSHOT_INTERVAL_DAYS", 30)),
        "OPENALEX_PREMIUM_UPDATES": os.environ.get("OPENALEX_PREMIUM_UPDATES", "hourly"),
        "OPENALEX_RETRACTION_BUG_START": os.environ.get("OPENALEX_RETRACTION_BUG_START", "2023-12-22"),
        "OPENALEX_RETRACTION_BUG_END": os.environ.get("OPENALEX_RETRACTION_BUG_END", "2024-03-19"),
        "OPENALEX_NO_FUNDING_DATA": os.environ.get("OPENALEX_NO_FUNDING_DATA", "true").lower() == "true",
        "OPENALEX_MISSING_CORRESPONDING_AUTHORS": os.environ.get("OPENALEX_MISSING_CORRESPONDING_AUTHORS", "true").lower() == "true",
        "OPENALEX_PARTIAL_ABSTRACTS": os.environ.get("OPENALEX_PARTIAL_ABSTRACTS", "true").lower() == "true",
    }

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

# Load configuration
config = get_config()
configure_pyalex(config["OPENALEX_MAILTO"])
pyalex.config.user_agent = config["OPENALEX_USER_AGENT"]


def search_authors_core(
    name: str,
    institution: Optional[str] = None,
    topic: Optional[str] = None,
    country_code: Optional[str] = None,
    limit: int = 15  # Reduced default limit
) -> OptimizedSearchResponse:
    """
    Optimized core logic for searching authors using OpenAlex.
    Returns streamlined author data to minimize token usage.

    Args:
        name: Author name to search for.
        institution: (Optional) Institution name filter.
        topic: (Optional) Topic filter.
        country_code: (Optional) Country code filter.
        limit: Maximum number of results to return (default: 15).

    Returns:
        OptimizedSearchResponse: Streamlined response with essential author data.
    """
    try:
        # Build query
        query = pyalex.Authors().search_filter(display_name=name)
        
        # Add filters if provided
        filters = {}
        if institution:
            filters['affiliations.institution.display_name.search'] = institution
        if topic:
            filters['x_concepts.display_name.search'] = topic
        if country_code:
            filters['affiliations.institution.country_code'] = country_code
        
        if filters:
            query = query.filter(**filters)
        
        # Execute query with limit
        results = query.get(per_page=min(limit, 25))  # Cap at 25 to control costs
        authors = list(results)
        
        # Convert to optimized format
        optimized_authors = []
        for author_data in authors:
            try:
                optimized_author = optimize_author_data(author_data)
                optimized_authors.append(optimized_author)
            except Exception as e:
                logger.warning(f"Error optimizing author data: {e}")
                # Skip problematic authors rather than failing completely
                continue
        
        logger.info(f"Found {len(optimized_authors)} authors for query: {name}")
        
        return OptimizedSearchResponse(
            query=name,
            total_count=len(optimized_authors),
            results=optimized_authors
        )
        
    except Exception as e:
        logger.error(f"Error searching authors for query '{name}': {e}")
        return OptimizedSearchResponse(
            query=name,
            total_count=0,
            results=[]
        )


@mcp.tool(
    annotations={
        "title": "Search Authors (Optimized)",
        "description": (
            "Search for authors by name with optional filters. "
            "Returns streamlined author data optimized for AI agents with ~70% fewer tokens. "
            "Includes essential info: name, ORCID, affiliations (as strings), metrics, and research fields."
        ),
        "readOnlyHint": True,
        "openWorldHint": True
    }
)
async def search_authors(
    name: str,
    institution: Optional[str] = None,
    topic: Optional[str] = None,
    country_code: Optional[str] = None,
    limit: int = 15
) -> dict:
    """
    Optimized MCP tool wrapper for searching authors.

    Args:
        name: Author name to search for.
        institution: (Optional) Institution name filter.
        topic: (Optional) Topic filter.
        country_code: (Optional) Country code filter.
        limit: Maximum number of results to return (default: 15, max: 25).

    Returns:
        dict: Serialized OptimizedSearchResponse with streamlined author data.
    """
    # Ensure reasonable limits to control token usage
    limit = min(limit, 25)
    
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
    limit: int = 10,  # Reduced default limit
    order_by: str = "date",  # "date" or "citations"
    publication_year: Optional[int] = None,
    type: Optional[str] = None,
    journal_only: bool = False,  # New filter for journal articles only
    min_citations: Optional[int] = None,  # New filter for minimum citations
) -> OptimizedWorksSearchResponse:
    """
    Optimized core logic to retrieve works for a given OpenAlex Author ID.
    Returns streamlined work data to minimize token usage.

    Args:
        author_id: OpenAlex Author ID
        limit: Maximum number of results (default: 10, max: 20)
        order_by: Sort order - "date" or "citations"
        publication_year: Filter by specific year
        type: Filter by work type (e.g., "journal-article")
        journal_only: If True, only return journal articles and letters
        min_citations: Minimum citation count filter

    Returns:
        OptimizedWorksSearchResponse: Streamlined response with essential work data.
    """
    try:
        # Ensure reasonable limits
        limit = min(limit, 20)
        
        # Build filters
        filters = {"author.id": author_id}
        
        if publication_year:
            filters["publication_year"] = publication_year
        if type:
            filters["type"] = type
        elif journal_only:
            # Focus on journal articles and letters for academic work
            filters["type"] = "journal-article|letter"
        if min_citations:
            filters["cited_by_count"] = f">={min_citations}"
        
        # Convert author_id to proper format if needed
        if author_id.startswith("https://openalex.org/"):
            author_id_short = author_id.split("/")[-1]
            filters["author.id"] = f"https://openalex.org/{author_id_short}"

        # Build query
        works_query = pyalex.Works().filter(**filters)
        
        # Apply sorting
        if order_by == "citations":
            works_query = works_query.sort(cited_by_count="desc")
        else:
            works_query = works_query.sort(updated_date="desc")
        
        # Execute query
        works = list(works_query.get(per_page=limit))
        
        # Get author name for response (if available from first work)
        author_name = None
        if works:
            authorships = works[0].get('authorships', [])
            for authorship in authorships:
                author = authorship.get('author', {})
                if author.get('id') == author_id:
                    author_name = author.get('display_name')
                    break
        
        # Convert to optimized format
        optimized_works = []
        for work_data in works:
            try:
                optimized_work = optimize_work_data(work_data)
                optimized_works.append(optimized_work)
            except Exception as e:
                logger.warning(f"Error optimizing work data: {e}")
                continue
        
        logger.info(f"Found {len(optimized_works)} works for author: {author_id}")
        
        return OptimizedWorksSearchResponse(
            author_id=author_id,
            author_name=author_name,
            total_count=len(optimized_works),
            results=optimized_works,
            filters=filters
        )
        
    except Exception as e:
        logger.error(f"Error retrieving works for author {author_id}: {e}")
        return OptimizedWorksSearchResponse(
            author_id=author_id,
            total_count=0,
            results=[],
            filters={}
        )


@mcp.tool(
    annotations={
        "title": "Retrieve Author Works (Optimized)",
        "description": (
            "Retrieve works (publications) for a given OpenAlex Author ID. "
            "Returns streamlined work data optimized for AI agents with ~80% fewer tokens. "
            "Includes essential info: title, DOI, year, journal, citations, and type. "
            "Supports filtering by year, type, and citation count."
        ),
        "readOnlyHint": True,
        "openWorldHint": True
    }
)
async def retrieve_author_works(
    author_id: str,
    limit: int = 10,
    order_by: str = "date",
    publication_year: Optional[int] = None,
    type: Optional[str] = None,
    journal_only: bool = False,
    min_citations: Optional[int] = None,
) -> dict:
    """
    Optimized MCP tool wrapper for retrieving works for a given author.

    Args:
        author_id: OpenAlex Author ID (e.g., 'https://openalex.org/A123456789')
        limit: Maximum number of results (default: 10, max: 20)
        order_by: Sort order - "date" for newest first, "citations" for most cited first
        publication_year: Filter by specific publication year
        type: Filter by work type (e.g., "journal-article", "book-chapter")
        journal_only: If True, only return journal articles and letters
        min_citations: Only return works with at least this many citations

    Returns:
        dict: Serialized OptimizedWorksSearchResponse with streamlined work data.
    """
    # Ensure reasonable limits to control token usage
    limit = min(limit, 20)
    
    response = retrieve_author_works_core(
        author_id=author_id,
        limit=limit,
        order_by=order_by,
        publication_year=publication_year,
        type=type,
        journal_only=journal_only,
        min_citations=min_citations,
    )
    return response.dict()


def main():
    """
    Entry point for the optimized alex-mcp server.
    """
    import asyncio
    logger.info("Optimized OpenAlex Author Disambiguation MCP Server starting...")
    logger.info("Features: ~70% token reduction for authors, ~80% for works")
    asyncio.run(mcp.run())


if __name__ == "__main__":
    main()