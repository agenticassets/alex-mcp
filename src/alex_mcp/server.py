#!/usr/bin/env python3
"""
OpenAlex Author Disambiguation MCP Server

A professional MCP server for author disambiguation and institution resolution using OpenAlex.org API.
Built following MCP best practices with the standard MCP library.

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
from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
server = Server("openalex-author-disambiguation")

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
# MCP TOOL IMPLEMENTATIONS
# ============================================================================

async def disambiguate_author_impl(
    name: str,
    affiliation: str = None,
    research_field: str = None,
    orcid: str = None,
    max_candidates: int = 5
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

async def search_authors_impl(
    name: str,
    affiliation: str = None,
    research_field: str = None,
    limit: int = 10
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

async def get_author_profile_impl(openalex_id: str) -> str:
    """
    Get detailed author profile by OpenAlex ID.
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

async def resolve_institution_impl(institution_query: str) -> str:
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
# MCP SERVER HANDLERS
# ============================================================================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="disambiguate_author",
            description="Disambiguate an author using OpenAlex's ML-powered disambiguation system. Returns ranked candidates with confidence scores and detailed analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Author name (required) - can be full name or surname"
                    },
                    "affiliation": {
                        "type": "string",
                        "description": "Institution name or affiliation to improve accuracy"
                    },
                    "research_field": {
                        "type": "string",
                        "description": "Research field, topic, or area of study"
                    },
                    "orcid": {
                        "type": "string",
                        "description": "ORCID identifier if known (provides highest confidence)"
                    },
                    "max_candidates": {
                        "type": "integer",
                        "description": "Maximum number of candidates to return (1-25, default: 5)",
                        "default": 5
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="search_authors",
            description="Search for authors with advanced filtering capabilities. Useful for finding multiple authors or exploring author profiles in specific institutions or research areas.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Author name to search for"
                    },
                    "affiliation": {
                        "type": "string",
                        "description": "Filter by institution or affiliation"
                    },
                    "research_field": {
                        "type": "string",
                        "description": "Filter by research field or topic"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (1-25, default: 10)",
                        "default": 10
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="get_author_profile",
            description="Get detailed author profile by OpenAlex ID. Retrieves comprehensive information about a specific author including metrics, affiliations, and research areas.",
            inputSchema={
                "type": "object",
                "properties": {
                    "openalex_id": {
                        "type": "string",
                        "description": "OpenAlex author ID (e.g., 'A5023888391' or full URL)"
                    }
                },
                "required": ["openalex_id"]
            }
        ),
        Tool(
            name="resolve_institution",
            description="Resolve institution name or abbreviation to full OpenAlex data. Automatically expands abbreviations and resolves partial names.",
            inputSchema={
                "type": "object",
                "properties": {
                    "institution_query": {
                        "type": "string",
                        "description": "Institution name, abbreviation, or partial name"
                    }
                },
                "required": ["institution_query"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "disambiguate_author":
            result = await disambiguate_author_impl(
                name=arguments["name"],
                affiliation=arguments.get("affiliation"),
                research_field=arguments.get("research_field"),
                orcid=arguments.get("orcid"),
                max_candidates=arguments.get("max_candidates", 5)
            )
        elif name == "search_authors":
            result = await search_authors_impl(
                name=arguments["name"],
                affiliation=arguments.get("affiliation"),
                research_field=arguments.get("research_field"),
                limit=arguments.get("limit", 10)
            )
        elif name == "get_author_profile":
            result = await get_author_profile_impl(
                openalex_id=arguments["openalex_id"]
            )
        elif name == "resolve_institution":
            result = await resolve_institution_impl(
                institution_query=arguments["institution_query"]
            )
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        return [TextContent(type="text", text=result)]
    
    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

def main():
    """Entry point for the alex-mcp command."""
    import sys
    import uvicorn
    logger.info("OpenAlex Author Disambiguation MCP Server starting...")
    # When run directly, start a simple HTTP server
    uvicorn.run(
        "src.alex_mcp.server:server",
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )

if __name__ == "__main__":
    main()
