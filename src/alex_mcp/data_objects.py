#!/usr/bin/env python3
"""
Data objects for structured output from the OpenAlex MCP server
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class WorkResult:
    """Structured data object for a scholarly work"""
    openalex_id: str
    title: str
    authors: List[str] = field(default_factory=list)
    publication_year: Optional[int] = None
    venue: Optional[str] = None
    work_type: Optional[str] = None
    citations: int = 0
    is_open_access: bool = False
    abstract: Optional[str] = None
    doi: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "openalex_id": self.openalex_id,
            "title": self.title,
            "authors": self.authors,
            "publication_year": self.publication_year,
            "venue": self.venue,
            "type": self.work_type,
            "citations": self.citations,
            "is_open_access": self.is_open_access,
            "abstract": self.abstract,
            "doi": self.doi
        }

@dataclass
class AuthorResult:
    """Structured data object for an author"""
    openalex_id: str
    display_name: str
    orcid: Optional[str] = None
    institutions: List[str] = field(default_factory=list)
    works_count: int = 0
    cited_by_count: int = 0
    h_index: Optional[int] = None
    research_topics: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    match_reasons: List[str] = field(default_factory=list)
    career_stage: str = "Unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "openalex_id": self.openalex_id,
            "display_name": self.display_name,
            "orcid": self.orcid,
            "institutions": self.institutions,
            "works_count": self.works_count,
            "cited_by_count": self.cited_by_count,
            "h_index": self.h_index,
            "research_topics": self.research_topics,
            "confidence_score": self.confidence_score,
            "match_reasons": self.match_reasons,
            "career_stage": self.career_stage
        }

@dataclass
class InstitutionResult:
    """Structured data object for an institution"""
    openalex_id: str
    display_name: str
    country_code: Optional[str] = None
    institution_type: Optional[str] = None
    homepage_url: Optional[str] = None
    alternative_names: List[str] = field(default_factory=list)
    match_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "openalex_id": self.openalex_id,
            "display_name": self.display_name,
            "country_code": self.country_code,
            "type": self.institution_type,
            "homepage_url": self.homepage_url,
            "alternative_names": self.alternative_names,
            "match_score": self.match_score
        }

@dataclass
class TopicResult:
    """Structured data object for a research topic"""
    openalex_id: str
    display_name: str
    level: int
    description: Optional[str] = None
    works_count: int = 0
    cited_by_count: int = 0
    related_topics: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "openalex_id": self.openalex_id,
            "display_name": self.display_name,
            "level": self.level,
            "description": self.description,
            "works_count": self.works_count,
            "cited_by_count": self.cited_by_count,
            "related_topics": self.related_topics
        }

@dataclass
class SearchResponse:
    """Generic search response wrapper"""
    query: str
    total_count: int
    results: List[Any] = field(default_factory=list)
    search_time: Optional[datetime] = None
    
    def __post_init__(self):
        if self.search_time is None:
            self.search_time = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "query": self.query,
            "total_count": self.total_count,
            "results": [r.to_dict() if hasattr(r, 'to_dict') else r for r in self.results],
            "search_time": self.search_time.isoformat() if self.search_time else None
        }
