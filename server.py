#!/usr/bin/env python3
"""
OpenAlex Author Disambiguation MCP Server

A professional MCP server for author disambiguation and institution resolution using OpenAlex.org API.
Built following MCP best practices with FastMCP for clean, maintainable code.

Features:
- ML-powered author disambiguation with confidence scoring
- Institution name resolution and abbreviation expansion  
- ORCID integration for highest accuracy
- Career analysis and publication metrics
- Full MCP protocol compliance

Author: OpenAlex MCP Team
License: MIT
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import re

import httpx
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("openalex-author-disambiguation")

# Constants
OPENALEX_BASE_URL = "https://api.openalex.org"
USER_AGENT = "OpenAlex-MCP-Server/1.0 (research@example.com)"

# Global HTTP client
http_client: Optional[httpx.AsyncClient] = None

@dataclass
class AuthorProfile:
    """Simplified author profile for MCP responses"""
    openalex_id: str
    display_name: str
    orcid: Optional[str] = None
    institutions: List[str] = None
    works_count: int = 0
    cited_by_count: int = 0
    h_index: Optional[int] = None
    research_topics: List[str] = None
    confidence_score: float = 0.0
    match_reasons: List[str] = None
    career_stage: str = "Unknown"
    
    def __post_init__(self):
        if self.institutions is None:
            self.institutions = []
        if self.research_topics is None:
            self.research_topics = []
        if self.match_reasons is None:
            self.match_reasons = []

async def get_http_client() -> httpx.AsyncClient:
    """Get or create HTTP client with proper configuration"""
    global http_client
    if http_client is None:
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json"
        }
        http_client = httpx.AsyncClient(
            base_url=OPENALEX_BASE_URL,
            headers=headers,
            timeout=30.0
        )
    return http_client

async def cleanup_http_client():
    """Clean up HTTP client"""
    global http_client
    if http_client:
        await http_client.aclose()
        http_client = None

def calculate_confidence_score(author_data: Dict[str, Any], query_name: str, 
                             query_affiliation: Optional[str] = None,
                             query_field: Optional[str] = None) -> tuple[float, List[str]]:
    """Calculate confidence score and match reasons"""
    confidence = 0.6  # Base confidence for OpenAlex
    reasons = []
    
    display_name = author_data.get("display_name", "").lower()
    query_name_lower = query_name.lower()
    
    # Name matching
    if display_name == query_name_lower:
        confidence += 0.3
        reasons.append("Exact name match")
    elif query_name_lower in display_name or display_name in query_name_lower:
        confidence += 0.2
        reasons.append("Partial name match")
    
    # Alternative names
    alternatives = author_data.get("display_name_alternatives", [])
    for alt_name in alternatives:
        if query_name_lower in alt_name.lower():
            confidence += 0.1
            reasons.append("Alternative name match")
            break
    
    # ORCID presence
    if author_data.get("orcid"):
        confidence += 0.1
        reasons.append("ORCID verified")
    
    # Affiliation matching
    if query_affiliation:
        institutions = author_data.get("last_known_institutions", [])
        for inst in institutions:
            inst_name = inst.get("display_name", "").lower()
            if query_affiliation.lower() in inst_name:
                confidence += 0.2
                reasons.append(f"Affiliation match")
                break
    
    # Research field matching
    if query_field:
        concepts = author_data.get("x_concepts", [])
        for concept in concepts[:10]:
            concept_name = concept.get("display_name", "").lower()
            if query_field.lower() in concept_name:
                confidence += 0.15
                reasons.append(f"Research field match")
                break
    
    # Publication activity
    works_count = author_data.get("works_count", 0)
    if works_count > 10:
        confidence += 0.05
        reasons.append("Active researcher")
    
    return min(confidence, 1.0), reasons

def determine_career_stage(author_data: Dict[str, Any]) -> str:
    """Determine career stage based on metrics"""
    works_count = author_data.get("works_count", 0)
    h_index = author_data.get("summary_stats", {}).get("h_index", 0) or 0
    
    if works_count < 5:
        return "Early Career"
    elif h_index > 20:
        return "Senior Researcher"
    elif works_count > 50:
        return "Established Researcher"
    else:
        return "Mid-Career"

async def create_author_profile(author_data: Dict[str, Any], query_name: str,
                              query_affiliation: Optional[str] = None,
                              query_field: Optional[str] = None) -> AuthorProfile:
    """Create author profile from OpenAlex data"""
    
    # Extract basic information
    openalex_id = author_data.get("id", "")
    display_name = author_data.get("display_name", "")
    orcid = author_data.get("orcid")
    
    # Extract institutions
    institutions = [
        inst.get("display_name", "") 
        for inst in author_data.get("last_known_institutions", [])
    ]
    
    # Extract metrics
    works_count = author_data.get("works_count", 0)
    cited_by_count = author_data.get("cited_by_count", 0)
    summary_stats = author_data.get("summary_stats", {})
    h_index = summary_stats.get("h_index")
    
    # Extract research topics
    x_concepts = author_data.get("x_concepts", [])
    research_topics = [concept.get("display_name", "") for concept in x_concepts[:5]]
    
    # Calculate confidence and career stage
    confidence_score, match_reasons = calculate_confidence_score(
        author_data, query_name, query_affiliation, query_field
    )
    career_stage = determine_career_stage(author_data)
    
    return AuthorProfile(
        openalex_id=openalex_id,
        display_name=display_name,
        orcid=orcid,
        institutions=institutions,
        works_count=works_count,
        cited_by_count=cited_by_count,
        h_index=h_index,
        research_topics=research_topics,
        confidence_score=confidence_score,
        match_reasons=match_reasons,
        career_stage=career_stage
    )

# ============================================================================
# MCP TOOLS - Following official best practices
# ============================================================================

@mcp.tool(
    annotations={
        "title": "Disambiguate Author",
        "readOnlyHint": True,
        "openWorldHint": True
    }
)
async def disambiguate_author(
    name: str,
    affiliation: str = None,
    research_field: str = None,
    orcid: str = None,
    max_candidates: int = 5
) -> str:
    """
    Disambiguate an author using OpenAlex's ML-powered disambiguation system.
    
    Returns ranked candidates with confidence scores and detailed analysis.
    Perfect for identifying the correct author when multiple people share similar names.
    
    Args:
        name: Author name (required) - can be full name or surname
        affiliation: Institution name or affiliation to improve accuracy
        research_field: Research field, topic, or area of study
        orcid: ORCID identifier if known (provides highest confidence)
        max_candidates: Maximum number of candidates to return (1-25, default: 5)
    """
    try:
        client = await get_http_client()
        
        # Build search parameters
        params = {
            "per-page": min(max_candidates, 25),
            "select": "id,display_name,display_name_alternatives,orcid,last_known_institutions,works_count,cited_by_count,summary_stats,x_concepts"
        }
        
        # Primary search
        if orcid:
            params["filter"] = f"orcid:{orcid}"
        else:
            params["search"] = name
        
        # Add affiliation filter
        if affiliation:
            affiliation_filter = f'last_known_institutions.display_name.search:"{affiliation}"'
            if "filter" in params:
                params["filter"] += f",{affiliation_filter}"
            else:
                params["filter"] = affiliation_filter
        
        response = await client.get("/authors", params=params)
        response.raise_for_status()
        data = response.json()
        
        # Process results
        candidates = []
        for author_data in data.get("results", []):
            profile = await create_author_profile(
                author_data, name, affiliation, research_field
            )
            candidates.append(profile)
        
        # Sort by confidence
        candidates.sort(key=lambda x: x.confidence_score, reverse=True)
        
        # Format response
        if not candidates:
            return f"No authors found matching '{name}'"
        
        result = f"Found {len(candidates)} candidate(s) for '{name}':\n\n"
        
        for i, candidate in enumerate(candidates, 1):
            result += f"{i}. {candidate.display_name}\n"
            result += f"   OpenAlex ID: {candidate.openalex_id}\n"
            result += f"   Confidence: {candidate.confidence_score:.2f}\n"
            result += f"   Match reasons: {', '.join(candidate.match_reasons)}\n"
            if candidate.orcid:
                result += f"   ORCID: {candidate.orcid}\n"
            if candidate.institutions:
                result += f"   Institutions: {', '.join(candidate.institutions)}\n"
            result += f"   Career: {candidate.career_stage}\n"
            result += f"   Works: {candidate.works_count}, Citations: {candidate.cited_by_count:,}\n"
            if candidate.h_index:
                result += f"   H-index: {candidate.h_index}\n"
            if candidate.research_topics:
                result += f"   Topics: {', '.join(candidate.research_topics[:3])}\n"
            result += "\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error in disambiguate_author: {e}")
        return f"Error: {str(e)}"

@mcp.tool(
    annotations={
        "title": "Search Authors",
        "readOnlyHint": True,
        "openWorldHint": True
    }
)
async def search_authors(
    name: str,
    affiliation: str = None,
    research_field: str = None,
    limit: int = 10
) -> str:
    """
    Search for authors with advanced filtering capabilities.
    
    Useful for finding multiple authors or exploring author profiles
    in specific institutions or research areas.
    
    Args:
        name: Author name to search for
        affiliation: Filter by institution or affiliation
        research_field: Filter by research field or topic
        limit: Maximum number of results (1-25, default: 10)
    """
    try:
        client = await get_http_client()
        
        params = {
            "search": name,
            "per-page": min(limit, 25),
            "select": "id,display_name,orcid,last_known_institutions,works_count,cited_by_count,summary_stats,x_concepts"
        }
        
        # Add filters
        filters = []
        if affiliation:
            filters.append(f'last_known_institutions.display_name.search:"{affiliation}"')
        
        if filters:
            params["filter"] = ",".join(filters)
        
        response = await client.get("/authors", params=params)
        response.raise_for_status()
        data = response.json()
        
        results = data.get("results", [])
        if not results:
            return f"No authors found for '{name}'"
        
        result = f"Found {len(results)} author(s) for '{name}':\n\n"
        
        for i, author in enumerate(results, 1):
            institutions = [inst.get("display_name", "") for inst in author.get("last_known_institutions", [])]
            topics = [concept.get("display_name", "") for concept in author.get("x_concepts", [])[:3]]
            
            result += f"{i}. {author.get('display_name', 'Unknown')}\n"
            result += f"   OpenAlex ID: {author.get('id', '')}\n"
            if author.get("orcid"):
                result += f"   ORCID: {author.get('orcid')}\n"
            if institutions:
                result += f"   Institutions: {', '.join(institutions)}\n"
            result += f"   Works: {author.get('works_count', 0)}, Citations: {author.get('cited_by_count', 0):,}\n"
            if topics:
                result += f"   Topics: {', '.join(topics)}\n"
            result += "\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error in search_authors: {e}")
        return f"Error: {str(e)}"

@mcp.tool(
    annotations={
        "title": "Get Author Profile",
        "readOnlyHint": True,
        "openWorldHint": True
    }
)
async def get_author_profile(openalex_id: str) -> str:
    """
    Get detailed author profile by OpenAlex ID.
    
    Retrieves comprehensive information about a specific author
    including metrics, affiliations, and research areas.
    
    Args:
        openalex_id: OpenAlex author ID (e.g., 'A5023888391' or full URL)
    """
    try:
        client = await get_http_client()
        
        # Clean ID
        clean_id = openalex_id.replace("https://openalex.org/", "")
        if not clean_id.startswith("A"):
            clean_id = f"A{clean_id}"
        
        response = await client.get(f"/authors/{clean_id}")
        response.raise_for_status()
        author = response.json()
        
        # Extract information
        name = author.get("display_name", "Unknown")
        orcid = author.get("orcid")
        institutions = [inst.get("display_name", "") for inst in author.get("last_known_institutions", [])]
        works_count = author.get("works_count", 0)
        cited_by_count = author.get("cited_by_count", 0)
        
        summary_stats = author.get("summary_stats", {})
        h_index = summary_stats.get("h_index")
        i10_index = summary_stats.get("i10_index")
        
        topics = [concept.get("display_name", "") for concept in author.get("x_concepts", [])[:5]]
        career_stage = determine_career_stage(author)
        
        # Format response
        result = f"Author Profile: {name}\n"
        result += f"OpenAlex ID: {author.get('id', '')}\n"
        if orcid:
            result += f"ORCID: {orcid}\n"
        result += f"\nMetrics:\n"
        result += f"  Works: {works_count:,}\n"
        result += f"  Citations: {cited_by_count:,}\n"
        if h_index:
            result += f"  H-index: {h_index}\n"
        if i10_index:
            result += f"  i10-index: {i10_index}\n"
        result += f"  Career stage: {career_stage}\n"
        
        if institutions:
            result += f"\nInstitutions:\n"
            for inst in institutions:
                result += f"  • {inst}\n"
        
        if topics:
            result += f"\nResearch Topics:\n"
            for topic in topics:
                result += f"  • {topic}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error in get_author_profile: {e}")
        return f"Error: {str(e)}"

@mcp.tool(
    annotations={
        "title": "Resolve Institution",
        "readOnlyHint": True,
        "openWorldHint": True
    }
)
async def resolve_institution(institution_query: str) -> str:
    """
    Resolve institution name or abbreviation to full OpenAlex data.
    
    Automatically expands abbreviations and resolves partial names.
    Perfect for standardizing institution names across systems.
    
    Examples:
    - 'MIT' → 'Massachusetts Institute of Technology'
    - 'Stanford' → 'Stanford University'
    - 'Max Planck' → 'Max Planck Society'
    
    Args:
        institution_query: Institution name, abbreviation, or partial name
    """
    try:
        client = await get_http_client()
        
        params = {
            "search": institution_query,
            "per-page": 5,
            "select": "id,display_name,display_name_alternatives,country_code,type,homepage_url"
        }
        
        response = await client.get("/institutions", params=params)
        response.raise_for_status()
        data = response.json()
        
        institutions = data.get("results", [])
        if not institutions:
            return f"No institutions found for '{institution_query}'"
        
        # Score and find best match
        query_lower = institution_query.lower()
        best_match = None
        best_score = 0
        
        for inst in institutions:
            display_name = inst.get("display_name", "").lower()
            alternatives = [alt.lower() for alt in inst.get("display_name_alternatives", [])]
            
            score = 0
            if query_lower == display_name:
                score = 100
            elif query_lower in alternatives:
                score = 95
            elif query_lower in display_name:
                score = 80
            elif display_name.startswith(query_lower):
                score = 70
            else:
                # Word matching
                query_words = query_lower.split()
                name_words = display_name.split()
                matching_words = sum(1 for word in query_words if any(word in name_word for name_word in name_words))
                if matching_words > 0:
                    score = 50 + (matching_words / len(query_words)) * 20
            
            if score > best_score:
                best_score = score
                best_match = inst
        
        if not best_match:
            return f"No good match found for '{institution_query}'"
        
        # Format response
        result = f"Institution Resolution for '{institution_query}':\n\n"
        result += f"Best Match: {best_match.get('display_name', 'Unknown')}\n"
        result += f"OpenAlex ID: {best_match.get('id', '')}\n"
        result += f"Match Score: {best_score}/100\n"
        result += f"Country: {best_match.get('country_code', 'Unknown')}\n"
        result += f"Type: {best_match.get('type', 'Unknown')}\n"
        
        if best_match.get("homepage_url"):
            result += f"Homepage: {best_match.get('homepage_url')}\n"
        
        alternatives = best_match.get("display_name_alternatives", [])
        if alternatives:
            result += f"Alternative names: {', '.join(alternatives[:3])}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error in resolve_institution: {e}")
        return f"Error: {str(e)}"

@mcp.tool(
    annotations={
        "title": "Autocomplete Authors",
        "readOnlyHint": True,
        "openWorldHint": True
    }
)
async def autocomplete_authors(query: str, limit: int = 10) -> str:
    """
    Fast autocomplete search for authors.
    
    Provides quick author suggestions for type-ahead functionality
    and interactive applications.
    
    Args:
        query: Partial author name for autocomplete
        limit: Maximum number of suggestions (1-25, default: 10)
    """
    try:
        client = await get_http_client()
        
        # Use autocomplete endpoint if available, otherwise fallback to search
        try:
            response = await client.get("/autocomplete/authors", params={
                "q": query,
                "limit": min(limit, 25)
            })
            response.raise_for_status()
            data = response.json()
            suggestions = data.get("results", [])
        except:
            # Fallback to regular search
            response = await client.get("/authors", params={
                "search": query,
                "per-page": min(limit, 25),
                "select": "id,display_name,last_known_institutions"
            })
            response.raise_for_status()
            data = response.json()
            suggestions = data.get("results", [])
        
        if not suggestions:
            return f"No author suggestions found for '{query}'"
        
        result = f"Author suggestions for '{query}':\n\n"
        
        for i, suggestion in enumerate(suggestions, 1):
            name = suggestion.get("display_name", "Unknown")
            institutions = suggestion.get("last_known_institutions", [])
            inst_names = [inst.get("display_name", "") for inst in institutions[:2]]
            
            result += f"{i}. {name}"
            if inst_names:
                result += f" ({', '.join(inst_names)})"
            result += "\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error in autocomplete_authors: {e}")
        return f"Error: {str(e)}"

# ============================================================================
# ADDITIONAL HIGH-VALUE TOOLS - Research Intelligence Expansion
# ============================================================================

@mcp.tool(
    annotations={
        "title": "Search Works",
        "readOnlyHint": True,
        "openWorldHint": True
    }
)
async def search_works(
    query: str,
    author_name: str = None,
    publication_year: str = None,
    source_type: str = None,
    topic: str = None,
    sort_by: str = "relevance",
    limit: int = 20
) -> str:
    """
    Search for scholarly works (publications) with advanced filtering.
    
    Find research papers, books, datasets, and other scholarly documents
    across OpenAlex's database of 240M+ works.
    
    Args:
        query: Search query for title, abstract, or content
        author_name: Filter by author name
        publication_year: Filter by year (e.g., "2023" or "2020-2023")
        source_type: Filter by type ("journal-article", "book", "dataset", etc.)
        topic: Filter by research topic or field
        sort_by: Sort order ("relevance", "cited_by_count", "publication_date")
        limit: Maximum number of results (1-100, default: 20)
    """
    try:
        client = await get_http_client()
        
        params = {
            "search": query,
            "per-page": min(limit, 100),
            "select": "id,title,publication_year,type,cited_by_count,authorships,primary_topic,open_access,doi"
        }
        
        # Build filters
        filters = []
        
        if author_name:
            filters.append(f'authorships.author.display_name.search:"{author_name}"')
        
        if publication_year:
            if "-" in publication_year:
                start_year, end_year = publication_year.split("-")
                filters.append(f"publication_year:{start_year}-{end_year}")
            else:
                filters.append(f"publication_year:{publication_year}")
        
        if source_type:
            filters.append(f"type:{source_type}")
        
        if topic:
            filters.append(f'primary_topic.display_name.search:"{topic}"')
        
        if filters:
            params["filter"] = ",".join(filters)
        
        # Set sort order
        sort_options = {
            "relevance": "relevance_score:desc",
            "cited_by_count": "cited_by_count:desc",
            "publication_date": "publication_date:desc"
        }
        params["sort"] = sort_options.get(sort_by, "relevance_score:desc")
        
        response = await client.get("/works", params=params)
        response.raise_for_status()
        data = response.json()
        
        works = data.get("results", [])
        if not works:
            return f"No works found for query: '{query}'"
        
        result = f"Found {len(works)} work(s) for '{query}':\n\n"
        
        for i, work in enumerate(works, 1):
            # Extract authors
            authorships = work.get("authorships", [])
            authors = [auth.get("author", {}).get("display_name", "") for auth in authorships[:3]]
            author_text = ", ".join(authors)
            if len(authorships) > 3:
                author_text += f" (+{len(authorships) - 3} more)"
            
            # Extract topic
            primary_topic = work.get("primary_topic", {})
            topic_name = primary_topic.get("display_name", "Unknown topic")
            
            result += f"{i}. {work.get('title', 'Untitled')}\n"
            result += f"   Authors: {author_text}\n"
            result += f"   Year: {work.get('publication_year', 'Unknown')}\n"
            result += f"   Type: {work.get('type', 'Unknown')}\n"
            result += f"   Citations: {work.get('cited_by_count', 0):,}\n"
            result += f"   Topic: {topic_name}\n"
            result += f"   Open Access: {work.get('open_access', {}).get('is_oa', False)}\n"
            if work.get('doi'):
                result += f"   DOI: {work.get('doi')}\n"
            result += f"   OpenAlex ID: {work.get('id', '')}\n"
            result += "\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error in search_works: {e}")
        return f"Error: {str(e)}"

@mcp.tool(
    annotations={
        "title": "Get Work Details",
        "readOnlyHint": True,
        "openWorldHint": True
    }
)
async def get_work_details(work_id: str) -> str:
    """
    Get comprehensive details about a specific scholarly work.
    
    Retrieves detailed information about a publication including
    full author list, citations, references, and metadata.
    
    Args:
        work_id: OpenAlex work ID (e.g., 'W2741809807' or full URL)
    """
    try:
        client = await get_http_client()
        
        # Clean work ID
        clean_id = work_id.replace("https://openalex.org/", "")
        if not clean_id.startswith("W"):
            clean_id = f"W{clean_id}"
        
        response = await client.get(f"/works/{clean_id}")
        response.raise_for_status()
        work = response.json()
        
        # Extract information
        title = work.get("title", "Untitled")
        publication_year = work.get("publication_year", "Unknown")
        publication_date = work.get("publication_date", "Unknown")
        work_type = work.get("type", "Unknown")
        cited_by_count = work.get("cited_by_count", 0)
        
        # Extract authors
        authorships = work.get("authorships", [])
        authors_info = []
        for i, authorship in enumerate(authorships):
            author = authorship.get("author", {})
            institutions = authorship.get("institutions", [])
            inst_names = [inst.get("display_name", "") for inst in institutions]
            
            author_info = f"   {i+1}. {author.get('display_name', 'Unknown')}"
            if inst_names:
                author_info += f" ({', '.join(inst_names[:2])})"
            authors_info.append(author_info)
        
        # Extract venue information
        primary_location = work.get("primary_location", {})
        source = primary_location.get("source", {})
        venue_name = source.get("display_name", "Unknown venue")
        
        # Extract topics
        primary_topic = work.get("primary_topic", {})
        topics = work.get("topics", [])
        
        # Extract abstract
        abstract_index = work.get("abstract_inverted_index", {})
        abstract_text = "No abstract available"
        if abstract_index:
            # Reconstruct abstract from inverted index
            word_positions = []
            for word, positions in abstract_index.items():
                for pos in positions:
                    word_positions.append((pos, word))
            word_positions.sort()
            abstract_words = [word for _, word in word_positions]
            abstract_text = " ".join(abstract_words)
            if len(abstract_text) > 500:
                abstract_text = abstract_text[:500] + "..."
        
        # Format response
        result = f"Work Details: {title}\n"
        result += f"OpenAlex ID: {work.get('id', '')}\n"
        result += f"Publication Year: {publication_year}\n"
        result += f"Publication Date: {publication_date}\n"
        result += f"Type: {work_type}\n"
        result += f"Citations: {cited_by_count:,}\n"
        result += f"Venue: {venue_name}\n"
        
        if work.get("doi"):
            result += f"DOI: {work.get('doi')}\n"
        
        result += f"Open Access: {work.get('open_access', {}).get('is_oa', False)}\n"
        
        if primary_topic.get("display_name"):
            result += f"\nPrimary Topic: {primary_topic.get('display_name')}\n"
        
        if len(topics) > 1:
            other_topics = [t.get("display_name", "") for t in topics[1:4]]
            result += f"Other Topics: {', '.join(other_topics)}\n"
        
        result += f"\nAuthors ({len(authorships)} total):\n"
        result += "\n".join(authors_info[:10])
        if len(authorships) > 10:
            result += f"\n   ... and {len(authorships) - 10} more authors"
        
        result += f"\n\nAbstract:\n{abstract_text}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error in get_work_details: {e}")
        return f"Error: {str(e)}"

@mcp.tool(
    annotations={
        "title": "Search Topics",
        "readOnlyHint": True,
        "openWorldHint": True
    }
)
async def search_topics(
    query: str,
    level: int = None,
    limit: int = 20
) -> str:
    """
    Search and explore research topics with detailed information.
    
    Find research topics, fields, and areas of study with
    comprehensive metadata and research volume statistics.
    
    Args:
        query: Topic name or description to search for
        level: Topic hierarchy level (0-5, where 0 is most general)
        limit: Maximum number of topics to return (1-50, default: 20)
    """
    try:
        client = await get_http_client()
        
        params = {
            "search": query,
            "per-page": min(limit, 50),
            "select": "id,display_name,description,level,works_count,cited_by_count,subfield,field,domain"
        }
        
        if level is not None:
            params["filter"] = f"level:{level}"
        
        response = await client.get("/topics", params=params)
        response.raise_for_status()
        data = response.json()
        
        topics = data.get("results", [])
        if not topics:
            return f"No topics found for query: '{query}'"
        
        result = f"Found {len(topics)} topic(s) for '{query}':\n\n"
        
        for i, topic in enumerate(topics, 1):
            # Calculate relevance score
            display_name = topic.get("display_name", "").lower()
            query_lower = query.lower()
            
            relevance = 0.0
            if query_lower == display_name:
                relevance = 1.0
            elif query_lower in display_name:
                relevance = 0.8
            elif any(word in display_name for word in query_lower.split()):
                relevance = 0.6
            else:
                relevance = 0.4
            
            # Extract hierarchy
            domain = topic.get("domain", {}).get("display_name", "") if topic.get("domain") else ""
            field = topic.get("field", {}).get("display_name", "") if topic.get("field") else ""
            subfield = topic.get("subfield", {}).get("display_name", "") if topic.get("subfield") else ""
            
            result += f"{i}. {topic.get('display_name', 'Unknown')}\n"
            result += f"   Level: {topic.get('level', 'Unknown')}\n"
            result += f"   Relevance: {relevance:.2f}\n"
            result += f"   Works: {topic.get('works_count', 0):,}\n"
            result += f"   Citations: {topic.get('cited_by_count', 0):,}\n"
            
            if domain or field or subfield:
                hierarchy = " > ".join(filter(None, [domain, field, subfield]))
                result += f"   Hierarchy: {hierarchy}\n"
            
            if topic.get("description"):
                desc = topic.get("description", "")
                if len(desc) > 150:
                    desc = desc[:150] + "..."
                result += f"   Description: {desc}\n"
            
            result += f"   OpenAlex ID: {topic.get('id', '')}\n"
            result += "\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error in search_topics: {e}")
        return f"Error: {str(e)}"

@mcp.tool(
    annotations={
        "title": "Analyze Text Aboutness",
        "readOnlyHint": True,
        "openWorldHint": True
    }
)
async def analyze_text_aboutness(
    title: str,
    abstract: str = None
) -> str:
    """
    Analyze text to determine research topics, keywords, and concepts.
    
    Uses OpenAlex's machine learning models to classify text and identify
    relevant research areas, topics, and concepts.
    
    Args:
        title: Title of the text to analyze (required)
        abstract: Abstract or description text (optional, improves accuracy)
    """
    try:
        client = await get_http_client()
        
        # Validate input length
        total_text = title + (abstract or "")
        if len(total_text) < 20:
            return "Error: Text too short (minimum 20 characters)"
        if len(total_text) > 2000:
            return "Error: Text too long (maximum 2000 characters)"
        
        params = {"title": title}
        if abstract:
            params["abstract"] = abstract
        
        response = await client.get("/text", params=params)
        response.raise_for_status()
        data = response.json()
        
        # Extract results
        meta = data.get("meta", {})
        keywords = data.get("keywords", [])
        primary_topic = data.get("primary_topic", {})
        topics = data.get("topics", [])
        concepts = data.get("concepts", [])
        
        result = f"Text Analysis Results:\n"
        result += f"Title: {title}\n"
        if abstract:
            result += f"Abstract: {abstract[:100]}{'...' if len(abstract) > 100 else ''}\n"
        result += "\n"
        
        # Primary topic
        if primary_topic:
            result += f"Primary Topic: {primary_topic.get('display_name', 'Unknown')}\n"
            result += f"  Confidence: {primary_topic.get('score', 0):.3f}\n"
            result += f"  Level: {primary_topic.get('level', 'Unknown')}\n"
            result += "\n"
        
        # Keywords
        if keywords:
            result += f"Keywords ({len(keywords)} found):\n"
            for keyword in keywords[:5]:
                result += f"  • {keyword.get('display_name', 'Unknown')} (score: {keyword.get('score', 0):.3f})\n"
            result += "\n"
        
        # Additional topics
        if len(topics) > 1:
            result += f"Additional Topics:\n"
            for topic in topics[1:4]:
                result += f"  • {topic.get('display_name', 'Unknown')} (score: {topic.get('score', 0):.3f})\n"
            result += "\n"
        
        # Concepts
        if concepts:
            result += f"Related Concepts:\n"
            for concept in concepts[:5]:
                result += f"  • {concept.get('display_name', 'Unknown')} (score: {concept.get('score', 0):.3f})\n"
            result += "\n"
        
        # Summary statistics
        result += f"Analysis Summary:\n"
        result += f"  Keywords found: {meta.get('keywords_count', 0)}\n"
        result += f"  Topics found: {meta.get('topics_count', 0)}\n"
        result += f"  Concepts found: {meta.get('concepts_count', 0)}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error in analyze_text_aboutness: {e}")
        return f"Error: {str(e)}"

@mcp.tool(
    annotations={
        "title": "Search Sources",
        "readOnlyHint": True,
        "openWorldHint": True
    }
)
async def search_sources(
    query: str,
    source_type: str = None,
    subject_area: str = None,
    limit: int = 20
) -> str:
    """
    Search for publication sources (journals, conferences, repositories).
    
    Find journals, conferences, books, and other publication venues
    with detailed metrics and information.
    
    Args:
        query: Source name or description to search for
        source_type: Filter by type ("journal", "conference", "repository", "book")
        subject_area: Filter by subject area or field
        limit: Maximum number of sources to return (1-50, default: 20)
    """
    try:
        client = await get_http_client()
        
        params = {
            "search": query,
            "per-page": min(limit, 50),
            "select": "id,display_name,type,host_organization,works_count,cited_by_count,summary_stats,issn,homepage_url"
        }
        
        # Add filters
        filters = []
        if source_type:
            filters.append(f"type:{source_type}")
        
        if filters:
            params["filter"] = ",".join(filters)
        
        response = await client.get("/sources", params=params)
        response.raise_for_status()
        data = response.json()
        
        sources = data.get("results", [])
        if not sources:
            return f"No sources found for query: '{query}'"
        
        result = f"Found {len(sources)} source(s) for '{query}':\n\n"
        
        for i, source in enumerate(sources, 1):
            # Extract metrics
            works_count = source.get("works_count", 0)
            cited_by_count = source.get("cited_by_count", 0)
            summary_stats = source.get("summary_stats", {})
            h_index = summary_stats.get("h_index", 0)
            
            # Extract host organization
            host_org = source.get("host_organization", "")
            
            result += f"{i}. {source.get('display_name', 'Unknown')}\n"
            result += f"   Type: {source.get('type', 'Unknown')}\n"
            result += f"   Works: {works_count:,}\n"
            result += f"   Citations: {cited_by_count:,}\n"
            if h_index:
                result += f"   H-index: {h_index}\n"
            
            if host_org:
                result += f"   Host: {host_org}\n"
            
            issn = source.get("issn", [])
            if issn:
                result += f"   ISSN: {', '.join(issn)}\n"
            
            if source.get("homepage_url"):
                result += f"   Homepage: {source.get('homepage_url')}\n"
            
            result += f"   OpenAlex ID: {source.get('id', '')}\n"
            result += "\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error in search_sources: {e}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    # Run the server
    logger.info("OpenAlex Author Disambiguation MCP Server starting...")
    mcp.run()
