#!/usr/bin/env python3
"""
Optimized OpenAlex Author Disambiguation MCP Server with Peer-Review Filtering

Provides a FastMCP-compliant API for author disambiguation and institution resolution
using the OpenAlex API with streamlined output to minimize token usage.
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


def is_peer_reviewed_journal(work_data) -> bool:
    """
    Improved filter to determine if a work is from a peer-reviewed journal.
    
    Uses a balanced approach that catches data catalogs and preprints while
    not being overly strict about DOIs (some legitimate papers lack them in OpenAlex).
    
    Args:
        work_data: OpenAlex work object
        
    Returns:
        bool: True if the work appears to be from a peer-reviewed journal
    """
    try:
        title = work_data.get('title', '').lower()
        
        # Quick exclusions based on title patterns
        title_exclusions = [
            'vizier online data catalog',
            'online data catalog',
            'data catalog',
            'catalog:',
            'database:',
            'repository:',
            'preprint',
            'arxiv:',
            'biorxiv',
            'medrxiv',
        ]
        
        for exclusion in title_exclusions:
            if exclusion in title:
                logger.debug(f"Excluding based on title pattern '{exclusion}': {title[:100]}")
                return False
        
        # Check primary location
        primary_location = work_data.get('primary_location')
        if not primary_location:
            logger.debug("Excluding work without primary location")
            return False
        
        # Check source information
        source = primary_location.get('source', {})
        if not source:
            logger.debug("Excluding work without source")
            return False
        
        # Get journal/source information
        journal_name = source.get('display_name', '').lower()
        publisher = work_data.get('publisher', '')
        doi = work_data.get('doi')
        issn_l = source.get('issn_l')
        issn = source.get('issn')
        source_type = source.get('type', '').lower()
        
        # CRITICAL: Exclude known data catalogs by journal name
        excluded_journals = [
            'vizier online data catalog',
            'ycat',
            'catalog',
            'database',
            'repository',
            'arxiv',
            'biorxiv',
            'medrxiv',
            'ssrn',
            'research square',
            'zenodo',
            'figshare',
            'dryad',
            'github',
            'protocols.io',
            'ceur',
            'conference proceedings',
            'workshop proceedings',
        ]
        
        for excluded in excluded_journals:
            if excluded in journal_name:
                logger.debug(f"Excluding journal pattern '{excluded}': {journal_name}")
                return False
        
        # CRITICAL: Data catalogs typically have no publisher AND no DOI
        # This catches VizieR entries effectively
        if not publisher and not doi:
            logger.debug(f"Excluding work without publisher AND DOI: {title[:100]}")
            return False
        
        # Source type should be journal (if specified)
        if source_type and source_type not in ['journal', '']:
            logger.debug(f"Excluding non-journal source type: {source_type}")
            return False
        
        # Work type should be article or letter
        work_type = work_data.get('type', '').lower()
        if work_type not in ['article', 'letter']:
            logger.debug(f"Excluding work type: {work_type}")
            return False
        
        # Should have reasonable publication year
        pub_year = work_data.get('publication_year')
        if not pub_year or pub_year < 1900 or pub_year > 2030:
            logger.debug(f"Excluding work with invalid publication year: {pub_year}")
            return False
        
        # For papers claiming to be from legitimate journals, check quality signals
        known_legitimate_journals = [
            'nature',
            'science',
            'cell',
            'astrophysical journal',
            'astronomy and astrophysics',
            'monthly notices',
            'physical review',
            'journal of',
            'proceedings of',
        ]
        
        is_known_journal = any(known in journal_name for known in known_legitimate_journals)
        
        if is_known_journal:
            # For known journals, be more lenient (don't require DOI)
            # But still require either publisher or ISSN
            if not publisher and not issn_l and not issn:
                logger.debug(f"Excluding known journal without publisher/ISSN: {journal_name}")
                return False
        else:
            # For unknown journals, require more quality signals
            quality_signals = sum([
                bool(doi),          # Has DOI
                bool(publisher),    # Has publisher  
                bool(issn_l or issn),  # Has ISSN
                bool(journal_name and len(journal_name) > 5),  # Reasonable journal name
            ])
            
            if quality_signals < 2:  # Require at least 2 quality signals
                logger.debug(f"Excluding unknown journal with insufficient quality signals ({quality_signals}/4): {journal_name}")
                return False
        
        # Additional quality checks
        if 'cited_by_count' not in work_data:
            logger.debug("Excluding work without citation data")
            return False
        
        # Very long titles might be data descriptions
        if len(title) > 250:
            logger.debug(f"Excluding work with very long title: {title[:100]}...")
            return False
        
        # If we get here, it passes all checks
        logger.debug(f"ACCEPTED: {title[:100]}")
        return True
        
    except Exception as e:
        logger.warning(f"Error in peer review check: {e}")
        return False


def filter_peer_reviewed_works(works: list) -> list:
    """
    Apply peer-review filtering to a list of works.
    
    Args:
        works: List of OpenAlex work objects
        
    Returns:
        list: Filtered list containing only peer-reviewed journal works
    """
    filtered_works = []
    excluded_count = 0
    
    logger.info(f"Starting filtering of {len(works)} works...")
    
    for i, work in enumerate(works):
        title = work.get('title', 'Unknown')[:60]
        
        if is_peer_reviewed_journal(work):
            filtered_works.append(work)
            logger.debug(f"✓ KEPT work {i+1}: {title}")
        else:
            excluded_count += 1
            logger.debug(f"✗ EXCLUDED work {i+1}: {title}")
    
    logger.info(f"Filtering complete: {len(filtered_works)} kept, {excluded_count} excluded from {len(works)} total")
    return filtered_works


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
        results = query.get(per_page=min(limit, 100))  # Increased for comprehensive search
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


def retrieve_author_works_core(
    author_id: str,
    limit: int = 20_000,  # High default limit for comprehensive analysis
    order_by: str = "date",  # "date" or "citations"
    publication_year: Optional[int] = None,
    type: Optional[str] = None,
    journal_only: bool = True,  # Default to True for peer-reviewed content
    min_citations: Optional[int] = None,
    peer_reviewed_only: bool = True,  # Default to True
) -> OptimizedWorksSearchResponse:
    """
    Enhanced core logic to retrieve peer-reviewed works for a given OpenAlex Author ID.
    Returns streamlined work data to minimize token usage and ensures only legitimate
    peer-reviewed journal articles and letters.

    Args:
        author_id: OpenAlex Author ID
        limit: Maximum number of results (default: 2000 for comprehensive analysis)
        order_by: Sort order - "date" or "citations"
        publication_year: Filter by specific year
        type: Filter by work type (e.g., "journal-article")
        journal_only: If True, only return journal articles and letters
        min_citations: Minimum citation count filter
        peer_reviewed_only: If True, apply comprehensive peer-review filters

    Returns:
        OptimizedWorksSearchResponse: Streamlined response with peer-reviewed work data.
    """
    try:
        limit = min(limit, 20_000)
        
        # Build base filters
        filters = {"author.id": author_id}
        
        # Add optional filters
        if publication_year:
            filters["publication_year"] = publication_year
        if type:
            filters["type"] = type
        elif journal_only:
            # Focus on journal articles and letters for academic work
            filters["type"] = "article|letter"
        if min_citations:
            filters["cited_by_count"] = f">={min_citations}"
        
        # Add some basic API-level filters (but not too restrictive)
        if peer_reviewed_only or journal_only:
            # Only exclude obviously retracted papers at API level
            filters["is_retracted"] = "false"
        
        # Convert author_id to proper format if needed
        if author_id.startswith("https://openalex.org/"):
            author_id_short = author_id.split("/")[-1]
            filters["author.id"] = f"https://openalex.org/{author_id_short}"

        # Build query - get more results for post-filtering if needed
        if peer_reviewed_only:
            initial_limit = min(limit * 4, 20_000)  # Get 4x more for filtering, much higher limit
        else:
            initial_limit = limit
            
        works_query = pyalex.Works().filter(**filters)
        
        # Apply sorting
        if order_by == "citations":
            works_query = works_query.sort(cited_by_count="desc")
        else:
            works_query = works_query.sort(publication_date="desc")
        
        # Execute query using pagination to get ALL works
        logger.info(f"Querying OpenAlex for up to {initial_limit} works with filters: {filters}")
        
        # Use paginate() to get all works, not just the first page
        all_works = []
        pager = works_query.paginate(per_page=200, n_max=initial_limit)  # Use 200 per page (API recommended)
        
        for page in pager:
            all_works.extend(page)
            if len(all_works) >= initial_limit:
                break
        
        works = all_works[:initial_limit]  # Ensure we don't exceed the limit
        logger.info(f"Retrieved {len(works)} works from OpenAlex via pagination")
        
        # Apply peer-review filtering if requested
        if peer_reviewed_only:
            logger.info("Applying peer-review filtering...")
            works = filter_peer_reviewed_works(works)
            logger.info(f"After filtering: {len(works)} works remain")
        
        # Limit to requested number after filtering
        works = works[:limit]
        
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
        
        logger.info(f"Final result: {len(optimized_works)} works for author: {author_id}")
        
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
        limit: Maximum number of results to return (default: 15, max: 100).

    Returns:
        dict: Serialized OptimizedSearchResponse with streamlined author data.
    """
    # Ensure reasonable limits to control token usage
    limit = min(limit, 100)  # Increased for comprehensive author search
    
    response = search_authors_core(
        name=name,
        institution=institution,
        topic=topic,
        country_code=country_code,
        limit=limit
    )
    return response.model_dump()


@mcp.tool(
    annotations={
        "title": "Retrieve Author Works (Peer-Reviewed Only)",
        "description": (
            "Retrieve peer-reviewed journal works for a given OpenAlex Author ID. "
            "Automatically filters out data catalogs, preprint servers, and non-journal content. "
            "Returns streamlined work data optimized for AI agents with ~80% fewer tokens. "
            "Uses balanced filtering: excludes VizieR catalogs but allows legitimate papers without DOIs."
        ),
        "readOnlyHint": True,
        "openWorldHint": True
    }
)
async def retrieve_author_works(
    author_id: str,
    limit: Optional[int] = None,
    order_by: str = "date",
    publication_year: Optional[int] = None,
    type: Optional[str] = None,
    journal_only: bool = True,
    min_citations: Optional[int] = None,
    peer_reviewed_only: bool = True,
) -> dict:
    """
    Enhanced MCP tool wrapper for retrieving peer-reviewed journal works.

    Args:
        author_id: OpenAlex Author ID (e.g., 'https://openalex.org/A123456789')
        limit: Maximum number of results (default: None = ALL works, max: 2000)
        order_by: Sort order - "date" for newest first, "citations" for most cited first
        publication_year: Filter by specific publication year
        type: Filter by work type (e.g., "journal-article", "letter")
        journal_only: If True, only return journal articles and letters (default: True)
        min_citations: Only return works with at least this many citations
        peer_reviewed_only: If True, apply balanced peer-review filters (default: True)

    Returns:
        dict: Serialized OptimizedWorksSearchResponse with peer-reviewed journal works only.
    """
    # Handle limit: None means ALL works, otherwise cap at reasonable limit
    logger.info(f"MCP tool received limit parameter: {limit}")
    if limit is None:
        limit = 2000  # Set a very high limit to get ALL works
        logger.info(f"No limit specified, setting to {limit} for comprehensive retrieval")
    else:
        limit = min(limit, 2000)  # Increased max limit for comprehensive analysis
        logger.info(f"Explicit limit specified, capped to {limit}")
    
    response = retrieve_author_works_core(
        author_id=author_id,
        limit=limit,
        order_by=order_by,
        publication_year=publication_year,
        type=type,
        journal_only=journal_only,
        min_citations=min_citations,
        peer_reviewed_only=peer_reviewed_only,
    )
    return response.model_dump()


def main():
    """
    Entry point for the enhanced alex-mcp server with balanced peer-review filtering.
    """
    import asyncio
    logger.info("Enhanced OpenAlex Author Disambiguation MCP Server starting...")
    logger.info("Features: ~70% token reduction for authors, ~80% for works")
    logger.info("Balanced peer-review filtering: excludes data catalogs while preserving legitimate papers")
    asyncio.run(mcp.run())


if __name__ == "__main__":
    main()