#!/usr/bin/env python3
"""
OpenAlex Author Disambiguation MCP Server

A professional MCP server for author disambiguation and institution resolution using OpenAlex.org API.
Built following MCP best practices with the FastMCP library.

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
from typing import Any, Dict, List, Optional, Sequence
from dataclasses import dataclass
import json

import httpx
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("OpenAlex Academic Research")

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
    career_stage: Optional[str] = "Unknown"
    
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
# MCP TOOL IMPLEMENTATIONS
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
    affiliation: Optional[str] = None,
    research_field: Optional[str] = None,
    orcid: Optional[str] = None,
    max_candidates: Optional[int] = 20
) -> str:
    """
    Disambiguate an author using OpenAlex's ML-powered disambiguation system.
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
    affiliation: Optional[str] = None,
    research_field: Optional[str] = None,
    limit: Optional[int] = 20
) -> str:
    """
    Search for authors with advanced filtering capabilities.
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
async def get_author_profile(openalex_id: str, max_works: int = 50) -> str:
    """
    Get detailed author profile by OpenAlex ID, including recent articles.
    """
    try:
        client = await get_http_client()
        
        # Clean ID
        clean_id = openalex_id.replace("https://openalex.org/", "")
        if not clean_id.startswith("A"):
            clean_id = f"A{clean_id}"
        
        # Get author profile
        response = await client.get(f"/authors/{clean_id}")
        response.raise_for_status()
        author = response.json()
        
        # Extract basic information
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
        
        # Get author's works (articles)
        works_params = {
            "filter": f"author.id:{clean_id},type:article",
            "sort": "publication_date:desc",
            "per-page": max_works,
            "select": "id,title,publication_year,publication_date,type,authorships,primary_location,cited_by_count,abstract_inverted_index,is_retracted,is_paratext,has_fulltext,concepts,indexed_in,topics,corresponding_author_ids,corresponding_institution_ids,keywords,ids"
        }
        
        works_response = await client.get("/works", params=works_params)
        works_response.raise_for_status()
        works_data = works_response.json()
        articles = works_data.get("results", [])
        
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
        
        # Add recent articles
        if articles:
            result += f"\nRecent Articles ({len(articles)}):\n"
            for i, article in enumerate(articles, 1):
                # Extract basic article info
                title = article.get("title", "Untitled")
                year = article.get("publication_year", "Unknown")
                pub_date = article.get("publication_date", "Unknown date")
                citations = article.get("cited_by_count", 0)
                is_retracted = article.get("is_retracted", False)
                is_paratext = article.get("is_paratext", False)
                has_fulltext = article.get("has_fulltext", False)
                
                # Extract venue
                venue = article.get("primary_location", {}).get("source", {}).get("display_name", "Unknown venue")
                
                # Extract indexing information
                indexed_in = article.get("indexed_in", [])
                indexed_str = ", ".join(indexed_in) if indexed_in else "None"
                
                # Extract IDs
                ids = article.get("ids", {})
                id_strings = []
                if ids.get("doi"):
                    id_strings.append(f"DOI: {ids.get('doi')}")
                if ids.get("pmid"):
                    id_strings.append(f"PMID: {ids.get('pmid')}")
                if ids.get("pmcid"):
                    id_strings.append(f"PMCID: {ids.get('pmcid')}")
                if ids.get("mag"):
                    id_strings.append(f"MAG: {ids.get('mag')}")
                
                # Extract keywords
                keywords = article.get("keywords", [])
                keyword_list = []
                for keyword_obj in keywords:
                    if isinstance(keyword_obj, dict):
                        keyword_list.append(keyword_obj.get("keyword", ""))
                    else:
                        keyword_list.append(str(keyword_obj))
                
                # Extract abstract
                abstract = ""
                if article.get("abstract_inverted_index"):
                    abstract_words = []
                    for position, word in sorted(article.get("abstract_inverted_index").items()):
                        abstract_words.append(word)
                    abstract = " ".join(abstract_words)
                    if len(abstract) > 200:
                        abstract = abstract[:197] + "..."
                
                # Extract concepts/topics
                article_concepts = []
                for concept in article.get("concepts", [])[:3]:
                    concept_name = concept.get("display_name", "Unknown")
                    concept_score = concept.get("score", 0)
                    article_concepts.append(f"{concept_name} ({concept_score:.2f})")
                
                # Extract co-authors
                co_authors = []
                corresponding_authors = []
                corresponding_institutions = []
                
                # Get corresponding author and institution IDs
                corresponding_author_ids = article.get("corresponding_author_ids", [])
                corresponding_institution_ids = article.get("corresponding_institution_ids", [])
                
                # Process authorships
                for authorship in article.get("authorships", []):
                    author_data = authorship.get("author", {})
                    author_name = author_data.get("display_name", "Unknown")
                    author_id = author_data.get("id", "")
                    
                    # Skip the main author
                    if author_id == author.get("id"):
                        continue
                    
                    # Add to co-authors
                    co_authors.append(author_name)
                    
                    # Check if this is a corresponding author
                    if author_id in corresponding_author_ids:
                        corresponding_authors.append(author_name)
                    
                    # Get institutions for this author
                    for institution in authorship.get("institutions", []):
                        inst_id = institution.get("id", "")
                        inst_name = institution.get("display_name", "Unknown")
                        
                        # Check if this is a corresponding institution
                        if inst_id in corresponding_institution_ids:
                            corresponding_institutions.append(inst_name)
                
                # Format article entry
                result += f"  {i}. {title}\n"
                result += f"     Published: {pub_date} ({year}) in {venue}\n"
                result += f"     Citations: {citations}\n"
                
                # Add status flags
                status_flags = []
                if is_retracted:
                    status_flags.append("RETRACTED")
                if is_paratext:
                    status_flags.append("PARATEXT")
                if has_fulltext:
                    status_flags.append("Full text available")
                
                if status_flags:
                    result += f"     Status: {', '.join(status_flags)}\n"
                
                if indexed_in:
                    result += f"     Indexed in: {indexed_str}\n"
                
                if id_strings:
                    result += f"     IDs: {' | '.join(id_strings)}\n"
                
                if article_concepts:
                    result += f"     Topics: {', '.join(article_concepts)}\n"
                
                if keyword_list:
                    # Limit to first 5 keywords if there are many
                    displayed_keywords = keyword_list[:5]
                    if len(keyword_list) > 5:
                        displayed_keywords.append("...")
                    result += f"     Keywords: {', '.join(displayed_keywords)}\n"
                
                if co_authors:
                    # Limit to first 3 co-authors if there are many
                    displayed_coauthors = co_authors[:3]
                    if len(co_authors) > 3:
                        displayed_coauthors.append("et al.")
                    result += f"     Co-authors: {', '.join(displayed_coauthors)}\n"
                
                if corresponding_authors:
                    result += f"     Corresponding author(s): {', '.join(corresponding_authors)}\n"
                
                if corresponding_institutions:
                    result += f"     Corresponding institution(s): {', '.join(corresponding_institutions)}\n"
                
                if abstract:
                    result += f"     Abstract: {abstract}\n"
                
                result += f"     OpenAlex ID: {article.get('id', '')}\n"
                result += "\n"
        
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

# ============================================================================
# ADDITIONAL MCP TOOL IMPLEMENTATIONS
# ============================================================================

@mcp.tool(
    annotations={
        "title": "Author Autocomplete",
        "readOnlyHint": True,
        "openWorldHint": True
    }
)
async def author_autocomplete(
    query: str,
    limit: Optional[int] = 10
) -> str:
    """
    Get autocomplete suggestions for author names.
    """
    try:
        client = await get_http_client()
        
        params = {
            "q": query,
            "filter": "entity:author",
            "per-page": min(limit, 25)
        }
        
        response = await client.get("/autocomplete", params=params)
        response.raise_for_status()
        data = response.json()
        
        results = data.get("results", [])
        if not results:
            return f"No author suggestions found for '{query}'"
        
        result = f"Author suggestions for '{query}':\n\n"
        
        for i, suggestion in enumerate(results, 1):
            result += f"{i}. {suggestion.get('display_name', 'Unknown')}\n"
            result += f"   ID: {suggestion.get('id', '')}\n"
            if suggestion.get("hint"):
                result += f"   Hint: {suggestion.get('hint')}\n"
            result += "\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error in author_autocomplete: {e}")
        return f"Error: {str(e)}"

@mcp.tool(
    annotations={
        "title": "Search Works",
        "readOnlyHint": True,
        "openWorldHint": True
    }
)
async def search_works(
    query: Optional[str] = None,
    author_name: Optional[str] = None,
    publication_year: Optional[str] = None,
    from_year: Optional[str] = None,
    to_year: Optional[str] = None,
    source_type: Optional[str] = None,
    topic: Optional[str] = None,
    sort_by: Optional[str] = "relevance",
    limit: Optional[int] = 20
) -> str:
    """
    Search for scholarly works (publications) with advanced filtering.
    
    All parameters are optional. If no parameters are provided, recent works will be returned.
    For date ranges, you can either use publication_year with a range format (e.g., "2020-2023")
    or use the from_year and to_year parameters separately.
    """
    try:
        # If no search criteria are provided, we'll return recent works
        default_search = not any([query, author_name, publication_year, from_year, to_year, source_type, topic])
        
        client = await get_http_client()
        
        # Initialize parameters
        params = {
            "per-page": min(limit or 20, 100),
            "select": "id,title,publication_year,type,open_access,authorships,primary_location,cited_by_count,abstract_inverted_index"
        }
        
        # For default search with no parameters, get recent works
        if default_search:
            params["sort"] = "publication_date:desc"
            # No need to add any filters, just get the most recent works
        
        # Add search query if provided
        if query:
            params["search"] = query
        
        # Add filters
        filters = []
        
        if author_name:
            filters.append(f'author.display_name.search:"{author_name}"')
        
        # Handle publication year filtering with multiple options
        if publication_year:
            # Handle range like "2020-2023" or single year like "2023"
            if "-" in publication_year:
                start_year, end_year = publication_year.split("-")
                filters.append(f'publication_year:>={start_year},<={end_year}')
            else:
                filters.append(f'publication_year:{publication_year}')
        else:
            # Handle from_year and to_year if provided
            if from_year and to_year:
                filters.append(f'publication_year:>={from_year},<={to_year}')
            elif from_year:
                filters.append(f'publication_year:>={from_year}')
            elif to_year:
                filters.append(f'publication_year:<={to_year}')
        
        if source_type:
            filters.append(f'type:{source_type}')
        
        if topic:
            filters.append(f'concepts.display_name.search:"{topic}"')
        
        if filters:
            params["filter"] = ",".join(filters)
        
        # Add sorting
        if sort_by:
            if sort_by == "cited_by_count":
                params["sort"] = "cited_by_count:desc"
            elif sort_by == "publication_date":
                params["sort"] = "publication_date:desc"
        
        response = await client.get("/works", params=params)
        response.raise_for_status()
        data = response.json()
        
        results = data.get("results", [])
        if not results:
            return f"No works found matching your criteria"
        
        # Safely get the count
        meta = data.get("meta", {})
        count = meta.get("count", len(results)) if meta else len(results)
        
        # Create a safe query display
        query_display = f"'{query}'" if query else "your criteria"
        result = f"Found {count} works matching {query_display}:\n\n"
        
        for i, work in enumerate(results, 1):
            # Extract authors
            authors = []
            for authorship in work.get("authorships", [])[:3]:
                author_name = authorship.get("author", {}).get("display_name", "Unknown")
                authors.append(author_name)
            
            if len(work.get("authorships", [])) > 3:
                authors.append("et al.")
            
            # Extract venue
            venue = work.get("primary_location", {}).get("source", {}).get("display_name", "Unknown venue")
            
            # Extract abstract
            abstract = ""
            if work.get("abstract_inverted_index"):
                abstract_words = []
                for position, word in sorted(work.get("abstract_inverted_index").items()):
                    abstract_words.append(word)
                abstract = " ".join(abstract_words)
                if len(abstract) > 200:
                    abstract = abstract[:197] + "..."
            
            result += f"{i}. {work.get('title', 'Untitled')}\n"
            result += f"   Authors: {', '.join(authors)}\n"
            result += f"   Published: {work.get('publication_year', 'Unknown')} in {venue}\n"
            result += f"   Type: {work.get('type', 'Unknown')}\n"
            result += f"   Citations: {work.get('cited_by_count', 0)}\n"
            result += f"   Open Access: {work.get('open_access', {}).get('is_oa', False)}\n"
            result += f"   OpenAlex ID: {work.get('id', '')}\n"
            if abstract:
                result += f"   Abstract: {abstract}\n"
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
    """
    try:
        client = await get_http_client()
        
        # Clean ID
        clean_id = work_id.replace("https://openalex.org/", "")
        if not clean_id.startswith("W"):
            clean_id = f"W{clean_id}"
        
        response = await client.get(f"/works/{clean_id}")
        response.raise_for_status()
        work = response.json()
        
        # Extract basic information
        title = work.get("title", "Untitled")
        publication_year = work.get("publication_year", "Unknown")
        type_name = work.get("type", "Unknown")
        cited_by_count = work.get("cited_by_count", 0)
        
        # Extract authors
        authors = []
        for authorship in work.get("authorships", []):
            author_name = authorship.get("author", {}).get("display_name", "Unknown")
            author_id = authorship.get("author", {}).get("id", "")
            institutions = []
            for institution in authorship.get("institutions", []):
                institutions.append(institution.get("display_name", "Unknown"))
            
            author_info = f"{author_name} ({author_id})"
            if institutions:
                author_info += f" - {', '.join(institutions)}"
            authors.append(author_info)
        
        # Extract venue
        venue = work.get("primary_location", {}).get("source", {})
        venue_name = venue.get("display_name", "Unknown venue")
        venue_type = venue.get("type", "Unknown")
        venue_id = venue.get("id", "")
        
        # Extract abstract
        abstract = ""
        if work.get("abstract_inverted_index"):
            abstract_words = []
            for position, word in sorted(work.get("abstract_inverted_index").items()):
                abstract_words.append(word)
            abstract = " ".join(abstract_words)
        
        # Extract concepts/topics
        concepts = []
        for concept in work.get("concepts", [])[:5]:
            concept_name = concept.get("display_name", "Unknown")
            concept_score = concept.get("score", 0)
            concepts.append(f"{concept_name} (score: {concept_score:.2f})")
        
        # Extract open access information
        oa_status = work.get("open_access", {}).get("oa_status", "Unknown")
        is_oa = work.get("open_access", {}).get("is_oa", False)
        
        # Format response
        result = f"Work Details: {title}\n\n"
        result += f"Basic Information:\n"
        result += f"  OpenAlex ID: {work.get('id', '')}\n"
        result += f"  DOI: {work.get('doi', 'None')}\n"
        result += f"  Type: {type_name}\n"
        result += f"  Published: {publication_year}\n"
        result += f"  Citations: {cited_by_count}\n"
        result += f"  Open Access: {is_oa} (Status: {oa_status})\n"
        
        result += f"\nAuthors:\n"
        for i, author in enumerate(authors, 1):
            result += f"  {i}. {author}\n"
        
        result += f"\nVenue:\n"
        result += f"  Name: {venue_name}\n"
        result += f"  Type: {venue_type}\n"
        result += f"  ID: {venue_id}\n"
        
        if concepts:
            result += f"\nConcepts/Topics:\n"
            for concept in concepts:
                result += f"  • {concept}\n"
        
        if abstract:
            result += f"\nAbstract:\n{abstract}\n"
        
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
    query: Optional[str] = None,
    level: Optional[int] = None,
    limit: Optional[int] = 20
) -> str:
    """
    Search and explore research topics with detailed information.
    """
    try:
        # If no query is provided, return popular topics
        default_search = not query
            
        client = await get_http_client()
        
        params = {
            "per-page": min(limit, 50),
            "select": "id,display_name,description,level,works_count,cited_by_count,related_concepts"
        }
        
        # For default search, get popular topics sorted by works count
        if default_search:
            params["sort"] = "works_count:desc"
        else:
            params["search"] = query
        
        # Add filters
        filters = []
        if level is not None:
            filters.append(f'level:{level}')
        
        if filters:
            params["filter"] = ",".join(filters)
        
        response = await client.get("/concepts", params=params)
        response.raise_for_status()
        data = response.json()
        
        results = data.get("results", [])
        if not results:
            return f"No topics found matching your criteria"
        
        # Safely get the count
        meta = data.get("meta", {})
        count = meta.get("count", len(results)) if meta else len(results)
        
        # Create a safe query display
        query_display = f"'{query}'" if query else "your criteria"
        result = f"Found {count} topics matching {query_display}:\n\n"
        
        for i, topic in enumerate(results, 1):
            # Extract related concepts
            related = []
            for related_concept in topic.get("related_concepts", [])[:3]:
                related.append(related_concept.get("display_name", "Unknown"))
            
            description = topic.get("description", "No description available")
            if len(description) > 200:
                description = description[:197] + "..."
            
            result += f"{i}. {topic.get('display_name', 'Unknown')}\n"
            result += f"   Level: {topic.get('level', 'Unknown')} (0=general, 5=specific)\n"
            result += f"   Works: {topic.get('works_count', 0):,}, Citations: {topic.get('cited_by_count', 0):,}\n"
            result += f"   Description: {description}\n"
            if related:
                result += f"   Related topics: {', '.join(related)}\n"
            result += f"   OpenAlex ID: {topic.get('id', '')}\n"
            result += "\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error in search_topics: {e}")
        return f"Error: {str(e)}"

@mcp.tool(
    annotations={
        "title": "Analyze Topics",
        "readOnlyHint": True,
        "openWorldHint": True
    }
)
async def analyze_topics(
    title: Optional[str] = None,
    abstract: Optional[str] = None
) -> str:
    """
    Analyze text to determine research topics, keywords, and concepts using OpenAlex.
    """
    try:
        # Check if at least title is provided
        if not title:
            return "Error: A title must be provided for topic analysis."
            
        client = await get_http_client()
        
        # First, search for works with similar title to get concepts
        params = {
            "search": title,
            "per-page": 5,
            "select": "id,title,concepts"
        }
        
        response = await client.get("/works", params=params)
        response.raise_for_status()
        data = response.json()
        
        results = data.get("results", [])
        if not results:
            return f"No similar works found to analyze topics for '{title}'"
        
        # Collect concepts from all similar works
        all_concepts = {}
        for work in results:
            for concept in work.get("concepts", []):
                concept_id = concept.get("id")
                if concept_id in all_concepts:
                    all_concepts[concept_id]["score"] += concept.get("score", 0)
                    all_concepts[concept_id]["count"] += 1
                else:
                    all_concepts[concept_id] = {
                        "id": concept_id,
                        "display_name": concept.get("display_name", "Unknown"),
                        "level": concept.get("level", 0),
                        "score": concept.get("score", 0),
                        "count": 1
                    }
        
        # Calculate average scores and sort by score
        for concept_id, concept in all_concepts.items():
            concept["avg_score"] = concept["score"] / concept["count"]
        
        sorted_concepts = sorted(
            all_concepts.values(), 
            key=lambda x: x["avg_score"], 
            reverse=True
        )
        
        # Format response
        result = f"Topic Analysis for: '{title}'\n\n"
        
        if abstract:
            result += f"Abstract: {abstract[:100]}...\n\n"
        
        result += f"Identified Topics (from {len(results)} similar works):\n\n"
        
        # Group by level
        by_level = {}
        for concept in sorted_concepts[:20]:  # Top 20 concepts
            level = concept["level"]
            if level not in by_level:
                by_level[level] = []
            by_level[level].append(concept)
        
        # Display by level
        for level in sorted(by_level.keys()):
            level_name = {
                0: "General Areas",
                1: "Disciplines",
                2: "Domains",
                3: "Fields",
                4: "Subfields",
                5: "Specific Topics"
            }.get(level, f"Level {level}")
            
            result += f"{level_name}:\n"
            for concept in by_level[level]:
                result += f"  • {concept['display_name']} (confidence: {concept['avg_score']:.2f})\n"
            result += "\n"
        
        # Add recommendations
        result += "Recommendations:\n"
        result += "  • Consider using these topics as keywords in your manuscript\n"
        result += "  • Explore the top topics to find related literature\n"
        result += "  • Use specific topics (levels 4-5) for targeted literature searches\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error in analyze_topics: {e}")
        return f"Error: {str(e)}"

@mcp.tool(
    annotations={
        "title": "Search Sources",
        "readOnlyHint": True,
        "openWorldHint": True
    }
)
async def search_sources(
    query: Optional[str] = None,
    source_type: Optional[str] = None,
    subject_area: Optional[str] = None,
    limit: Optional[int] = 20
) -> str:
    """
    Search for publication sources (journals, conferences, repositories).
    """
    try:
        # If no search criteria are provided, return popular sources
        default_search = not any([query, source_type, subject_area])
            
        client = await get_http_client()
        
        params = {
            "per-page": min(limit, 50),
            "select": "id,display_name,type,publisher,country_code,is_oa,is_in_doaj,homepage_url,works_count,cited_by_count,summary_stats"
        }
        
        # For default search, get popular sources sorted by works count
        if default_search:
            params["sort"] = "works_count:desc"
        elif query:
            params["search"] = query
        
        # Add filters
        filters = []
        if source_type:
            filters.append(f'type:{source_type}')
        
        if subject_area:
            filters.append(f'x_concepts.display_name.search:"{subject_area}"')
        
        if filters:
            params["filter"] = ",".join(filters)
        
        response = await client.get("/sources", params=params)
        response.raise_for_status()
        data = response.json()
        
        results = data.get("results", [])
        if not results:
            return f"No sources found matching your criteria"
        
        # Safely get the count
        meta = data.get("meta", {})
        count = meta.get("count", len(results)) if meta else len(results)
        
        # Create a safe query display
        query_display = f"'{query}'" if query else "your criteria"
        result = f"Found {count} sources matching {query_display}:\n\n"
        
        for i, source in enumerate(results, 1):
            # Extract metrics
            works_count = source.get("works_count", 0)
            cited_by_count = source.get("cited_by_count", 0)
            
            # Extract impact metrics
            summary_stats = source.get("summary_stats", {})
            h_index = summary_stats.get("h_index")
            i10_index = summary_stats.get("i10_index")
            
            # Extract publisher
            publisher = source.get("publisher", {}).get("display_name", "Unknown")
            
            result += f"{i}. {source.get('display_name', 'Unknown')}\n"
            result += f"   Type: {source.get('type', 'Unknown')}\n"
            result += f"   Publisher: {publisher}\n"
            if source.get("country_code"):
                result += f"   Country: {source.get('country_code')}\n"
            result += f"   Open Access: {source.get('is_oa', False)}\n"
            result += f"   In DOAJ: {source.get('is_in_doaj', False)}\n"
            result += f"   Works: {works_count:,}, Citations: {cited_by_count:,}\n"
            if h_index:
                result += f"   H-index: {h_index}\n"
            if source.get("homepage_url"):
                result += f"   Homepage: {source.get('homepage_url')}\n"
            result += f"   OpenAlex ID: {source.get('id', '')}\n"
            result += "\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error in search_sources: {e}")
        return f"Error: {str(e)}"

# FastMCP automatically handles tool registration and calling

def main():
    """Entry point for the alex-mcp command."""
    import sys
    logger.info("OpenAlex Author Disambiguation MCP Server starting...")
    # When installed as a package, the src directory is not in the path
    asyncio.run(mcp.run())

if __name__ == "__main__":
    main()
