#!/usr/bin/env python3
"""
OpenAlex Author Disambiguation MCP Server v2.0.0

A professional MCP server for author disambiguation and institution resolution using OpenAlex.org API and pyalex.
Built following MCP best practices with the FastMCP library.

Features:
- ML-powered author disambiguation with confidence scoring
- Institution name resolution and abbreviation expansion  
- ORCID integration for highest accuracy
- Career analysis and publication metrics
- Full MCP protocol compliance
- Robust error handling for API limitations

Author: OpenAlex MCP Team
License: MIT
"""

import logging
from typing import Optional, List
from fastmcp import FastMCP
import pyalex

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("OpenAlex Academic Research")

# Load configuration for pyalex from a config file or environment
def configure_pyalex(email: str):
    """
    Configure pyalex for OpenAlex API usage.
    Args:
        email (str): The email to use for OpenAlex API requests.
    """
    pyalex.config.email = email
    pyalex.config.user_agent = f"OpenAlex-MCP-Server/2.0.0 ({email})"
    pyalex.config.max_retries = 0
    pyalex.config.retry_backoff_factor = 0.1
    pyalex.config.retry_http_codes = [429, 500, 503]

# Example: load from environment or config file in production
configure_pyalex("jorge.abreu@embo.org")


def autocomplete_ids(pyalex_cls, query: str, country_code: Optional[str] = None) -> str:
    """
    Autocomplete using a pyalex entity class and return a '|' joined string of IDs.
    Optionally filter by country_code (for Institutions).
    """
    if country_code and pyalex_cls is pyalex.Institutions:
        results = list(pyalex_cls().filter(country_code=country_code).autocomplete(query))
    else:
        results = list(pyalex_cls().autocomplete(query))
    ids = [entry["id"].split("/")[-1] for entry in results]
    return "|".join(ids) if ids else ""


def search_authors_core(
    name: str,
    institution: Optional[str] = None,
    topic: Optional[str] = None,
    country_code: Optional[str] = None,
    limit: int = 20
) -> dict:
    """
    Core logic for searching authors using OpenAlex.
    """
    try:
        query = pyalex.Authors().search_filter(display_name=name)

        # Institution filter (with optional country code)
        if institution:
            inst_ids = autocomplete_ids(
                pyalex.Institutions, institution, country_code=country_code
            )
            if inst_ids:
                inst_filter = {"institution": {"id": inst_ids}}
                if country_code:
                    inst_filter["institution"]["country_code"] = country_code
                query = query.filter(affiliations=inst_filter)
        elif country_code:
            # If only country_code is provided, filter by country_code
            query = query.filter(affiliations={"institution": {"country_code": country_code}})

        # Topics filter
        if topic:
            topic_ids = autocomplete_ids(pyalex.Topics, topic)
            if topic_ids:
                query = query.filter(topics={"id": topic_ids})

        results = query.get(per_page=limit)
        authors = list(results)
        if not authors:
            return {
                "authors": [],
                "error": {"code": 404, "message": f"No authors found for '{name}' with the given filters."}
            }
        author_list = [
            {
                "id": a.get("id"),
                "display_name": a.get("display_name"),
                "orcid": a.get("orcid"),
                "last_known_institution": a.get("last_known_institution", {}).get("display_name"),
                "works_count": a.get("works_count"),
                "cited_by_count": a.get("cited_by_count"),
            }
            for a in authors
        ]
        return {
            "authors": author_list,
            "error": None
        }
    except Exception as e:
        logger.error(f"Error in search_authors_core: {e}")
        return {
            "authors": [],
            "error": {"code": 500, "message": str(e)}
        }

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
    """
    return search_authors_core(
        name=name,
        institution=institution,
        topic=topic,
        country_code=country_code,
        limit=limit
    )

def main():
    """Entry point for the alex-mcp command."""
    import asyncio
    logger.info("OpenAlex Author Disambiguation MCP Server starting...")
    asyncio.run(mcp.run())

if __name__ == "__main__":
    main()
