#!/usr/bin/env python3
"""
Author Disambiguation MCP Server

This server provides tools for disambiguating authors across multiple scientific databases:
- Semantic Scholar API
- OpenAlex API
- EuropePMC API

Input parameters:
- author name/surname
- current affiliation
- field of study
- other keywords

Output:
- Disambiguated author profile
- Author seniority based on paper positions
- Comparable data across services
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime

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
class AuthorProfile:
    """Standardized author profile across all services"""
    name: str
    author_id: str
    service: str  # 'semantic_scholar', 'openalex', 'europepmc'
    affiliation: Optional[str] = None
    field_of_study: Optional[str] = None
    paper_count: int = 0
    citation_count: int = 0
    h_index: Optional[int] = None
    first_author_papers: int = 0
    last_author_papers: int = 0
    middle_author_papers: int = 0
    seniority_score: float = 0.0
    confidence_score: float = 0.0
    profile_url: Optional[str] = None
    recent_papers: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.recent_papers is None:
            self.recent_papers = []
        
        # Calculate seniority score based on authorship positions
        total_papers = self.first_author_papers + self.last_author_papers + self.middle_author_papers
        if total_papers > 0:
            # Weight: first author (junior) = 0.3, last author (senior) = 1.0, middle = 0.5
            self.seniority_score = (
                (self.first_author_papers * 0.3 + 
                 self.last_author_papers * 1.0 + 
                 self.middle_author_papers * 0.5) / total_papers
            )

class AuthorDisambiguationServer:
    def __init__(self):
        self.server = Server("author-disambiguation-server")
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # API endpoints
        self.semantic_scholar_base = "https://api.semanticscholar.org/graph/v1"
        self.openalex_base = "https://api.openalex.org"
        self.europepmc_base = "https://www.ebi.ac.uk/europepmc/webservices/rest"

    async def search_semantic_scholar(self, name: str, affiliation: str = None, 
                                    field: str = None, keywords: str = None) -> List[AuthorProfile]:
        """Search for authors in Semantic Scholar"""
        try:
            # Search for authors by name
            url = f"{self.semantic_scholar_base}/author/search"
            params = {
                "query": name,
                "limit": 10,
                "fields": "authorId,name,affiliations,paperCount,citationCount,hIndex,papers.title,papers.year,papers.authors"
            }
            
            response = await self.http_client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            profiles = []
            for author_data in data.get("data", []):
                # Calculate authorship positions
                first_author = last_author = middle_author = 0
                papers = author_data.get("papers", [])
                
                for paper in papers:
                    authors = paper.get("authors", [])
                    if not authors:
                        continue
                        
                    author_positions = [i for i, a in enumerate(authors) 
                                     if a.get("authorId") == author_data.get("authorId")]
                    
                    for pos in author_positions:
                        if pos == 0:
                            first_author += 1
                        elif pos == len(authors) - 1:
                            last_author += 1
                        else:
                            middle_author += 1
                
                # Calculate confidence score based on affiliation and field matching
                confidence = 0.5  # Base confidence
                author_affiliations = author_data.get("affiliations", [])
                
                if affiliation and author_affiliations:
                    for aff in author_affiliations:
                        if affiliation.lower() in aff.lower():
                            confidence += 0.3
                            break
                
                profile = AuthorProfile(
                    name=author_data.get("name", ""),
                    author_id=author_data.get("authorId", ""),
                    service="semantic_scholar",
                    affiliation=", ".join(author_affiliations) if author_affiliations else None,
                    paper_count=author_data.get("paperCount", 0),
                    citation_count=author_data.get("citationCount", 0),
                    h_index=author_data.get("hIndex"),
                    first_author_papers=first_author,
                    last_author_papers=last_author,
                    middle_author_papers=middle_author,
                    confidence_score=min(confidence, 1.0),
                    profile_url=f"https://www.semanticscholar.org/author/{author_data.get('authorId', '')}",
                    recent_papers=[{
                        "title": p.get("title", ""),
                        "year": p.get("year")
                    } for p in papers[:5]]
                )
                profiles.append(profile)
            
            return profiles
            
        except Exception as e:
            logger.error(f"Error searching Semantic Scholar: {e}")
            return []

    async def search_openalex(self, name: str, affiliation: str = None, 
                            field: str = None, keywords: str = None) -> List[AuthorProfile]:
        """Search for authors in OpenAlex"""
        try:
            # Build search query
            query_parts = [f'display_name.search:"{name}"']
            if affiliation:
                query_parts.append(f'last_known_institutions.display_name.search:"{affiliation}"')
            
            url = f"{self.openalex_base}/authors"
            params = {
                "filter": ",".join(query_parts),
                "per-page": 10,
                "select": "id,display_name,last_known_institutions,works_count,cited_by_count,h_index,works_api_url"
            }
            
            response = await self.http_client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            profiles = []
            for author_data in data.get("results", []):
                # Get author's works to calculate positions
                works_url = author_data.get("works_api_url", "")
                first_author = last_author = middle_author = 0
                recent_papers = []
                
                if works_url:
                    try:
                        works_response = await self.http_client.get(f"{works_url}?per-page=50")
                        works_data = works_response.json()
                        
                        for work in works_data.get("results", []):
                            authorships = work.get("authorships", [])
                            author_id = author_data.get("id", "")
                            
                            for i, authorship in enumerate(authorships):
                                if authorship.get("author", {}).get("id") == author_id:
                                    if i == 0:
                                        first_author += 1
                                    elif i == len(authorships) - 1:
                                        last_author += 1
                                    else:
                                        middle_author += 1
                                    break
                            
                            # Collect recent papers
                            if len(recent_papers) < 5:
                                recent_papers.append({
                                    "title": work.get("title", ""),
                                    "year": work.get("publication_year")
                                })
                    except Exception as e:
                        logger.warning(f"Error fetching works for author {author_id}: {e}")
                
                # Calculate confidence score
                confidence = 0.5
                institutions = author_data.get("last_known_institutions", [])
                if affiliation and institutions:
                    for inst in institutions:
                        if affiliation.lower() in inst.get("display_name", "").lower():
                            confidence += 0.3
                            break
                
                profile = AuthorProfile(
                    name=author_data.get("display_name", ""),
                    author_id=author_data.get("id", "").replace("https://openalex.org/", ""),
                    service="openalex",
                    affiliation=", ".join([inst.get("display_name", "") for inst in institutions]),
                    paper_count=author_data.get("works_count", 0),
                    citation_count=author_data.get("cited_by_count", 0),
                    h_index=author_data.get("h_index"),
                    first_author_papers=first_author,
                    last_author_papers=last_author,
                    middle_author_papers=middle_author,
                    confidence_score=min(confidence, 1.0),
                    profile_url=author_data.get("id", ""),
                    recent_papers=recent_papers
                )
                profiles.append(profile)
            
            return profiles
            
        except Exception as e:
            logger.error(f"Error searching OpenAlex: {e}")
            return []

    async def search_europepmc(self, name: str, affiliation: str = None, 
                             field: str = None, keywords: str = None) -> List[AuthorProfile]:
        """Search for authors in EuropePMC"""
        try:
            # EuropePMC doesn't have a direct author search, so we search papers and extract authors
            query_parts = [f'AUTH:"{name}"']
            if affiliation:
                query_parts.append(f'AFF:"{affiliation}"')
            if keywords:
                query_parts.append(keywords)
            
            url = f"{self.europepmc_base}/search"
            params = {
                "query": " AND ".join(query_parts),
                "format": "json",
                "pageSize": 50,
                "resultType": "core"
            }
            
            response = await self.http_client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Group papers by author
            author_papers = {}
            for paper in data.get("resultList", {}).get("result", []):
                authors = paper.get("authorList", {}).get("author", [])
                for i, author in enumerate(authors):
                    author_name = f"{author.get('firstName', '')} {author.get('lastName', '')}".strip()
                    if not author_name or name.lower() not in author_name.lower():
                        continue
                    
                    if author_name not in author_papers:
                        author_papers[author_name] = {
                            "papers": [],
                            "first_author": 0,
                            "last_author": 0,
                            "middle_author": 0,
                            "affiliations": set()
                        }
                    
                    author_papers[author_name]["papers"].append(paper)
                    
                    # Track authorship position
                    if i == 0:
                        author_papers[author_name]["first_author"] += 1
                    elif i == len(authors) - 1:
                        author_papers[author_name]["last_author"] += 1
                    else:
                        author_papers[author_name]["middle_author"] += 1
                    
                    # Track affiliations
                    if author.get("affiliation"):
                        author_papers[author_name]["affiliations"].add(author.get("affiliation"))
            
            profiles = []
            for author_name, data in author_papers.items():
                # Calculate confidence score
                confidence = 0.4  # Lower base confidence for EuropePMC
                if affiliation and data["affiliations"]:
                    for aff in data["affiliations"]:
                        if affiliation.lower() in aff.lower():
                            confidence += 0.4
                            break
                
                profile = AuthorProfile(
                    name=author_name,
                    author_id=f"europepmc_{hash(author_name)}",  # Generate pseudo-ID
                    service="europepmc",
                    affiliation=", ".join(list(data["affiliations"])[:3]),
                    field_of_study="Biomedical Sciences",  # EuropePMC is biomedical focused
                    paper_count=len(data["papers"]),
                    citation_count=sum([int(p.get("citedByCount", 0)) for p in data["papers"]]),
                    first_author_papers=data["first_author"],
                    last_author_papers=data["last_author"],
                    middle_author_papers=data["middle_author"],
                    confidence_score=min(confidence, 1.0),
                    profile_url=f"https://europepmc.org/search?query=AUTH%3A%22{author_name.replace(' ', '%20')}%22",
                    recent_papers=[{
                        "title": p.get("title", ""),
                        "year": p.get("pubYear")
                    } for p in data["papers"][:5]]
                )
                profiles.append(profile)
            
            return profiles
            
        except Exception as e:
            logger.error(f"Error searching EuropePMC: {e}")
            return []

    async def disambiguate_author(self, name: str, affiliation: str = None, 
                                field: str = None, keywords: str = None) -> Dict[str, Any]:
        """Main disambiguation function that queries all services and returns ranked results"""
        
        # Search all services concurrently
        tasks = [
            self.search_semantic_scholar(name, affiliation, field, keywords),
            self.search_openalex(name, affiliation, field, keywords),
            self.search_europepmc(name, affiliation, field, keywords)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_profiles = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error in service {i}: {result}")
                continue
            all_profiles.extend(result)
        
        # Sort by confidence score and seniority
        all_profiles.sort(key=lambda x: (x.confidence_score, x.seniority_score), reverse=True)
        
        # Prepare summary
        summary = {
            "query": {
                "name": name,
                "affiliation": affiliation,
                "field": field,
                "keywords": keywords
            },
            "total_candidates": len(all_profiles),
            "services_searched": ["semantic_scholar", "openalex", "europepmc"],
            "best_match": asdict(all_profiles[0]) if all_profiles else None,
            "all_candidates": [asdict(profile) for profile in all_profiles[:10]],  # Top 10
            "disambiguation_timestamp": datetime.now().isoformat()
        }
        
        return summary

    def setup_tools(self):
        """Setup MCP tools"""
        
        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            return ListToolsResult(
                tools=[
                    Tool(
                        name="disambiguate_author",
                        description="Disambiguate an author across multiple scientific databases (Semantic Scholar, OpenAlex, EuropePMC)",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Author name or surname"
                                },
                                "affiliation": {
                                    "type": "string",
                                    "description": "Current or known affiliation of the author"
                                },
                                "field": {
                                    "type": "string",
                                    "description": "Field of study or research area"
                                },
                                "keywords": {
                                    "type": "string",
                                    "description": "Additional keywords to help with disambiguation"
                                }
                            },
                            "required": ["name"]
                        }
                    ),
                    Tool(
                        name="search_semantic_scholar",
                        description="Search specifically in Semantic Scholar database",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Author name"},
                                "affiliation": {"type": "string", "description": "Author affiliation"},
                                "field": {"type": "string", "description": "Field of study"},
                                "keywords": {"type": "string", "description": "Additional keywords"}
                            },
                            "required": ["name"]
                        }
                    ),
                    Tool(
                        name="search_openalex",
                        description="Search specifically in OpenAlex database",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Author name"},
                                "affiliation": {"type": "string", "description": "Author affiliation"},
                                "field": {"type": "string", "description": "Field of study"},
                                "keywords": {"type": "string", "description": "Additional keywords"}
                            },
                            "required": ["name"]
                        }
                    ),
                    Tool(
                        name="search_europepmc",
                        description="Search specifically in EuropePMC database",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Author name"},
                                "affiliation": {"type": "string", "description": "Author affiliation"},
                                "field": {"type": "string", "description": "Field of study"},
                                "keywords": {"type": "string", "description": "Additional keywords"}
                            },
                            "required": ["name"]
                        }
                    )
                ]
            )

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            try:
                if name == "disambiguate_author":
                    result = await self.disambiguate_author(
                        name=arguments["name"],
                        affiliation=arguments.get("affiliation"),
                        field=arguments.get("field"),
                        keywords=arguments.get("keywords")
                    )
                    return CallToolResult(
                        content=[TextContent(type="text", text=json.dumps(result, indent=2))]
                    )
                
                elif name == "search_semantic_scholar":
                    profiles = await self.search_semantic_scholar(
                        name=arguments["name"],
                        affiliation=arguments.get("affiliation"),
                        field=arguments.get("field"),
                        keywords=arguments.get("keywords")
                    )
                    result = {"service": "semantic_scholar", "profiles": [asdict(p) for p in profiles]}
                    return CallToolResult(
                        content=[TextContent(type="text", text=json.dumps(result, indent=2))]
                    )
                
                elif name == "search_openalex":
                    profiles = await self.search_openalex(
                        name=arguments["name"],
                        affiliation=arguments.get("affiliation"),
                        field=arguments.get("field"),
                        keywords=arguments.get("keywords")
                    )
                    result = {"service": "openalex", "profiles": [asdict(p) for p in profiles]}
                    return CallToolResult(
                        content=[TextContent(type="text", text=json.dumps(result, indent=2))]
                    )
                
                elif name == "search_europepmc":
                    profiles = await self.search_europepmc(
                        name=arguments["name"],
                        affiliation=arguments.get("affiliation"),
                        field=arguments.get("field"),
                        keywords=arguments.get("keywords")
                    )
                    result = {"service": "europepmc", "profiles": [asdict(p) for p in profiles]}
                    return CallToolResult(
                        content=[TextContent(type="text", text=json.dumps(result, indent=2))]
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
    server = AuthorDisambiguationServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
