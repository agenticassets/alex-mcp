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
    OptimizedGeneralWorksSearchResponse,
    OptimizedWorkResult,
    AutocompleteAuthorCandidate,
    AutocompleteAuthorsResponse,
    optimize_author_data,
    optimize_work_data
)
import pyalex
import os
import sys
import aiohttp
import asyncio
import json
import re

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
        # Safe string extraction with None checking
        title = work_data.get('title') or ''
        if isinstance(title, str):
            title = title.lower()
        else:
            title = str(title).lower() if title is not None else ''
        
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
        
        # Get journal/source information with safe None checking
        journal_name_raw = source.get('display_name') or ''
        journal_name = journal_name_raw.lower() if isinstance(journal_name_raw, str) else str(journal_name_raw).lower()
        
        publisher = work_data.get('publisher', '')
        doi = work_data.get('doi')
        issn_l = source.get('issn_l')
        issn = source.get('issn')
        
        source_type_raw = source.get('type') or ''
        source_type = source_type_raw.lower() if isinstance(source_type_raw, str) else str(source_type_raw).lower()
        
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
        
        # Work type should be article or letter with safe None checking
        work_type_raw = work_data.get('type') or ''
        work_type = work_type_raw.lower() if isinstance(work_type_raw, str) else str(work_type_raw).lower()
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
        logger.error(f"Error in peer review check for work: {e}")
        logger.error(f"Work data keys: {list(work_data.keys()) if isinstance(work_data, dict) else 'Not a dict'}")
        logger.error(f"Work title: {repr(work_data.get('title') if isinstance(work_data, dict) else 'N/A')}")
        logger.error(f"Primary location: {repr(work_data.get('primary_location') if isinstance(work_data, dict) else 'N/A')}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
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
        # Safe handling of potentially None work or title
        if work is None:
            logger.warning(f"Skipping None work at position {i+1}")
            excluded_count += 1
            continue
            
        title_raw = work.get('title') if isinstance(work, dict) else None
        title = (title_raw or 'Unknown')[:60] if title_raw is not None else 'Unknown'
        
        try:
            if is_peer_reviewed_journal(work):
                filtered_works.append(work)
                logger.debug(f"✓ KEPT work {i+1}: {title}")
            else:
                excluded_count += 1
                logger.debug(f"✗ EXCLUDED work {i+1}: {title}")
        except Exception as e:
            logger.error(f"Error filtering work {i+1} (title: {title}): {e}")
            excluded_count += 1
    
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


def autocomplete_authors_core(
    name: str, 
    context: Optional[str] = None, 
    limit: int = 10,
    filter_no_institution: bool = True,
    enable_institution_ranking: bool = True
) -> AutocompleteAuthorsResponse:
    """
    Enhanced core function for author autocomplete with intelligent filtering and ranking.
    
    Args:
        name: Author name to search for
        context: Optional context for better matching (institution, research area, etc.)
        limit: Maximum number of candidates to return (increased default to 10)
        filter_no_institution: If True, exclude candidates with no institutional affiliation
        enable_institution_ranking: If True, rank candidates by institutional context relevance
        
    Returns:
        AutocompleteAuthorsResponse with filtered and ranked candidate authors
    """
    try:
        logger.info(f"🔍 Autocompleting authors for: '{name}' (limit: {limit})")
        if context:
            logger.info(f"   📝 Context provided: {context}")
        
        # Use PyAlex autocomplete for authors - get more results for filtering
        raw_limit = min(limit * 2, 20)  # Get 2x candidates for filtering
        results = pyalex.Authors().autocomplete(name)[:raw_limit]
        
        # Convert to our data model first
        all_candidates = []
        for result in results:
            candidate = AutocompleteAuthorCandidate(
                openalex_id=result.get('id', ''),
                display_name=result.get('display_name', ''),
                institution_hint=result.get('hint'),
                works_count=result.get('works_count', 0),
                cited_by_count=result.get('cited_by_count', 0),
                entity_type=result.get('entity_type', 'author'),
                external_id=result.get('external_id')
            )
            all_candidates.append(candidate)
        
        # ENHANCEMENT 1: Filter out candidates with no institution
        if filter_no_institution:
            filtered_candidates = [
                c for c in all_candidates 
                if c.institution_hint and c.institution_hint not in ['No institution', 'None', '']
            ]
            excluded_count = len(all_candidates) - len(filtered_candidates)
            if excluded_count > 0:
                logger.info(f"   🔍 Filtered out {excluded_count} candidates with no institution")
        else:
            filtered_candidates = all_candidates
        
        # ENHANCEMENT 2: Institution-aware ranking (if context provided)
        if enable_institution_ranking and context and filtered_candidates:
            scored_candidates = []
            context_lower = context.lower()
            
            for candidate in filtered_candidates:
                relevance_score = 0
                matched_terms = []
                
                inst_hint = (candidate.institution_hint or '').lower()
                
                # High-value institutional matches
                high_value_terms = [
                    'max planck', 'harvard', 'stanford', 'mit', 'cambridge', 'oxford',
                    'excellence cluster', 'crick', 'wellcome', 'nih', 'cnrs', 'inserm'
                ]
                for term in high_value_terms:
                    if term in context_lower and term in inst_hint:
                        relevance_score += 3
                        matched_terms.append(f"{term} (+3)")
                
                # Location-based matches
                location_terms = ['germany', 'uk', 'usa', 'france', 'köln', 'cologne', 'london', 'boston', 'berlin']
                for term in location_terms:
                    if term in context_lower and term in inst_hint:
                        relevance_score += 2
                        matched_terms.append(f"{term} (+2)")
                
                # Research field alignment (basic keyword matching)
                research_terms = ['biology', 'chemistry', 'biochemistry', 'physics', 'medicine']
                for term in research_terms:
                    if term in context_lower and term in inst_hint:
                        relevance_score += 1
                        matched_terms.append(f"{term} (+1)")
                
                # High-impact researcher bonus
                if candidate.cited_by_count and candidate.cited_by_count > 1000:
                    relevance_score += 1
                    matched_terms.append("high-impact (+1)")
                
                scored_candidates.append({
                    'candidate': candidate,
                    'relevance_score': relevance_score,
                    'matched_terms': matched_terms
                })
            
            # Sort by relevance score (descending), then by citation count
            scored_candidates.sort(key=lambda x: (x['relevance_score'], x['candidate'].cited_by_count), reverse=True)
            
            # Extract ranked candidates
            final_candidates = [sc['candidate'] for sc in scored_candidates[:limit]]
            
            # Log ranking results
            logger.info(f"   🏆 Institution-aware ranking applied:")
            for i, sc in enumerate(scored_candidates[:3], 1):  # Log top 3
                candidate = sc['candidate']
                logger.info(f"      {i}. {candidate.display_name} (score: {sc['relevance_score']}, {candidate.institution_hint})")
        else:
            # No ranking, just take first N candidates
            final_candidates = filtered_candidates[:limit]
        
        # Log final candidates
        for candidate in final_candidates:
            logger.info(f"   👤 {candidate.display_name} ({candidate.institution_hint or 'No institution'}) - {candidate.works_count} works")
        
        response = AutocompleteAuthorsResponse(
            query=name,
            context=context,
            total_candidates=len(final_candidates),
            candidates=final_candidates,
            search_metadata={
                'api_used': 'openalex_autocomplete',
                'has_context': context is not None,
                'filtered_no_institution': filter_no_institution,
                'institution_ranking_enabled': enable_institution_ranking and context is not None,
                'response_time_ms': None  # Could be added with timing
            }
        )
        
        logger.info(f"✅ Found {len(final_candidates)} candidates for '{name}'")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error in autocomplete_authors_core: {e}")
        # Return empty response on error
        return AutocompleteAuthorsResponse(
            query=name,
            context=context,
            total_candidates=0,
            candidates=[],
            search_metadata={
                'api_used': 'openalex_autocomplete',
                'has_context': context is not None,
                'error': str(e)
            }
        )


def search_works_core(
    query: str,
    author: Optional[str] = None,
    institution: Optional[str] = None,
    publication_year: Optional[int] = None,
    type: Optional[str] = None,
    limit: int = 25,
    peer_reviewed_only: bool = True,
    search_type: str = "general"
) -> OptimizedGeneralWorksSearchResponse:
    """
    Core logic for searching works using OpenAlex with configurable search modes.
    Returns streamlined work data to minimize token usage.

    Args:
        query: Search query text
        author: (Optional) Author name filter
        institution: (Optional) Institution name filter
        publication_year: (Optional) Publication year filter
        type: (Optional) Work type filter (e.g., "article", "letter")
        limit: Maximum number of results (default: 25, max: 100)
        peer_reviewed_only: If True, apply peer-review filters (default: True)
        search_type: Search mode - "general" (title/abstract/fulltext), "title" (title only), 
                    or "title_and_abstract" (title and abstract only)

    Returns:
        OptimizedGeneralWorksSearchResponse: Streamlined response with work data.
    """
    try:
        # Ensure reasonable limits to control token usage
        limit = min(limit, 100)
        
        # Build the search query using PyAlex based on search_type
        if search_type == "title":
            # Use title-specific search for precise title matching
            works_query = pyalex.Works()
            filters = {'title.search': query}
        elif search_type == "title_and_abstract":
            # Use title and abstract search
            works_query = pyalex.Works()
            filters = {'title_and_abstract.search': query}
        else:  # search_type == "general" or any other value
            # Use general search across title, abstract, and fulltext (default behavior)
            works_query = pyalex.Works().search(query)
            filters = {}
        
        # Add author filter if provided
        if author:
            # For general work search, we can use raw_author_name.search for name-based filtering
            # This searches for works where the author name appears in the raw author strings
            filters['raw_author_name.search'] = author
        
        # Add institution filter if provided  
        if institution:
            # Use the correct field for institution name filtering
            filters['authorships.institutions.display_name.search'] = institution
        
        # Add publication year filter
        if publication_year:
            filters['publication_year'] = publication_year
        
        # Add type filter
        if type:
            filters['type'] = type
        elif peer_reviewed_only:
            # Focus on journal articles and letters for academic work
            filters['type'] = 'article|letter'
        
        # Add basic quality filters
        if peer_reviewed_only:
            filters['is_retracted'] = False
        
        # Apply filters to query
        if filters:
            works_query = works_query.filter(**filters)
        
        # Execute query
        logger.info(f"Searching OpenAlex works with search_type='{search_type}', query: '{query[:50]}...' and {len(filters)} filters")
        results = works_query.get(per_page=limit)
        
        # Apply additional peer-review filtering if requested
        if peer_reviewed_only and results:
            logger.info(f"Applying peer-review filtering to {len(results)} results...")
            results = filter_peer_reviewed_works(results)
            logger.info(f"After peer-review filtering: {len(results)} results remain")
        
        # Convert to optimized format
        optimized_works = []
        for work in results:
            try:
                optimized_work = optimize_work_data(work)
                optimized_works.append(optimized_work)
            except Exception as e:
                logger.warning(f"Error optimizing work data: {e}")
                continue
        
        logger.info(f"Returning {len(optimized_works)} optimized works for search query")
        
        return OptimizedGeneralWorksSearchResponse(
            query=query,
            total_count=len(optimized_works),
            results=optimized_works,
            filters=filters
        )
        
    except Exception as e:
        logger.error(f"Error searching works for query '{query}': {e}")
        return OptimizedGeneralWorksSearchResponse(
            query=query,
            total_count=0,
            results=[],
            filters={}
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
    Enhanced MCP tool wrapper for retrieving author works with flexible filtering.

    Args:
        author_id: OpenAlex Author ID (e.g., 'https://openalex.org/A123456789')
        limit: Maximum number of results (default: None = ALL works via pagination, max: 2000)
        order_by: Sort order - "date" for newest first, "citations" for most cited first
        publication_year: Filter by specific publication year
        type: Filter by work type (e.g., "journal-article", "letter")
        journal_only: If True, only return journal articles and letters (default: True)
        min_citations: Only return works with at least this many citations
        peer_reviewed_only: If True, apply balanced peer-review filters (default: True)

    Returns:
        dict: Serialized OptimizedWorksSearchResponse with author's works.
        
    Usage Patterns:
        # For AI validation (sample of high-impact works)
        retrieve_author_works(author_id, limit=20, order_by="citations")
        
        # For complete benchmark evaluation (ALL works, minimal filtering)
        retrieve_author_works(author_id, peer_reviewed_only=False, journal_only=False)
        
        # For peer-reviewed works only (default behavior)
        retrieve_author_works(author_id)
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


@mcp.tool(
    annotations={
        "title": "Search Works (Optimized)",
        "description": (
            "Search for academic works with configurable search modes and optional filters. "
            "Returns streamlined work data optimized for AI agents with ~80% fewer tokens. "
            "Supports different search types: 'general' (title/abstract/fulltext), 'title' (title only), "
            "or 'title_and_abstract' (title and abstract only). "
            "Supports author, institution, publication year, and type filters. "
            "Automatically applies peer-review filtering to exclude data catalogs and preprints."
        ),
        "readOnlyHint": True,
        "openWorldHint": True
    }
)
async def search_works(
    query: str,
    author: Optional[str] = None,
    institution: Optional[str] = None,
    publication_year: Optional[int] = None,
    type: Optional[str] = None,
    limit: int = 25,
    peer_reviewed_only: bool = True,
    search_type: str = "general"
) -> dict:
    """
    Optimized MCP tool wrapper for searching works.

    Args:
        query: Search query text
        author: (Optional) Author name filter
        institution: (Optional) Institution name filter
        publication_year: (Optional) Publication year filter
        type: (Optional) Work type filter (e.g., "article", "letter")
        limit: Maximum number of results (default: 25, max: 100)
        peer_reviewed_only: If True, apply peer-review filters (default: True)
        search_type: Search mode - "general" (title/abstract/fulltext), "title" (title only), 
                    or "title_and_abstract" (title and abstract only)

    Returns:
        dict: Serialized OptimizedGeneralWorksSearchResponse with streamlined work data.
    """
    # Ensure reasonable limits to control token usage
    limit = min(limit, 100)
    
    response = search_works_core(
        query=query,
        author=author,
        institution=institution,
        publication_year=publication_year,
        type=type,
        limit=limit,
        peer_reviewed_only=peer_reviewed_only,
        search_type=search_type
    )
    return response.model_dump()


@mcp.tool(
    annotations={
        "title": "Autocomplete Authors (Smart Disambiguation)",
        "description": (
            "Get multiple author candidates using OpenAlex autocomplete API for intelligent disambiguation. "
            "Returns a ranked list of potential author matches with institutional hints and research metrics. "
            "Perfect when you need to disambiguate authors and have context like institution, research area, or co-authors. "
            "The AI can select the best match based on the provided context. "
            "Much faster than full search (~200ms) and provides multiple options for better accuracy."
        ),
        "readOnlyHint": True,
        "openWorldHint": True
    }
)
async def autocomplete_authors(
    name: str,
    context: Optional[str] = None, 
    limit: int = 10,
    filter_no_institution: bool = True,
    enable_institution_ranking: bool = True
) -> dict:
    """
    Enhanced autocomplete authors with intelligent filtering and ranking.
    
    Args:
        name: Author name to search for (e.g., "James Briscoe", "M. Ralser")
        context: Optional context to help with disambiguation (e.g., "Francis Crick Institute developmental biology", "Max Planck Institute Köln Germany")
        limit: Maximum number of candidates to return (default: 10, max: 15)
        filter_no_institution: If True, exclude candidates with no institutional affiliation (default: True)
        enable_institution_ranking: If True, rank candidates by institutional context relevance (default: True)
        
    Returns:
        dict: Serialized AutocompleteAuthorsResponse with filtered and ranked candidate authors, including:
        - openalex_id: Full OpenAlex author ID
        - display_name: Author's display name
        - institution_hint: Current/last known institution 
        - works_count: Number of published works
        - cited_by_count: Total citation count
        - external_id: ORCID or other external identifiers
        - search_metadata: Information about filtering and ranking applied
        
    Example usage:
        # Get high-quality candidates with institutional filtering
        candidates = await autocomplete_authors("Ivan Matić", context="Max Planck Institute Biology Ageing Köln Germany")
        
        # For seasoned researchers, institution hints and ranking help disambiguation
        # AI can then select the best match or retrieve works for further verification
        
    Enhanced Features:
        - Filters out candidates with no institutional affiliation (reduces noise)
        - Institution-aware ranking when context is provided (improves accuracy)
        - Higher default limit (10 vs 5) for better candidate coverage
        - Detailed logging for debugging and optimization
    """
    # Ensure reasonable limits - increased max to 15
    limit = min(max(limit, 1), 15)
    
    response = autocomplete_authors_core(
        name=name,
        context=context, 
        limit=limit,
        filter_no_institution=filter_no_institution,
        enable_institution_ranking=enable_institution_ranking
    )
    return response.model_dump()


# PubMed Integration Functions
import requests
import xml.etree.ElementTree as ET
from typing import Union

def pubmed_search_core(
    query: str,
    max_results: int = 20,
    search_type: str = "author"
) -> dict:
    """
    Core PubMed search functionality using E-utilities API.
    
    Args:
        query: Search query (author name, DOI, or keywords)
        max_results: Maximum number of results to return
        search_type: Type of search ("author", "doi", "title", "keywords")
        
    Returns:
        dict with search results including PMIDs, total count, and basic metadata
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    
    try:
        # Format search term based on type
        if search_type == "author":
            search_term = f'"{query}"[Author]'
        elif search_type == "doi":
            clean_doi = query.replace('https://doi.org/', '').replace('http://dx.doi.org/', '')
            search_term = f'"{clean_doi}"[AID]'
        elif search_type == "title":
            search_term = f'"{query}"[Title]'
        else:  # keywords
            search_term = query
        
        logger.info(f"🔍 PubMed search: {search_term} (max: {max_results})")
        
        # Search PubMed
        search_url = f"{base_url}esearch.fcgi"
        search_params = {
            'db': 'pubmed',
            'term': search_term,
            'retmax': max_results,
            'retmode': 'json',
            'sort': 'relevance'
        }
        
        response = requests.get(search_url, params=search_params, timeout=10)
        response.raise_for_status()
        search_data = response.json()
        
        pmids = search_data.get('esearchresult', {}).get('idlist', [])
        total_count = int(search_data.get('esearchresult', {}).get('count', 0))
        
        logger.info(f"📊 Found {total_count} total results, retrieved {len(pmids)} PMIDs")
        
        # Get basic details for retrieved PMIDs (if any)
        articles = []
        if pmids:
            articles = get_pubmed_summaries(pmids[:min(len(pmids), 10)])  # Limit to 10 for performance
        
        return {
            'query': query,
            'search_type': search_type,
            'search_term_used': search_term,
            'total_count': total_count,
            'retrieved_count': len(pmids),
            'pmids': pmids,
            'articles': articles,
            'search_metadata': {
                'api_used': 'pubmed_esearch',
                'max_results_requested': max_results,
                'response_time_ms': None
            }
        }
        
    except Exception as e:
        logger.error(f"❌ PubMed search error: {e}")
        return {
            'query': query,
            'search_type': search_type,
            'total_count': 0,
            'retrieved_count': 0,
            'pmids': [],
            'articles': [],
            'error': str(e)
        }


def get_pubmed_summaries(pmids: list) -> list:
    """
    Get summary information for a list of PMIDs using esummary.
    
    Args:
        pmids: List of PubMed IDs
        
    Returns:
        List of article summaries with basic metadata
    """
    if not pmids:
        return []
    
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    
    try:
        # Get summaries
        summary_url = f"{base_url}esummary.fcgi"
        summary_params = {
            'db': 'pubmed',
            'id': ','.join(pmids),
            'retmode': 'json'
        }
        
        response = requests.get(summary_url, params=summary_params, timeout=15)
        response.raise_for_status()
        summary_data = response.json()
        
        articles = []
        uids = summary_data.get('result', {}).get('uids', [])
        
        for uid in uids:
            article_data = summary_data.get('result', {}).get(uid, {})
            if article_data:
                # Extract key information
                authors = article_data.get('authors', [])
                author_names = [author.get('name', '') for author in authors[:5]]  # First 5 authors
                
                article = {
                    'pmid': uid,
                    'title': article_data.get('title', ''),
                    'authors': author_names,
                    'journal': article_data.get('fulljournalname', ''),
                    'pub_date': article_data.get('pubdate', ''),
                    'doi': article_data.get('elocationid', ''),  # Often contains DOI
                    'pmcid': article_data.get('pmcid', ''),
                    'publication_types': article_data.get('pubtype', [])
                }
                articles.append(article)
        
        logger.info(f"📄 Retrieved summaries for {len(articles)} articles")
        return articles
        
    except Exception as e:
        logger.error(f"❌ Error getting PubMed summaries: {e}")
        return []


def get_pubmed_author_sample(author_name: str, sample_size: int = 5) -> dict:
    """
    Get a sample of works by an author from PubMed with institutional information.
    
    Args:
        author_name: Author name to search for
        sample_size: Number of sample works to analyze in detail
        
    Returns:
        dict with author sample analysis including affiliations and name variants
    """
    try:
        logger.info(f"🔍 Getting PubMed author sample for: {author_name}")
        
        # Search for author
        search_result = pubmed_search_core(author_name, max_results=sample_size, search_type="author")
        
        if not search_result['pmids']:
            return {
                'author_name': author_name,
                'total_works': 0,
                'sample_works': [],
                'institutional_keywords': [],
                'name_variants': [],
                'email_addresses': []
            }
        
        # Get detailed information for sample
        sample_pmids = search_result['pmids'][:sample_size]
        detailed_articles = []
        all_affiliations = []
        name_variants = set()
        email_addresses = set()
        
        for pmid in sample_pmids:
            article_details = get_detailed_pubmed_article(pmid, author_name)
            if article_details:
                detailed_articles.append(article_details)
                
                # Extract affiliations and variants for target author
                for author_info in article_details.get('author_details', []):
                    if is_target_author(author_info, author_name):
                        all_affiliations.extend(author_info.get('affiliations', []))
                        
                        # Collect name variants
                        full_name = f"{author_info['first_name']} {author_info['last_name']}".strip()
                        if full_name:
                            name_variants.add(full_name)
                        
                        # Extract email addresses
                        for affil in author_info.get('affiliations', []):
                            emails = extract_emails_from_text(affil)
                            email_addresses.update(emails)
        
        # Extract institutional keywords
        institutional_keywords = extract_institutional_keywords(all_affiliations)
        
        return {
            'author_name': author_name,
            'total_works': search_result['total_count'],
            'sample_works': detailed_articles,
            'institutional_keywords': institutional_keywords,
            'name_variants': list(name_variants),
            'email_addresses': list(email_addresses),
            'sample_metadata': {
                'sample_size': len(detailed_articles),
                'affiliations_found': len(all_affiliations)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error in PubMed author sample: {e}")
        return {
            'author_name': author_name,
            'total_works': 0,
            'sample_works': [],
            'error': str(e)
        }


def get_detailed_pubmed_article(pmid: str, target_author: str) -> dict:
    """Get detailed article information including author affiliations"""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    
    try:
        fetch_url = f"{base_url}efetch.fcgi"
        fetch_params = {
            'db': 'pubmed',
            'id': pmid,
            'retmode': 'xml',
            'rettype': 'abstract'
        }
        
        response = requests.get(fetch_url, params=fetch_params, timeout=10)
        response.raise_for_status()
        
        # Parse XML
        root = ET.fromstring(response.text)
        article = root.find('.//PubmedArticle')
        
        if article is None:
            return None
        
        # Extract basic info
        title_elem = article.find('.//ArticleTitle')
        title = ''.join(title_elem.itertext()).strip() if title_elem is not None else ''
        
        journal_elem = article.find('.//Journal/Title')
        journal = journal_elem.text if journal_elem is not None else ''
        
        # Extract authors with affiliations
        author_details = []
        author_list = article.find('.//AuthorList')
        if author_list is not None:
            for author_elem in author_list.findall('Author'):
                author_info = extract_detailed_author_info(author_elem)
                author_details.append(author_info)
        
        return {
            'pmid': pmid,
            'title': title,
            'journal': journal,
            'author_details': author_details
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching detailed article {pmid}: {e}")
        return None


def extract_detailed_author_info(author_elem: ET.Element) -> dict:
    """Extract detailed author information from XML element"""
    author_info = {
        'last_name': '',
        'first_name': '',
        'initials': '',
        'affiliations': []
    }
    
    try:
        last_name = author_elem.find('LastName')
        if last_name is not None:
            author_info['last_name'] = last_name.text or ''
        
        first_name = author_elem.find('ForeName')
        if first_name is not None:
            author_info['first_name'] = first_name.text or ''
        
        initials = author_elem.find('Initials')
        if initials is not None:
            author_info['initials'] = initials.text or ''
        
        # Get affiliations
        affil_info = author_elem.find('AffiliationInfo')
        if affil_info is not None:
            for affil in affil_info.findall('Affiliation'):
                if affil.text:
                    author_info['affiliations'].append(affil.text.strip())
        
    except Exception:
        pass
    
    return author_info


def is_target_author(author_info: dict, target_name: str) -> bool:
    """Check if author_info matches target author name"""
    full_name = f"{author_info['first_name']} {author_info['last_name']}".strip().lower()
    target_lower = target_name.lower()
    
    # Simple similarity check
    return (target_lower in full_name or 
            full_name in target_lower or
            author_info['last_name'].lower() in target_lower)


def extract_emails_from_text(text: str) -> list:
    """Extract email addresses from text"""
    import re
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(email_pattern, text)


def extract_institutional_keywords(affiliations: list) -> list:
    """Extract common institutional keywords from affiliations"""
    if not affiliations:
        return []
    
    # Combine all affiliations
    all_text = ' '.join(affiliations).lower()
    
    # Common institutional keywords
    keywords = []
    institutional_terms = [
        'university', 'institute', 'college', 'school', 'center', 'centre',
        'hospital', 'laboratory', 'department', 'faculty', 'division',
        'max planck', 'harvard', 'stanford', 'mit', 'cambridge', 'oxford',
        'excellence cluster', 'cnrs', 'inserm', 'nih'
    ]
    
    for term in institutional_terms:
        if term in all_text:
            keywords.append(term)
    
    return keywords[:10]  # Return top 10


@mcp.tool(
    annotations={
        "title": "Search PubMed",
        "description": (
            "Search PubMed database for publications by author, DOI, title, or keywords. "
            "Provides basic article metadata including authors, journal, and publication info. "
            "Useful for cross-validation with OpenAlex data and discovering name variants."
        ),
        "readOnlyHint": True,
        "openWorldHint": True
    }
)
async def search_pubmed(
    query: str,
    search_type: str = "author",
    max_results: int = 20
) -> dict:
    """
    Search PubMed database for publications.
    
    Args:
        query: Search query (author name, DOI, title, or keywords)
        search_type: Type of search - "author", "doi", "title", or "keywords" (default: "author")
        max_results: Maximum number of results to return (default: 20, max: 50)
        
    Returns:
        dict: Search results with PMIDs, article metadata, and summary statistics
        
    Example usage:
        # Search for author
        search_pubmed("Ivan Matic", search_type="author", max_results=10)
        
        # Search by DOI
        search_pubmed("10.1038/nprot.2009.36", search_type="doi")
        
        # Search by keywords
        search_pubmed("ADP-ribosylation DNA repair", search_type="keywords")
    """
    # Validate parameters
    max_results = min(max(max_results, 1), 50)  # Cap at 50 for performance
    valid_types = ["author", "doi", "title", "keywords"]
    if search_type not in valid_types:
        search_type = "author"
    
    logger.info(f"🔍 PubMed search: '{query}' (type: {search_type}, max: {max_results})")
    
    result = pubmed_search_core(query, max_results, search_type)
    return result


@mcp.tool(
    annotations={
        "title": "PubMed Author Sample",
        "description": (
            "Get a detailed sample of works by an author from PubMed including "
            "institutional affiliations, name variants, and email addresses. "
            "Useful for cross-validation and institutional disambiguation."
        ),
        "readOnlyHint": True,
        "openWorldHint": True
    }
)
async def pubmed_author_sample(
    author_name: str,
    sample_size: int = 5
) -> dict:
    """
    Get detailed author sample from PubMed with institutional information.
    
    Args:
        author_name: Author name to search for (e.g., "Ivan Matic", "J Smith")
        sample_size: Number of recent works to analyze in detail (default: 5, max: 10)
        
    Returns:
        dict: Author analysis including:
        - total_works: Total number of works found in PubMed
        - sample_works: Detailed information for sample works
        - institutional_keywords: Common institutional terms found
        - name_variants: Different name formats found
        - email_addresses: Email addresses extracted from affiliations
        
    Example usage:
        # Get institutional profile for author
        pubmed_author_sample("Ivan Matic", sample_size=5)
    """
    # Validate parameters
    sample_size = min(max(sample_size, 1), 10)  # Cap at 10 for performance
    
    logger.info(f"🔍 PubMed author sample: '{author_name}' (sample: {sample_size})")
    
    result = get_pubmed_author_sample(author_name, sample_size)
    return result


# ============================================================================
# ORCID Integration Functions
# ============================================================================

async def search_orcid_by_name(name: str, affiliation: str = None, max_results: int = 10) -> dict:
    """
    Search ORCID by author name and optionally affiliation.
    
    Args:
        name: Author name to search
        affiliation: Optional affiliation to help disambiguation
        max_results: Maximum number of results to return
        
    Returns:
        dict: ORCID search results with author profiles
    """
    try:
        # ORCID Public API search endpoint
        base_url = "https://pub.orcid.org/v3.0/search"
        
        # Build search query
        query_parts = []
        if name:
            # Split name into parts for better matching
            name_parts = name.replace(",", "").split()
            if len(name_parts) >= 2:
                # Assume last part is family name, rest are given names
                family_name = name_parts[-1]
                given_names = " ".join(name_parts[:-1])
                query_parts.append(f'family-name:"{family_name}"')
                query_parts.append(f'given-names:"{given_names}"')
            else:
                query_parts.append(f'text:"{name}"')
        
        if affiliation:
            query_parts.append(f'affiliation-org-name:"{affiliation}"')
        
        query = " AND ".join(query_parts)
        
        params = {
            'q': query,
            'rows': min(max_results, 50),  # ORCID API limit
            'start': 0
        }
        
        headers = {
            'Accept': 'application/json',
            'User-Agent': f'alex-mcp (+{get_config()["OPENALEX_MAILTO"]})'
        }
        
        logger.info(f"🔍 ORCID search: '{query}' (max: {max_results})")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    results = []
                    for result in data.get('result', []):
                        orcid_id = result.get('orcid-identifier', {}).get('path', '')
                        
                        # Extract name information
                        person = result.get('person', {})
                        names = person.get('name', {})
                        given_names = names.get('given-names', {}).get('value', '') if names.get('given-names') else ''
                        family_name = names.get('family-name', {}).get('value', '') if names.get('family-name') else ''
                        
                        # Extract employment/affiliation info
                        employments = []
                        employment_summaries = result.get('employment-summary', [])
                        for emp in employment_summaries[:3]:  # Limit to top 3
                            org_name = emp.get('organization', {}).get('name', '')
                            if org_name:
                                employments.append(org_name)
                        
                        results.append({
                            'orcid_id': orcid_id,
                            'orcid_url': f'https://orcid.org/{orcid_id}' if orcid_id else '',
                            'given_names': given_names,
                            'family_name': family_name,
                            'full_name': f"{given_names} {family_name}".strip(),
                            'employments': employments,
                            'relevance_score': result.get('relevance-score', {}).get('value', 0)
                        })
                    
                    logger.info(f"📊 Found {len(results)} ORCID profiles")
                    
                    return {
                        'total_found': data.get('num-found', 0),
                        'results_returned': len(results),
                        'results': results
                    }
                else:
                    logger.warning(f"ORCID API error: {response.status}")
                    return {'total_found': 0, 'results_returned': 0, 'results': [], 'error': f'HTTP {response.status}'}
                    
    except Exception as e:
        logger.error(f"ORCID search error: {str(e)}")
        return {'total_found': 0, 'results_returned': 0, 'results': [], 'error': str(e)}


async def get_orcid_works(orcid_id: str, max_works: int = 20) -> dict:
    """
    Get works/publications for a specific ORCID ID.
    
    Args:
        orcid_id: ORCID identifier (e.g., "0000-0000-0000-0000")
        max_works: Maximum number of works to retrieve
        
    Returns:
        dict: Works information from ORCID profile
    """
    try:
        # Clean ORCID ID (remove URL if present)
        clean_orcid = orcid_id.replace('https://orcid.org/', '').replace('http://orcid.org/', '')
        if not re.match(r'^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$', clean_orcid):
            return {'error': 'Invalid ORCID format', 'works': []}
        
        # ORCID Public API works endpoint
        url = f"https://pub.orcid.org/v3.0/{clean_orcid}/works"
        
        headers = {
            'Accept': 'application/json',
            'User-Agent': f'alex-mcp (+{get_config()["OPENALEX_MAILTO"]})'
        }
        
        logger.info(f"🔍 Getting ORCID works: {clean_orcid} (max: {max_works})")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    works = []
                    work_summaries = data.get('group', [])[:max_works]
                    
                    for group in work_summaries:
                        for work_summary in group.get('work-summary', []):
                            title_info = work_summary.get('title', {})
                            title = title_info.get('title', {}).get('value', '') if title_info else ''
                            
                            journal_title = work_summary.get('journal-title', {}).get('value', '') if work_summary.get('journal-title') else ''
                            
                            # Extract publication date
                            pub_date = work_summary.get('publication-date')
                            pub_year = ''
                            if pub_date and pub_date.get('year'):
                                pub_year = pub_date['year'].get('value', '')
                            
                            # Extract external IDs (DOI, PMID, etc.)
                            external_ids = {}
                            for ext_id in work_summary.get('external-ids', {}).get('external-id', []):
                                id_type = ext_id.get('external-id-type', '')
                                id_value = ext_id.get('external-id-value', '')
                                if id_type and id_value:
                                    external_ids[id_type.lower()] = id_value
                            
                            works.append({
                                'title': title,
                                'journal': journal_title,
                                'publication_year': pub_year,
                                'external_ids': external_ids,
                                'doi': external_ids.get('doi', ''),
                                'pmid': external_ids.get('pmid', ''),
                                'type': work_summary.get('type', '')
                            })
                    
                    logger.info(f"📊 Retrieved {len(works)} works from ORCID")
                    
                    return {
                        'orcid_id': clean_orcid,
                        'total_works': len(works),
                        'works': works
                    }
                else:
                    logger.warning(f"ORCID works API error: {response.status}")
                    return {'error': f'HTTP {response.status}', 'works': []}
                    
    except Exception as e:
        logger.error(f"ORCID works error: {str(e)}")
        return {'error': str(e), 'works': []}


# ============================================================================
# ORCID MCP Tools
# ============================================================================

@mcp.tool(
    annotations={
        "title": "Search ORCID Authors",
        "description": (
            "Search ORCID database for author profiles by name and optionally affiliation. "
            "Provides ORCID IDs, verified names, and institutional affiliations for "
            "enhanced author disambiguation and verification."
        ),
        "readOnlyHint": True,
        "openWorldHint": True
    }
)
async def search_orcid_authors(
    name: str,
    affiliation: str = None,
    max_results: int = 10
) -> dict:
    """
    Search ORCID for author profiles by name and affiliation.
    
    Args:
        name: Author name to search (e.g., "John Smith", "Maria Garcia")
        affiliation: Optional institutional affiliation for disambiguation
        max_results: Maximum number of results to return (default: 10, max: 50)
        
    Returns:
        dict: ORCID search results with:
        - total_found: Total number of matches found
        - results_returned: Number of results returned
        - results: List of author profiles with ORCID IDs, names, and affiliations
        
    Example usage:
        # Basic name search
        search_orcid_authors("John Smith")
        
        # Search with affiliation for better disambiguation
        search_orcid_authors("Maria Garcia", "University of Barcelona")
    """
    # Validate parameters
    max_results = min(max(max_results, 1), 50)  # ORCID API limit
    
    result = await search_orcid_by_name(name, affiliation, max_results)
    return result


@mcp.tool(
    annotations={
        "title": "Get ORCID Works",
        "description": (
            "Retrieve publications/works from a specific ORCID profile. "
            "Useful for cross-validation with OpenAlex data and verifying "
            "author publication records."
        ),
        "readOnlyHint": True,
        "openWorldHint": True
    }
)
async def get_orcid_publications(
    orcid_id: str,
    max_works: int = 20
) -> dict:
    """
    Get publications/works from an ORCID profile.
    
    Args:
        orcid_id: ORCID identifier (e.g., "0000-0000-0000-0000" or full URL)
        max_works: Maximum number of works to retrieve (default: 20, max: 100)
        
    Returns:
        dict: Publications data with:
        - orcid_id: Cleaned ORCID identifier
        - total_works: Number of works found
        - works: List of publications with titles, journals, DOIs, PMIDs
        
    Example usage:
        # Get works for specific ORCID
        get_orcid_publications("0000-0000-0000-0000")
        
        # Get limited number of works
        get_orcid_publications("0000-0000-0000-0000", max_works=10)
    """
    # Validate parameters
    max_works = min(max(max_works, 1), 100)  # Reasonable limit
    
    result = await get_orcid_works(orcid_id, max_works)
    return result


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