#!/usr/bin/env python3
"""
OpenAlex Author Disambiguation MCP Server

A specialized MCP server focused exclusively on OpenAlex.org API for robust author disambiguation.
OpenAlex has excellent built-in author disambiguation using machine learning models that consider:
- Author names and alternatives
- Publication records and citation patterns
- ORCID integration when available
- Institutional affiliations
- Research topics and concepts

This server provides comprehensive author disambiguation with confidence scoring and
the ability to return N top candidates for agentic AI decision-making.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import re

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolResult,
    ListToolsResult,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OpenAlexAuthorProfile:
    """Enhanced author profile specifically designed for OpenAlex data"""
    # Core identification
    openalex_id: str
    display_name: str
    orcid: Optional[str] = None
    
    # Alternative names and identifiers
    display_name_alternatives: List[str] = None
    scopus_id: Optional[str] = None
    
    # Current and historical affiliations
    last_known_institutions: List[Dict[str, Any]] = None
    all_affiliations: List[Dict[str, Any]] = None
    
    # Research metrics
    works_count: int = 0
    cited_by_count: int = 0
    h_index: Optional[int] = None
    i10_index: Optional[int] = None
    two_year_mean_citedness: Optional[float] = None
    
    # Research areas and topics
    top_concepts: List[Dict[str, Any]] = None
    research_topics: List[str] = None
    
    # Career timeline
    first_publication_year: Optional[int] = None
    last_publication_year: Optional[int] = None
    career_length: Optional[int] = None
    
    # Publication patterns (for seniority analysis)
    authorship_positions: Dict[str, int] = None
    seniority_score: float = 0.0
    career_stage: str = "Unknown"
    
    # Disambiguation confidence
    confidence_score: float = 0.0
    match_reasons: List[str] = None
    
    # Additional metadata
    profile_url: str = ""
    works_api_url: str = ""
    created_date: Optional[str] = None
    updated_date: Optional[str] = None
    
    # Recent works sample
    recent_works: List[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize default values and calculate derived metrics"""
        if self.display_name_alternatives is None:
            self.display_name_alternatives = []
        if self.last_known_institutions is None:
            self.last_known_institutions = []
        if self.all_affiliations is None:
            self.all_affiliations = []
        if self.top_concepts is None:
            self.top_concepts = []
        if self.research_topics is None:
            self.research_topics = []
        if self.authorship_positions is None:
            self.authorship_positions = {"first": 0, "middle": 0, "last": 0}
        if self.match_reasons is None:
            self.match_reasons = []
        if self.recent_works is None:
            self.recent_works = []
        
        # Calculate career metrics
        if self.first_publication_year and self.last_publication_year:
            self.career_length = self.last_publication_year - self.first_publication_year + 1
        
        # Calculate seniority score and career stage
        self._calculate_seniority_metrics()
        
        # Set profile URL
        if self.openalex_id:
            clean_id = self.openalex_id.replace("https://openalex.org/", "")
            self.profile_url = f"https://openalex.org/{clean_id}"
            self.works_api_url = f"https://api.openalex.org/works?filter=author.id:{clean_id}"

    def _calculate_seniority_metrics(self):
        """Calculate seniority score and determine career stage"""
        total_papers = sum(self.authorship_positions.values())
        
        if total_papers == 0:
            self.seniority_score = 0.0
            self.career_stage = "No Publications"
            return
        
        # Seniority scoring: first=0.2, middle=0.5, last=1.0
        first_weight = 0.2
        middle_weight = 0.5
        last_weight = 1.0
        
        weighted_score = (
            self.authorship_positions["first"] * first_weight +
            self.authorship_positions["middle"] * middle_weight +
            self.authorship_positions["last"] * last_weight
        )
        
        self.seniority_score = weighted_score / total_papers
        
        # Determine career stage based on multiple factors
        first_ratio = self.authorship_positions["first"] / total_papers
        last_ratio = self.authorship_positions["last"] / total_papers
        
        # Career stage classification
        if total_papers < 5:
            self.career_stage = "Very Early Career"
        elif first_ratio > 0.6:
            self.career_stage = "Early Career (First Author Focus)"
        elif last_ratio > 0.4:
            if self.h_index and self.h_index > 15:
                self.career_stage = "Senior Researcher"
            else:
                self.career_stage = "Mid-Career (Leadership Role)"
        elif self.seniority_score > 0.6:
            self.career_stage = "Established Researcher"
        elif total_papers > 20:
            self.career_stage = "Experienced Researcher"
        else:
            self.career_stage = "Mid-Career"

class OpenAlexAuthorDisambiguationServer:
    """MCP Server specialized for OpenAlex author disambiguation"""
    
    def __init__(self):
        self.server = Server("openalex-author-disambiguation")
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.base_url = "https://api.openalex.org"
        
        # Email for polite API usage (recommended by OpenAlex)
        self.headers = {
            "User-Agent": "OpenAlex-Author-Disambiguation-MCP/1.0 (mailto:research@example.com)",
            "Accept": "application/json"
        }

    async def search_authors(
        self, 
        name: str, 
        affiliation: Optional[str] = None,
        additional_affiliations: Optional[List[str]] = None,
        research_field: Optional[str] = None,
        orcid: Optional[str] = None,
        limit: int = 10,
        include_works_sample: bool = True
    ) -> List[OpenAlexAuthorProfile]:
        """
        Search for authors using OpenAlex API with comprehensive disambiguation
        
        Args:
            name: Author name (required)
            affiliation: Institution name or affiliation
            research_field: Research field, topic, or concept
            orcid: ORCID identifier if known
            limit: Maximum number of results to return
            include_works_sample: Whether to fetch recent works for each author
        """
        try:
            # Build search query
            search_params = {
                "per-page": min(limit, 25),  # OpenAlex max is 25
                "select": ",".join([
                    "id", "display_name", "display_name_alternatives", "orcid",
                    "ids", "last_known_institutions", "affiliations",
                    "works_count", "cited_by_count", "summary_stats",
                    "x_concepts", "counts_by_year", "works_api_url",
                    "created_date", "updated_date"
                ])
            }
            
            # Primary search by name
            if orcid:
                # If ORCID is provided, use it for precise matching
                search_params["filter"] = f"orcid:{orcid}"
            else:
                search_params["search"] = name
            
            # Add affiliation filter if provided
            if affiliation:
                affiliation_filter = f'last_known_institutions.display_name.search:"{affiliation}"'
                if "filter" in search_params:
                    search_params["filter"] += f",{affiliation_filter}"
                else:
                    search_params["filter"] = affiliation_filter
            
            # Make API request
            url = f"{self.base_url}/authors"
            response = await self.http_client.get(url, params=search_params, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            profiles = []
            for author_data in data.get("results", []):
                profile = await self._create_author_profile(
                    author_data, 
                    query_name=name,
                    query_affiliation=affiliation,
                    query_field=research_field,
                    include_works_sample=include_works_sample
                )
                profiles.append(profile)
            
            # Sort by confidence score
            profiles.sort(key=lambda x: x.confidence_score, reverse=True)
            
            return profiles
            
        except Exception as e:
            logger.error(f"Error searching OpenAlex authors: {e}")
            return []

    async def _create_author_profile(
        self, 
        author_data: Dict[str, Any], 
        query_name: str,
        query_affiliation: Optional[str] = None,
        query_field: Optional[str] = None,
        include_works_sample: bool = True
    ) -> OpenAlexAuthorProfile:
        """Create a comprehensive author profile from OpenAlex data"""
        
        # Extract basic information
        openalex_id = author_data.get("id", "")
        display_name = author_data.get("display_name", "")
        orcid = author_data.get("orcid")
        
        # Extract identifiers
        ids = author_data.get("ids", {})
        scopus_id = ids.get("scopus")
        if scopus_id:
            # Extract numeric ID from Scopus URL
            scopus_match = re.search(r'authorID=(\d+)', scopus_id)
            scopus_id = scopus_match.group(1) if scopus_match else scopus_id
        
        # Extract affiliations
        last_known_institutions = author_data.get("last_known_institutions", [])
        all_affiliations = author_data.get("affiliations", [])
        
        # Extract metrics
        works_count = author_data.get("works_count", 0)
        cited_by_count = author_data.get("cited_by_count", 0)
        
        summary_stats = author_data.get("summary_stats", {})
        h_index = summary_stats.get("h_index")
        i10_index = summary_stats.get("i10_index")
        two_year_mean_citedness = summary_stats.get("2yr_mean_citedness")
        
        # Extract concepts/topics
        x_concepts = author_data.get("x_concepts", [])
        top_concepts = x_concepts[:5]  # Top 5 concepts
        research_topics = [concept.get("display_name", "") for concept in top_concepts]
        
        # Calculate career timeline
        counts_by_year = author_data.get("counts_by_year", [])
        years_with_works = [year_data["year"] for year_data in counts_by_year if year_data.get("works_count", 0) > 0]
        first_pub_year = min(years_with_works) if years_with_works else None
        last_pub_year = max(years_with_works) if years_with_works else None
        
        # Get authorship positions and recent works
        authorship_positions = {"first": 0, "middle": 0, "last": 0}
        recent_works = []
        
        if include_works_sample and works_count > 0:
            works_data = await self._fetch_author_works(openalex_id, limit=20)
            authorship_positions, recent_works = self._analyze_works(works_data, openalex_id)
        
        # Calculate confidence score
        confidence_score, match_reasons = self._calculate_confidence_score(
            author_data, query_name, query_affiliation, query_field
        )
        
        # Create profile
        profile = OpenAlexAuthorProfile(
            openalex_id=openalex_id,
            display_name=display_name,
            orcid=orcid,
            display_name_alternatives=author_data.get("display_name_alternatives", []),
            scopus_id=scopus_id,
            last_known_institutions=last_known_institutions,
            all_affiliations=all_affiliations,
            works_count=works_count,
            cited_by_count=cited_by_count,
            h_index=h_index,
            i10_index=i10_index,
            two_year_mean_citedness=two_year_mean_citedness,
            top_concepts=top_concepts,
            research_topics=research_topics,
            first_publication_year=first_pub_year,
            last_publication_year=last_pub_year,
            authorship_positions=authorship_positions,
            confidence_score=confidence_score,
            match_reasons=match_reasons,
            works_api_url=author_data.get("works_api_url", ""),
            created_date=author_data.get("created_date"),
            updated_date=author_data.get("updated_date"),
            recent_works=recent_works
        )
        
        return profile

    async def _fetch_author_works(self, author_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch recent works for an author to analyze authorship positions"""
        try:
            clean_id = author_id.replace("https://openalex.org/", "")
            url = f"{self.base_url}/works"
            params = {
                "filter": f"author.id:{clean_id}",
                "per-page": limit,
                "sort": "publication_date:desc",
                "select": "id,title,publication_year,authorships,cited_by_count,type"
            }
            
            response = await self.http_client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            return data.get("results", [])
            
        except Exception as e:
            logger.warning(f"Error fetching works for author {author_id}: {e}")
            return []

    def _analyze_works(self, works_data: List[Dict[str, Any]], author_id: str) -> tuple:
        """Analyze works to determine authorship positions and extract recent works info"""
        authorship_positions = {"first": 0, "middle": 0, "last": 0}
        recent_works = []
        
        clean_author_id = author_id.replace("https://openalex.org/", "")
        
        for work in works_data:
            authorships = work.get("authorships", [])
            
            # Find author's position
            author_position = None
            for i, authorship in enumerate(authorships):
                if authorship.get("author", {}).get("id", "").replace("https://openalex.org/", "") == clean_author_id:
                    author_position = i
                    break
            
            if author_position is not None:
                total_authors = len(authorships)
                if author_position == 0:
                    authorship_positions["first"] += 1
                elif author_position == total_authors - 1:
                    authorship_positions["last"] += 1
                else:
                    authorship_positions["middle"] += 1
            
            # Collect recent works info
            if len(recent_works) < 5:
                recent_works.append({
                    "title": work.get("title", ""),
                    "year": work.get("publication_year"),
                    "type": work.get("type", ""),
                    "cited_by_count": work.get("cited_by_count", 0),
                    "author_position": author_position + 1 if author_position is not None else None,
                    "total_authors": len(authorships)
                })
        
        return authorship_positions, recent_works

    def _calculate_confidence_score(
        self, 
        author_data: Dict[str, Any], 
        query_name: str,
        query_affiliation: Optional[str] = None,
        query_field: Optional[str] = None
    ) -> tuple:
        """Calculate confidence score and reasons for the match"""
        confidence = 0.6  # Base confidence for OpenAlex (higher due to good disambiguation)
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
        
        # ORCID presence (indicates higher reliability)
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
                    reasons.append(f"Affiliation match: {inst.get('display_name')}")
                    break
        
        # Research field matching
        if query_field:
            concepts = author_data.get("x_concepts", [])
            for concept in concepts[:10]:  # Check top 10 concepts
                concept_name = concept.get("display_name", "").lower()
                if query_field.lower() in concept_name or concept_name in query_field.lower():
                    confidence += 0.15
                    reasons.append(f"Research field match: {concept.get('display_name')}")
                    break
        
        # Publication activity (more active = more reliable)
        works_count = author_data.get("works_count", 0)
        if works_count > 10:
            confidence += 0.05
            reasons.append("Active researcher")
        
        return min(confidence, 1.0), reasons

    async def disambiguate_author(
        self, 
        name: str,
        affiliation: Optional[str] = None,
        research_field: Optional[str] = None,
        orcid: Optional[str] = None,
        max_candidates: int = 5,
        include_detailed_analysis: bool = True
    ) -> Dict[str, Any]:
        """
        Main disambiguation function with comprehensive analysis
        
        Args:
            name: Author name (required)
            affiliation: Institution or affiliation
            research_field: Research field or topic
            orcid: ORCID if known
            max_candidates: Maximum number of candidates to return
            include_detailed_analysis: Include detailed career analysis
        """
        
        # Search for candidates
        candidates = await self.search_authors(
            name=name,
            affiliation=affiliation,
            research_field=research_field,
            orcid=orcid,
            limit=max_candidates * 2,  # Get more to filter better
            include_works_sample=include_detailed_analysis
        )
        
        # Limit to requested number
        top_candidates = candidates[:max_candidates]
        
        # Prepare comprehensive response
        result = {
            "query": {
                "name": name,
                "affiliation": affiliation,
                "research_field": research_field,
                "orcid": orcid,
                "max_candidates": max_candidates
            },
            "disambiguation_summary": {
                "total_candidates_found": len(candidates),
                "candidates_returned": len(top_candidates),
                "best_match_confidence": top_candidates[0].confidence_score if top_candidates else 0.0,
                "disambiguation_timestamp": datetime.now().isoformat(),
                "data_source": "OpenAlex.org"
            },
            "best_match": asdict(top_candidates[0]) if top_candidates else None,
            "all_candidates": [asdict(candidate) for candidate in top_candidates],
            "disambiguation_notes": [
                "OpenAlex uses advanced ML-based author disambiguation",
                "Confidence scores include name matching, affiliation, ORCID, and research field alignment",
                "Career stage analysis based on authorship patterns and publication metrics",
                "All data sourced from OpenAlex.org comprehensive academic database"
            ]
        }
        
        return result

    async def get_author_by_id(self, openalex_id: str, include_works_sample: bool = True) -> Optional[OpenAlexAuthorProfile]:
        """Get detailed author information by OpenAlex ID"""
        try:
            # Clean the ID
            clean_id = openalex_id.replace("https://openalex.org/", "")
            if not clean_id.startswith("A"):
                clean_id = f"A{clean_id}"
            
            url = f"{self.base_url}/authors/{clean_id}"
            response = await self.http_client.get(url, headers=self.headers)
            response.raise_for_status()
            author_data = response.json()
            
            profile = await self._create_author_profile(
                author_data,
                query_name=author_data.get("display_name", ""),
                include_works_sample=include_works_sample
            )
            
            return profile
            
        except Exception as e:
            logger.error(f"Error fetching author by ID {openalex_id}: {e}")
            return None

    async def resolve_institution(self, institution_query: str) -> Optional[Dict[str, Any]]:
        """
        Resolve institution name/abbreviation to full OpenAlex institution data
        
        Args:
            institution_query: Institution name, abbreviation, or partial name
            
        Returns:
            Best matching institution data or None if not found
        """
        try:
            url = f"{self.base_url}/institutions"
            params = {
                "search": institution_query,
                "per-page": 5,
                "select": "id,display_name,display_name_alternatives,country_code,type,homepage_url"
            }
            
            response = await self.http_client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            institutions = data.get("results", [])
            if not institutions:
                return None
            
            # Score institutions by match quality
            scored_institutions = []
            query_lower = institution_query.lower()
            
            for inst in institutions:
                display_name = inst.get("display_name", "").lower()
                alternatives = [alt.lower() for alt in inst.get("display_name_alternatives", [])]
                
                score = 0
                match_type = ""
                
                # Exact match gets highest score
                if query_lower == display_name:
                    score = 100
                    match_type = "exact_match"
                elif query_lower in alternatives:
                    score = 95
                    match_type = "alternative_name_exact"
                elif query_lower in display_name:
                    score = 80
                    match_type = "partial_match"
                elif any(query_lower in alt for alt in alternatives):
                    score = 75
                    match_type = "alternative_partial"
                elif display_name.startswith(query_lower):
                    score = 70
                    match_type = "prefix_match"
                else:
                    # Check if query words are in institution name
                    query_words = query_lower.split()
                    name_words = display_name.split()
                    matching_words = sum(1 for word in query_words if any(word in name_word for name_word in name_words))
                    if matching_words > 0:
                        score = 50 + (matching_words / len(query_words)) * 20
                        match_type = "word_match"
                
                if score > 0:
                    scored_institutions.append({
                        "institution": inst,
                        "score": score,
                        "match_type": match_type
                    })
            
            if scored_institutions:
                # Return the best match
                best_match = max(scored_institutions, key=lambda x: x["score"])
                return {
                    **best_match["institution"],
                    "match_score": best_match["score"],
                    "match_type": best_match["match_type"]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error resolving institution '{institution_query}': {e}")
            return None

    async def resolve_multiple_institutions(self, institution_queries: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Resolve multiple institution queries in parallel
        
        Args:
            institution_queries: List of institution names/abbreviations
            
        Returns:
            Dictionary mapping query to resolved institution data
        """
        results = {}
        
        for query in institution_queries:
            # Add small delay to avoid rate limiting
            if len(results) > 0:
                await asyncio.sleep(0.2)
            
            resolved = await self.resolve_institution(query)
            results[query] = resolved
        
        return results

    async def autocomplete_authors(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fast autocomplete search for authors"""
        try:
            url = f"{self.base_url}/autocomplete/authors"
            params = {
                "q": query,
                "limit": limit
            }
            
            response = await self.http_client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            return data.get("results", [])
            
        except Exception as e:
            logger.error(f"Error in autocomplete: {e}")
            return []

    # ========================================
    # PHASE 1 EXPANSION: Core Research Tools
    # ========================================

    async def search_works_by_author(
        self,
        author_id: Optional[str] = None,
        author_name: Optional[str] = None,
        publication_year_range: Optional[str] = None,
        source_type: Optional[str] = None,
        topic_filter: Optional[str] = None,
        sort_by: str = "publication_date",
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Find all publications by a specific author with advanced filtering
        
        Args:
            author_id: OpenAlex author ID (preferred)
            author_name: Author name (if ID not available)
            publication_year_range: e.g., "2020-2024" or "2020"
            source_type: "journal", "conference", "book", "repository", etc.
            topic_filter: Filter by research topics/concepts
            sort_by: "publication_date", "cited_by_count", "relevance"
            limit: Maximum number of works to return
        """
        try:
            if not author_id and not author_name:
                raise ValueError("Either author_id or author_name must be provided")
            
            # If only name provided, try to find the author first
            if not author_id and author_name:
                authors = await self.search_authors(author_name, limit=1)
                if not authors:
                    return {"error": f"No author found with name: {author_name}", "works": []}
                author_id = authors[0].openalex_id
            
            # Clean author ID
            clean_author_id = author_id.replace("https://openalex.org/", "")
            
            # Build filter parameters
            filters = [f"author.id:{clean_author_id}"]
            
            # Add year range filter
            if publication_year_range:
                if "-" in publication_year_range:
                    start_year, end_year = publication_year_range.split("-")
                    filters.append(f"publication_year:{start_year}-{end_year}")
                else:
                    filters.append(f"publication_year:{publication_year_range}")
            
            # Add source type filter
            if source_type:
                filters.append(f"type:{source_type}")
            
            # Add topic filter
            if topic_filter:
                filters.append(f"concepts.display_name.search:{topic_filter}")
            
            # Set sort parameter
            sort_options = {
                "publication_date": "publication_date:desc",
                "cited_by_count": "cited_by_count:desc",
                "relevance": "relevance_score:desc"
            }
            sort_param = sort_options.get(sort_by, "publication_date:desc")
            
            # Make API request with simplified select to avoid 403 errors
            url = f"{self.base_url}/works"
            params = {
                "filter": ",".join(filters),
                "sort": sort_param,
                "per-page": min(limit, 200),  # OpenAlex max is 200
                "select": "id,title,publication_year,publication_date,type,cited_by_count,is_oa,authorships,concepts,primary_location,doi"
            }
            
            response = await self.http_client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            works = data.get("results", [])
            
            # Process works for better presentation
            processed_works = []
            for work in works:
                # Find author's position in this work
                author_position = None
                total_authors = 0
                authorships = work.get("authorships", [])
                total_authors = len(authorships)
                
                for i, authorship in enumerate(authorships):
                    if authorship.get("author", {}).get("id", "").replace("https://openalex.org/", "") == clean_author_id:
                        author_position = i + 1
                        break
                
                # Extract key concepts
                concepts = work.get("concepts", [])
                top_concepts = [c.get("display_name") for c in concepts[:3]]
                
                # Extract venue information
                primary_location = work.get("primary_location", {})
                venue_name = primary_location.get("source", {}).get("display_name", "Unknown")
                
                processed_work = {
                    "id": work.get("id"),
                    "title": work.get("title", ""),
                    "publication_year": work.get("publication_year"),
                    "publication_date": work.get("publication_date"),
                    "type": work.get("type", ""),
                    "venue": venue_name,
                    "cited_by_count": work.get("cited_by_count", 0),
                    "is_open_access": work.get("is_oa", False),
                    "doi": work.get("doi"),
                    "author_position": author_position,
                    "total_authors": total_authors,
                    "top_concepts": top_concepts,
                    "url": work.get("id", "")
                }
                processed_works.append(processed_work)
            
            # Calculate summary statistics
            total_citations = sum(work["cited_by_count"] for work in processed_works)
            open_access_count = sum(1 for work in processed_works if work["is_open_access"])
            
            # Analyze authorship positions
            first_author_count = sum(1 for work in processed_works if work["author_position"] == 1)
            last_author_count = sum(1 for work in processed_works if work["author_position"] == work["total_authors"])
            
            result = {
                "query": {
                    "author_id": author_id,
                    "author_name": author_name,
                    "publication_year_range": publication_year_range,
                    "source_type": source_type,
                    "topic_filter": topic_filter,
                    "sort_by": sort_by,
                    "limit": limit
                },
                "summary": {
                    "total_works_found": len(processed_works),
                    "total_citations": total_citations,
                    "open_access_percentage": (open_access_count / len(processed_works) * 100) if processed_works else 0,
                    "first_author_papers": first_author_count,
                    "last_author_papers": last_author_count,
                    "average_citations_per_paper": total_citations / len(processed_works) if processed_works else 0
                },
                "works": processed_works,
                "data_source": "OpenAlex.org"
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error searching works by author: {e}")
            return {"error": str(e), "works": []}

    async def get_work_details(
        self,
        work_id: str,
        include_citations: bool = False,
        include_references: bool = False
    ) -> Dict[str, Any]:
        """
        Get comprehensive details about a specific publication
        
        Args:
            work_id: OpenAlex work ID
            include_citations: Include works that cite this work
            include_references: Include works referenced by this work
        """
        try:
            # Clean work ID
            clean_work_id = work_id.replace("https://openalex.org/", "")
            if not clean_work_id.startswith("W"):
                clean_work_id = f"W{clean_work_id}"
            
            # Get main work details
            url = f"{self.base_url}/works/{clean_work_id}"
            response = await self.http_client.get(url, headers=self.headers)
            response.raise_for_status()
            work_data = response.json()
            
            # Process authorship information
            authorships = work_data.get("authorships", [])
            processed_authors = []
            for i, authorship in enumerate(authorships):
                author = authorship.get("author", {})
                institutions = authorship.get("institutions", [])
                
                processed_author = {
                    "position": i + 1,
                    "name": author.get("display_name", ""),
                    "id": author.get("id", ""),
                    "orcid": author.get("orcid"),
                    "institutions": [inst.get("display_name", "") for inst in institutions]
                }
                processed_authors.append(processed_author)
            
            # Process concepts/topics
            concepts = work_data.get("concepts", [])
            processed_concepts = []
            for concept in concepts:
                processed_concepts.append({
                    "name": concept.get("display_name", ""),
                    "level": concept.get("level", 0),
                    "score": concept.get("score", 0.0)
                })
            
            # Extract venue information
            primary_location = work_data.get("primary_location", {})
            venue_info = {
                "name": primary_location.get("source", {}).get("display_name", ""),
                "type": primary_location.get("source", {}).get("type", ""),
                "issn": primary_location.get("source", {}).get("issn", []),
                "is_oa": primary_location.get("is_oa", False),
                "version": primary_location.get("version", "")
            }
            
            # Build main result
            result = {
                "work_details": {
                    "id": work_data.get("id"),
                    "title": work_data.get("title", ""),
                    "display_name": work_data.get("display_name", ""),
                    "publication_year": work_data.get("publication_year"),
                    "publication_date": work_data.get("publication_date"),
                    "type": work_data.get("type", ""),
                    "doi": work_data.get("doi"),
                    "url": work_data.get("id", ""),
                    "is_open_access": work_data.get("is_oa", False),
                    "cited_by_count": work_data.get("cited_by_count", 0),
                    "biblio": work_data.get("biblio", {}),
                    "language": work_data.get("language"),
                    "abstract": work_data.get("abstract_inverted_index")
                },
                "venue": venue_info,
                "authors": processed_authors,
                "concepts": processed_concepts,
                "open_access": work_data.get("open_access", {}),
                "data_source": "OpenAlex.org"
            }
            
            # Add citations if requested
            if include_citations:
                await asyncio.sleep(0.5)  # Rate limiting
                citations_url = f"{self.base_url}/works"
                citations_params = {
                    "filter": f"cites:{clean_work_id}",
                    "per-page": 50,
                    "select": "id,title,publication_year,cited_by_count,authorships"
                }
                
                try:
                    citations_response = await self.http_client.get(
                        citations_url, params=citations_params, headers=self.headers
                    )
                    citations_response.raise_for_status()
                    citations_data = citations_response.json()
                    
                    citing_works = []
                    for citing_work in citations_data.get("results", []):
                        citing_works.append({
                            "id": citing_work.get("id"),
                            "title": citing_work.get("title", ""),
                            "publication_year": citing_work.get("publication_year"),
                            "cited_by_count": citing_work.get("cited_by_count", 0),
                            "first_author": citing_work.get("authorships", [{}])[0].get("author", {}).get("display_name", "") if citing_work.get("authorships") else ""
                        })
                    
                    result["citations"] = {
                        "total_citing_works": len(citing_works),
                        "citing_works_sample": citing_works[:20]  # Limit sample
                    }
                except Exception as e:
                    logger.warning(f"Error fetching citations: {e}")
                    result["citations"] = {"error": "Could not fetch citations"}
            
            # Add references if requested
            if include_references:
                await asyncio.sleep(0.5)  # Rate limiting
                references_url = f"{self.base_url}/works"
                references_params = {
                    "filter": f"cited_by:{clean_work_id}",
                    "per-page": 50,
                    "select": "id,title,publication_year,cited_by_count,authorships"
                }
                
                try:
                    references_response = await self.http_client.get(
                        references_url, params=references_params, headers=self.headers
                    )
                    references_response.raise_for_status()
                    references_data = references_response.json()
                    
                    referenced_works = []
                    for ref_work in references_data.get("results", []):
                        referenced_works.append({
                            "id": ref_work.get("id"),
                            "title": ref_work.get("title", ""),
                            "publication_year": ref_work.get("publication_year"),
                            "cited_by_count": ref_work.get("cited_by_count", 0),
                            "first_author": ref_work.get("authorships", [{}])[0].get("author", {}).get("display_name", "") if ref_work.get("authorships") else ""
                        })
                    
                    result["references"] = {
                        "total_referenced_works": len(referenced_works),
                        "referenced_works_sample": referenced_works[:20]  # Limit sample
                    }
                except Exception as e:
                    logger.warning(f"Error fetching references: {e}")
                    result["references"] = {"error": "Could not fetch references"}
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting work details for {work_id}: {e}")
            return {"error": str(e)}

    async def search_topics(
        self,
        topic_query: str,
        level: Optional[int] = None,
        related_topics: bool = False,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Search and explore research topics/concepts
        
        Args:
            topic_query: Topic name or description to search for
            level: Topic hierarchy level (0-5, where 0 is most general)
            related_topics: Include related topics in results
            limit: Maximum number of topics to return
        """
        try:
            # Build search parameters with simplified select to avoid 403 errors
            url = f"{self.base_url}/topics"
            params = {
                "search": topic_query,
                "per-page": min(limit, 200),
                "select": "id,display_name,description,keywords,level,works_count,cited_by_count,subfield,field,domain"
            }
            
            # Add level filter if specified
            if level is not None:
                params["filter"] = f"level:{level}"
            
            response = await self.http_client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            topics = data.get("results", [])
            processed_topics = []
            
            for topic in topics:
                # Calculate relevance score based on search query
                display_name = topic.get("display_name", "").lower()
                query_lower = topic_query.lower()
                
                relevance_score = 0.0
                if query_lower == display_name:
                    relevance_score = 1.0
                elif query_lower in display_name:
                    relevance_score = 0.8
                elif any(word in display_name for word in query_lower.split()):
                    relevance_score = 0.6
                else:
                    relevance_score = 0.4
                
                processed_topic = {
                    "id": topic.get("id"),
                    "name": topic.get("display_name", ""),
                    "description": topic.get("description", ""),
                    "level": topic.get("level", 0),
                    "keywords": topic.get("keywords", []),
                    "works_count": topic.get("works_count", 0),
                    "cited_by_count": topic.get("cited_by_count", 0),
                    "hierarchy": {
                        "domain": topic.get("domain", {}).get("display_name", "") if topic.get("domain") else "",
                        "field": topic.get("field", {}).get("display_name", "") if topic.get("field") else "",
                        "subfield": topic.get("subfield", {}).get("display_name", "") if topic.get("subfield") else ""
                    },
                    "relevance_score": relevance_score,
                    "url": topic.get("id", "")
                }
                processed_topics.append(processed_topic)
            
            # Sort by relevance score and works count
            processed_topics.sort(key=lambda x: (x["relevance_score"], x["works_count"]), reverse=True)
            
            result = {
                "query": {
                    "topic_query": topic_query,
                    "level": level,
                    "related_topics": related_topics,
                    "limit": limit
                },
                "summary": {
                    "total_topics_found": len(processed_topics),
                    "search_timestamp": datetime.now().isoformat()
                },
                "topics": processed_topics,
                "data_source": "OpenAlex.org"
            }
            
            # Add related topics if requested
            if related_topics and processed_topics:
                # Get related topics for the top result
                top_topic_id = processed_topics[0]["id"].replace("https://openalex.org/", "")
                await asyncio.sleep(0.5)  # Rate limiting
                
                try:
                    related_url = f"{self.base_url}/topics"
                    related_params = {
                        "filter": f"subfield.id:{top_topic_id}",
                        "per-page": 10,
                        "select": "id,display_name,level,works_count"
                    }
                    
                    related_response = await self.http_client.get(
                        related_url, params=related_params, headers=self.headers
                    )
                    related_response.raise_for_status()
                    related_data = related_response.json()
                    
                    related_topics_list = []
                    for related_topic in related_data.get("results", []):
                        related_topics_list.append({
                            "id": related_topic.get("id"),
                            "name": related_topic.get("display_name", ""),
                            "level": related_topic.get("level", 0),
                            "works_count": related_topic.get("works_count", 0)
                        })
                    
                    result["related_topics"] = related_topics_list
                    
                except Exception as e:
                    logger.warning(f"Error fetching related topics: {e}")
                    result["related_topics"] = []
            
            return result
            
        except Exception as e:
            logger.error(f"Error searching topics: {e}")
            return {"error": str(e), "topics": []}

    def setup_tools(self):
        """Setup MCP tools for OpenAlex author disambiguation"""
        
        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            return ListToolsResult(
                tools=[
                    Tool(
                        name="disambiguate_author_openalex",
                        description="Disambiguate an author using OpenAlex.org's advanced ML-based disambiguation system. Returns ranked candidates with confidence scores and detailed analysis.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Author name (required) - can be full name or surname"
                                },
                                "affiliation": {
                                    "type": "string",
                                    "description": "Institution name or affiliation to improve disambiguation accuracy"
                                },
                                "research_field": {
                                    "type": "string",
                                    "description": "Research field, topic, or area of study"
                                },
                                "orcid": {
                                    "type": "string",
                                    "description": "ORCID identifier if known (provides highest confidence matching)"
                                },
                                "max_candidates": {
                                    "type": "integer",
                                    "description": "Maximum number of author candidates to return (default: 5, max: 25)",
                                    "default": 5,
                                    "minimum": 1,
                                    "maximum": 25
                                },
                                "include_detailed_analysis": {
                                    "type": "boolean",
                                    "description": "Include detailed career analysis and recent works (default: true)",
                                    "default": True
                                }
                            },
                            "required": ["name"]
                        }
                    ),
                    Tool(
                        name="get_author_by_openalex_id",
                        description="Get detailed author information by OpenAlex ID",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "openalex_id": {
                                    "type": "string",
                                    "description": "OpenAlex author ID (e.g., 'A5023888391' or 'https://openalex.org/A5023888391')"
                                },
                                "include_works_sample": {
                                    "type": "boolean",
                                    "description": "Include sample of recent works for analysis (default: true)",
                                    "default": True
                                }
                            },
                            "required": ["openalex_id"]
                        }
                    ),
                    Tool(
                        name="autocomplete_authors_openalex",
                        description="Fast autocomplete search for authors - useful for type-ahead functionality",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Partial author name for autocomplete"
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "Maximum number of suggestions (default: 10)",
                                    "default": 10,
                                    "minimum": 1,
                                    "maximum": 25
                                }
                            },
                            "required": ["query"]
                        }
                    ),
                    Tool(
                        name="search_authors_openalex",
                        description="Advanced author search with multiple filters and detailed results",
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
                                "orcid": {
                                    "type": "string",
                                    "description": "Search by ORCID identifier"
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "Maximum number of results (default: 10, max: 25)",
                                    "default": 10,
                                    "minimum": 1,
                                    "maximum": 25
                                },
                                "include_works_sample": {
                                    "type": "boolean",
                                    "description": "Include recent works analysis (default: true)",
                                    "default": True
                                }
                            },
                            "required": ["name"]
                        }
                    ),
                    Tool(
                        name="resolve_institution_openalex",
                        description="Resolve institution name or abbreviation to full OpenAlex institution data. Useful for expanding abbreviations like 'EMBO' to 'European Molecular Biology Organization'.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "institution_query": {
                                    "type": "string",
                                    "description": "Institution name, abbreviation, or partial name to resolve (e.g., 'EMBO', 'MIT', 'Max Planck')"
                                }
                            },
                            "required": ["institution_query"]
                        }
                    ),
                    Tool(
                        name="resolve_multiple_institutions_openalex",
                        description="Resolve multiple institution names or abbreviations in batch. Efficient for processing multiple affiliations at once.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "institution_queries": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    },
                                    "description": "List of institution names, abbreviations, or partial names to resolve"
                                }
                            },
                            "required": ["institution_queries"]
                        }
                    ),
                    # PHASE 1 EXPANSION: Core Research Tools
                    Tool(
                        name="search_works_by_author_openalex",
                        description="Find all publications by a specific author with advanced filtering. Essential for research impact analysis, CV generation, and collaboration discovery.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "author_id": {
                                    "type": "string",
                                    "description": "OpenAlex author ID (preferred for accuracy)"
                                },
                                "author_name": {
                                    "type": "string",
                                    "description": "Author name (if ID not available)"
                                },
                                "publication_year_range": {
                                    "type": "string",
                                    "description": "Year range filter (e.g., '2020-2024' or '2020')"
                                },
                                "source_type": {
                                    "type": "string",
                                    "description": "Publication type filter: 'journal', 'conference', 'book', 'repository', etc."
                                },
                                "topic_filter": {
                                    "type": "string",
                                    "description": "Filter by research topics/concepts"
                                },
                                "sort_by": {
                                    "type": "string",
                                    "description": "Sort order: 'publication_date', 'cited_by_count', 'relevance' (default: publication_date)",
                                    "default": "publication_date"
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "Maximum number of works to return (default: 20, max: 200)",
                                    "default": 20,
                                    "minimum": 1,
                                    "maximum": 200
                                }
                            },
                            "anyOf": [
                                {"required": ["author_id"]},
                                {"required": ["author_name"]}
                            ]
                        }
                    ),
                    Tool(
                        name="get_work_details_openalex",
                        description="Get comprehensive details about a specific publication including authors, venue, concepts, and optionally citations and references.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "work_id": {
                                    "type": "string",
                                    "description": "OpenAlex work ID (e.g., 'W2741809807' or full URL)"
                                },
                                "include_citations": {
                                    "type": "boolean",
                                    "description": "Include works that cite this publication (default: false)",
                                    "default": False
                                },
                                "include_references": {
                                    "type": "boolean",
                                    "description": "Include works referenced by this publication (default: false)",
                                    "default": False
                                }
                            },
                            "required": ["work_id"]
                        }
                    ),
                    Tool(
                        name="search_topics_openalex",
                        description="Search and explore research topics/concepts with hierarchy information. Important for research area discovery and trend analysis.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "topic_query": {
                                    "type": "string",
                                    "description": "Topic name or description to search for"
                                },
                                "level": {
                                    "type": "integer",
                                    "description": "Topic hierarchy level (0-5, where 0 is most general)",
                                    "minimum": 0,
                                    "maximum": 5
                                },
                                "related_topics": {
                                    "type": "boolean",
                                    "description": "Include related topics in results (default: false)",
                                    "default": False
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "Maximum number of topics to return (default: 20, max: 200)",
                                    "default": 20,
                                    "minimum": 1,
                                    "maximum": 200
                                }
                            },
                            "required": ["topic_query"]
                        }
                    )
                ]
            )

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            try:
                if name == "disambiguate_author_openalex":
                    result = await self.disambiguate_author(
                        name=arguments["name"],
                        affiliation=arguments.get("affiliation"),
                        research_field=arguments.get("research_field"),
                        orcid=arguments.get("orcid"),
                        max_candidates=arguments.get("max_candidates", 5),
                        include_detailed_analysis=arguments.get("include_detailed_analysis", True)
                    )
                    return CallToolResult(
                        content=[TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
                    )
                
                elif name == "get_author_by_openalex_id":
                    profile = await self.get_author_by_id(
                        openalex_id=arguments["openalex_id"],
                        include_works_sample=arguments.get("include_works_sample", True)
                    )
                    if profile:
                        result = {"author_profile": asdict(profile)}
                    else:
                        result = {"error": "Author not found"}
                    
                    return CallToolResult(
                        content=[TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
                    )
                
                elif name == "autocomplete_authors_openalex":
                    suggestions = await self.autocomplete_authors(
                        query=arguments["query"],
                        limit=arguments.get("limit", 10)
                    )
                    result = {"suggestions": suggestions}
                    return CallToolResult(
                        content=[TextContent(type="text", text=json.dumps(result, indent=2))]
                    )
                
                elif name == "search_authors_openalex":
                    profiles = await self.search_authors(
                        name=arguments["name"],
                        affiliation=arguments.get("affiliation"),
                        research_field=arguments.get("research_field"),
                        orcid=arguments.get("orcid"),
                        limit=arguments.get("limit", 10),
                        include_works_sample=arguments.get("include_works_sample", True)
                    )
                    result = {
                        "search_results": [asdict(profile) for profile in profiles],
                        "total_found": len(profiles)
                    }
                    return CallToolResult(
                        content=[TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
                    )
                
                elif name == "resolve_institution_openalex":
                    institution = await self.resolve_institution(
                        institution_query=arguments["institution_query"]
                    )
                    result = {
                        "query": arguments["institution_query"],
                        "resolved_institution": institution
                    }
                    return CallToolResult(
                        content=[TextContent(type="text", text=json.dumps(result, indent=2))]
                    )
                
                elif name == "resolve_multiple_institutions_openalex":
                    institutions = await self.resolve_multiple_institutions(
                        institution_queries=arguments["institution_queries"]
                    )
                    result = {
                        "queries": arguments["institution_queries"],
                        "resolved_institutions": institutions
                    }
                    return CallToolResult(
                        content=[TextContent(type="text", text=json.dumps(result, indent=2))]
                    )
                
                # PHASE 1 EXPANSION: Core Research Tools
                elif name == "search_works_by_author_openalex":
                    result = await self.search_works_by_author(
                        author_id=arguments.get("author_id"),
                        author_name=arguments.get("author_name"),
                        publication_year_range=arguments.get("publication_year_range"),
                        source_type=arguments.get("source_type"),
                        topic_filter=arguments.get("topic_filter"),
                        sort_by=arguments.get("sort_by", "publication_date"),
                        limit=arguments.get("limit", 20)
                    )
                    return CallToolResult(
                        content=[TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
                    )
                
                elif name == "get_work_details_openalex":
                    result = await self.get_work_details(
                        work_id=arguments["work_id"],
                        include_citations=arguments.get("include_citations", False),
                        include_references=arguments.get("include_references", False)
                    )
                    return CallToolResult(
                        content=[TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
                    )
                
                elif name == "search_topics_openalex":
                    result = await self.search_topics(
                        topic_query=arguments["topic_query"],
                        level=arguments.get("level"),
                        related_topics=arguments.get("related_topics", False),
                        limit=arguments.get("limit", 20)
                    )
                    return CallToolResult(
                        content=[TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
                    )
                
                else:
                    raise ValueError(f"Unknown tool: {name}")
                    
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")],
                    isError=True
                )

    async def run(self):
        """Run the MCP server"""
        self.setup_tools()
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

async def main():
    """Main entry point"""
    server = OpenAlexAuthorDisambiguationServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
