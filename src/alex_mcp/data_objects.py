#!/usr/bin/env python3
"""
Data models for the OpenAlex MCP server.

Defines the structure of author search results and the overall search response,
following the OpenAlex Author object specification:
https://docs.openalex.org/api-entities/authors/author-object
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class AuthorResult(BaseModel):
    """
    Represents a single author as returned by the OpenAlex API.

    Fields:
        id: OpenAlex unique author ID (e.g., 'https://openalex.org/A123456789').
        orcid: ORCID identifier if available.
        display_name: Primary display name of the author.
        display_name_alternatives: Alternative names for the author.
        affiliations: List of current and past affiliations (institution objects).
        cited_by_count: Total number of citations received by this author.
        counts_by_year: List of yearly publication/citation counts.
        ids: Dictionary of external IDs (e.g., OpenAlex, ORCID, etc.).
        summary_stats: Summary statistics (e.g., h-index, i10-index).
        updated_date: Last update date for this author record (ISO 8601).
        works_api_url: API URL to retrieve all works by this author.
        works_count: Total number of works (publications) by this author.
        x_concepts: (Deprecated) List of concepts associated with this author.
        topics: List of topic objects (future replacement for x_concepts).
    """
    id: str
    orcid: Optional[str] = None
    display_name: str
    display_name_alternatives: Optional[List[str]] = None
    affiliations: Optional[List[Dict[str, Any]]] = None
    cited_by_count: int
    counts_by_year: Optional[List[Dict[str, Any]]] = None
    ids: Optional[Dict[str, str]] = None
    summary_stats: Optional[Dict[str, Any]] = None
    updated_date: Optional[str] = None
    works_api_url: Optional[str] = None
    works_count: int
    x_concepts: Optional[List[Dict[str, Any]]] = None  # Deprecated, but included for now
    topics: Optional[List[Dict[str, Any]]] = None      # For future compatibility


class SearchResponse(BaseModel):
    """
    Represents the response to an author search query.

    Fields:
        query: The original search query string.
        total_count: Number of authors found matching the query.
        results: List of AuthorResult objects.
        search_time: Timestamp when the search was performed.
    """
    query: str
    total_count: int
    results: List[AuthorResult]
    search_time: Optional[datetime] = Field(default_factory=datetime.now)


class WorkResult(BaseModel):
    """
    Represents a single work (publication) as returned by the OpenAlex API.

    Fields:
        abstract_inverted_index: Inverted index of the abstract.
        authorships: List of authorship objects.
        citation_normalized_percentile: Citation percentile.
        corresponding_author_ids: List of corresponding author OpenAlex IDs.
        counts_by_year: List of yearly publication/citation counts.
        doi: DOI of the work.
        fwci: Field-weighted citation impact.
        grants: List of grant objects.
        has_fulltext: Whether the work has full text available.
        id: OpenAlex unique work ID.
        ids: Dictionary of external IDs.
        indexed_in: List of indexes where the work is indexed.
        is_retracted: Whether the work is retracted.
        keywords: List of keywords.
        locations: List of location objects (may contain URLs).
        open_access: Open access information.
        primary_topic: Primary topic object.
        publication_year: Year of publication.
        referenced_works: List of referenced work IDs.
        related_works: List of related work IDs.
        title: Title of the work.
        type: Type of the work (e.g., journal-article).
    """
    abstract_inverted_index: Optional[Dict[str, List[int]]] = None
    authorships: Optional[List[Dict[str, Any]]] = None
    citation_normalized_percentile: Optional[Dict[str, Any]] = None
    corresponding_author_ids: Optional[List[str]] = None
    counts_by_year: Optional[List[Dict[str, Any]]] = None
    doi: Optional[str] = None
    fwci: Optional[float] = None
    grants: Optional[List[Dict[str, Any]]] = None
    has_fulltext: Optional[bool] = None
    id: str
    ids: Optional[Dict[str, str]] = None
    indexed_in: Optional[List[str]] = None
    is_retracted: Optional[bool] = None
    keywords: Optional[List[Dict[str, Any]]] = None
    locations: Optional[List[Dict[str, Any]]] = None
    open_access: Optional[Dict[str, Any]] = None
    primary_topic: Optional[Dict[str, Any]] = None
    publication_year: Optional[int] = None
    referenced_works: Optional[List[str]] = None
    related_works: Optional[List[str]] = None
    title: Optional[str] = None
    type: Optional[str] = None

class WorksSearchResponse(BaseModel):
    """
    Represents the response to a works search query.

    Fields:
        author_id: The OpenAlex Author ID used for the search.
        total_count: Number of works found matching the query.
        results: List of WorkResult objects.
        search_time: Timestamp when the search was performed.
        filters: Dictionary of filters applied to the search.
    """
    author_id: str
    total_count: int
    results: List[WorkResult]
    search_time: Optional[datetime] = Field(default_factory=datetime.now)
    filters: Optional[Dict[str, Any]] = None