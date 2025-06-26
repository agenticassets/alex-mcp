#!/usr/bin/env python3
"""
OpenAlex Author Disambiguation MCP Server

Provides a FastMCP-compliant API for author disambiguation and institution resolution
using the OpenAlex API and pyalex client.

Features:
- Author search and disambiguation with rich metadata
- Institution name resolution
- ORCID integration
- Publication and citation metrics
- Full MCP protocol compliance

See https://docs.openalex.org/api-entities/authors/author-object for the Author object specification.
"""

import logging
from typing import Optional
from fastmcp import FastMCP
from alex_mcp.data_objects import (
    AuthorResult,
    SearchResponse,
    WorksSearchResponse,
    WorkResult
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
        "OPENALEX_MAX_AUTHORS": int(os.environ.get("OPENALEX_MAX_AUTHORS", 100)),
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

# Example: load from environment or config file in production
config = get_config()
configure_pyalex(config["OPENALEX_MAILTO"])
pyalex.config.user_agent = config["OPENALEX_USER_AGENT"]

def search_authors_core(
    name: str,
    institution: Optional[str] = None,
    topic: Optional[str] = None,
    country_code: Optional[str] = None,
    limit: int = 20
) -> SearchResponse:
    """
    Core logic for searching authors using OpenAlex.

    Args:
        name: Author name to search for.
        institution: (Optional) Institution name filter.
        topic: (Optional) Topic filter.
        country_code: (Optional) Country code filter.
        limit: Maximum number of results to return.

    Returns:
        SearchResponse: Structured response with author results.
    """
    query = pyalex.Authors().search_filter(display_name=name)
    # Add additional filters as needed...
    results = query.get(per_page=limit)
    authors = list(results)
    author_list = []
    for a in authors:
        author_result = AuthorResult(
            id=a.get("id"),
            orcid=a.get("orcid"),
            display_name=a.get("display_name"),
            display_name_alternatives=a.get("display_name_alternatives"),
            affiliations=a.get("affiliations"),
            cited_by_count=a.get("cited_by_count"),
            counts_by_year=a.get("counts_by_year"),
            ids=a.get("ids"),
            summary_stats=a.get("summary_stats"),
            updated_date=a.get("updated_date"),
            works_api_url=a.get("works_api_url"),
            works_count=a.get("works_count"),
            x_concepts=a.get("x_concepts"),
            topics=a.get("topics"),
        )
        author_list.append(author_result)
    return SearchResponse(
        query=name,
        total_count=len(author_list),
        results=author_list
    )


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

    Args:
        name: Author name to search for.
        institution: (Optional) Institution name filter.
        topic: (Optional) Topic filter.
        country_code: (Optional) Country code filter.
        limit: Maximum number of results to return.

    Returns:
        dict: Serialized SearchResponse.
    """
    response = search_authors_core(
        name=name,
        institution=institution,
        topic=topic,
        country_code=country_code,
        limit=limit
    )
    return response.dict()


def retrieve_author_works_core(
    author_id: str,
    limit: int = 20,
    order_by: str = "date",  # "date" or "citations"
    authorships_author_orcid: Optional[str] = None,
    authorships_institutions_id: Optional[str] = None,
    authorships_is_corresponding: Optional[bool] = None,
    best_oa_location_is_accepted: Optional[bool] = None,
    best_oa_location_is_published: Optional[bool] = None,
    cited_by_count: Optional[int] = None,
    concepts_id: Optional[str] = None,
    doi: Optional[str] = None,
    has_fulltext: Optional[bool] = None,
    fulltext_origin: Optional[str] = None,
    ids_pmcid: Optional[str] = None,
    ids_pmid: Optional[str] = None,
    ids_openalex: Optional[str] = None,
    is_retracted: Optional[bool] = None,
    keywords_keyword: Optional[str] = None,
    locations_is_accepted: Optional[bool] = None,
    locations_is_oa: Optional[bool] = None,
    locations_is_published: Optional[bool] = None,
    locations_source_id: Optional[str] = None,
    locations_source_type: Optional[str] = None,
    open_access_is_oa: Optional[bool] = None,
    publication_year: Optional[int] = None,
    topics_id: Optional[str] = None,
    topics_field_id: Optional[str] = None,
    type: Optional[str] = None,
) -> WorksSearchResponse:
    """
    Core logic to retrieve works for a given OpenAlex Author ID, with optional filters and ordering.
    """

    filters = {"author.id": author_id}
    if authorships_author_orcid: filters["authorships.author.orcid"] = authorships_author_orcid
    if authorships_institutions_id: filters["authorships.institutions.id"] = authorships_institutions_id
    if authorships_is_corresponding is not None: filters["authorships.is_corresponding"] = authorships_is_corresponding
    if best_oa_location_is_accepted is not None: filters["best_oa_location.is_accepted"] = best_oa_location_is_accepted
    if best_oa_location_is_published is not None: filters["best_oa_location.is_published"] = best_oa_location_is_published
    if cited_by_count is not None: filters["cited_by_count"] = cited_by_count
    if concepts_id: filters["concepts.id"] = concepts_id
    if doi: filters["doi"] = doi
    if has_fulltext is not None: filters["has_fulltext"] = has_fulltext
    if fulltext_origin: filters["fulltext_origin"] = fulltext_origin
    if ids_pmcid: filters["ids.pmcid"] = ids_pmcid
    if ids_pmid: filters["ids.pmid"] = ids_pmid
    if ids_openalex: filters["ids.openalex"] = ids_openalex
    if is_retracted is not None: filters["is_retracted"] = is_retracted
    if keywords_keyword: filters["keywords.keyword"] = keywords_keyword
    if locations_is_accepted is not None: filters["locations.is_accepted"] = locations_is_accepted
    if locations_is_oa is not None: filters["locations.is_oa"] = locations_is_oa
    if locations_is_published is not None: filters["locations.is_published"] = locations_is_published
    if locations_source_id: filters["locations.source.id"] = locations_source_id
    if locations_source_type: filters["locations.source.type"] = locations_source_type
    if open_access_is_oa is not None: filters["open_access.is_oa"] = open_access_is_oa
    if publication_year is not None: filters["publication_year"] = publication_year
    if topics_id: filters["topics.id"] = topics_id
    if topics_field_id: filters["topics.field.id"] = topics_field_id
    if type: filters["type"] = type

    # Convert author_id to OpenAlex format if needed
    if author_id.startswith("https://openalex.org/"):
        author_id_short = author_id.split("/")[-1]
        filters["author.id"] = f"https://openalex.org/{author_id_short}"

    if order_by == "citations":
        sort = "cited_by_count:desc"
    else:
        sort = "updated_date:desc"
    works_query = pyalex.Works().filter(**filters)
    
    works = list(works_query.get(per_page=limit * 2))  # Fetch more to allow sorting
    if order_by == "citations":
        works.sort(key=lambda w: w.get("cited_by_count", 0), reverse=True)
    else:
        works.sort(key=lambda w: w.get("updated_date", ""), reverse=True)
    works = works[:limit]    
    
    try:
        works = list(works_query.get(per_page=limit))
        work_results = [
            WorkResult(
                abstract_inverted_index=w.get("abstract_inverted_index"),
                authorships=w.get("authorships"),
                citation_normalized_percentile=w.get("citation_normalized_percentile"),
                corresponding_author_ids=w.get("corresponding_author_ids"),
                counts_by_year=w.get("counts_by_year"),
                doi=w.get("doi"),
                fwci=w.get("fwci"),
                grants=w.get("grants"),
                has_fulltext=w.get("has_fulltext"),
                id=w.get("id"),
                ids=w.get("ids"),
                indexed_in=w.get("indexed_in"),
                is_retracted=w.get("is_retracted"),
                keywords=w.get("keywords"),
                locations=w.get("locations"),
                open_access=w.get("open_access"),
                primary_topic=w.get("primary_topic"),
                publication_year=w.get("publication_year"),
                referenced_works=w.get("referenced_works"),
                related_works=w.get("related_works"),
                title=w.get("title"),
                type=w.get("type"),
            )
            for w in works
        ]
        return WorksSearchResponse(
            author_id=author_id,
            total_count=len(work_results),
            results=work_results,
            filters=filters
        )
    except Exception as e:
        logger.error(f"Error retrieving works for author {author_id}: {e}")
        return WorksSearchResponse(
            author_id=author_id,
            total_count=0,
            results=[],
            filters=filters
        )


@mcp.tool(
    annotations={
        "title": "Retrieve Author Works",
        "description": (
            "Given an OpenAlex Author ID and optional filters, retrieve the list of works (publications) for that author. "
            "You can order by date (default) or by citations. "
            "See https://docs.openalex.org/api-entities/works/filter-works for filter details."
        ),
        "readOnlyHint": True,
        "openWorldHint": True
    }
)


async def retrieve_author_works(
    author_id: str,
    limit: int = 20,
    order_by: str = "date",
    authorships_author_orcid: Optional[str] = None,
    authorships_institutions_id: Optional[str] = None,
    authorships_is_corresponding: Optional[bool] = None,
    best_oa_location_is_accepted: Optional[bool] = None,
    best_oa_location_is_published: Optional[bool] = None,
    cited_by_count: Optional[int] = None,
    concepts_id: Optional[str] = None,
    doi: Optional[str] = None,
    has_fulltext: Optional[bool] = None,
    fulltext_origin: Optional[str] = None,
    ids_pmcid: Optional[str] = None,
    ids_pmid: Optional[str] = None,
    ids_openalex: Optional[str] = None,
    is_retracted: Optional[bool] = None,
    keywords_keyword: Optional[str] = None,
    locations_is_accepted: Optional[bool] = None,
    locations_is_oa: Optional[bool] = None,
    locations_is_published: Optional[bool] = None,
    locations_source_id: Optional[str] = None,
    locations_source_type: Optional[str] = None,
    open_access_is_oa: Optional[bool] = None,
    publication_year: Optional[int] = None,
    topics_id: Optional[str] = None,
    topics_field_id: Optional[str] = None,
    type: Optional[str] = None,
) -> dict:
    """
    MCP tool wrapper for retrieving works for a given author with optional filters and ordering.
    """
    response = retrieve_author_works_core(
        author_id=author_id,
        limit=limit,
        order_by=order_by,
        authorships_author_orcid=authorships_author_orcid,
        authorships_institutions_id=authorships_institutions_id,
        authorships_is_corresponding=authorships_is_corresponding,
        best_oa_location_is_accepted=best_oa_location_is_accepted,
        best_oa_location_is_published=best_oa_location_is_published,
        cited_by_count=cited_by_count,
        concepts_id=concepts_id,
        doi=doi,
        has_fulltext=has_fulltext,
        fulltext_origin=fulltext_origin,
        ids_pmcid=ids_pmcid,
        ids_pmid=ids_pmid,
        ids_openalex=ids_openalex,
        is_retracted=is_retracted,
        keywords_keyword=keywords_keyword,
        locations_is_accepted=locations_is_accepted,
        locations_is_oa=locations_is_oa,
        locations_is_published=locations_is_published,
        locations_source_id=locations_source_id,
        locations_source_type=locations_source_type,
        open_access_is_oa=open_access_is_oa,
        publication_year=publication_year,
        topics_id=topics_id,
        topics_field_id=topics_field_id,
        type=type,
    )
    return response.dict()

def main():
    """
    Entry point for the alex-mcp server.
    """
    import asyncio
    logger.info("OpenAlex Author Disambiguation MCP Server starting...")
    asyncio.run(mcp.run())

if __name__ == "__main__":
    main()