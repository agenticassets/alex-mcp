# Alex-MCP Tool Reference

**Note**: Requires `OPENALEX_MAILTO` environment variable set to your email address for OpenAlex API access.

## Configurable Defaults
All function limits can be customized via environment variables in your `mcp.json`:
- **Hardcoded defaults**: All functions default to **5** results
- **Environment override**: Set custom defaults via env vars (see examples below)
- **Parameter override**: Explicit `limit` parameters override both defaults and env vars (must be numeric)

**Priority**: `Explicit parameter > Environment variable > Hardcoded default (5)`

## OpenAlex Academic Tools

### `autocomplete_authors`
**Purpose**: Fast author disambiguation with institutional context
**Parameters**:
- `name` (str): Author name to search
- `context` (str, optional): Institutional context for ranking
- `limit` (int, optional): Max results (1-15, default: 5 or env var DEFAULT_AUTOCOMPLETE_AUTHORS_LIMIT)
**Returns**: Ranked author candidates with institution hints, citation counts

### `search_authors`
**Purpose**: Comprehensive author search with full metadata
**Parameters**:
- `name` (str): Author name
- `institution` (str, optional): Institution filter
- `topic` (str, optional): Research topic filter
- `country_code` (str, optional): Country filter
- `limit` (int, optional): Max results (1-100, default: 5 or env var DEFAULT_SEARCH_AUTHORS_LIMIT)
**Returns**: Author profiles with ORCID, affiliations, metrics, research fields

### `retrieve_author_works`
**Purpose**: Get complete publication history
**Parameters**:
- `author_id` (str): OpenAlex author ID
- `limit` (int, optional): Max results (1-2000, default: 5 or env var DEFAULT_RETRIEVE_AUTHOR_WORKS_LIMIT)
- `order_by` (str, optional): "date" or "citations" (default: "date")
- `publication_year` (int, optional): Filter by year
- `type` (str, optional): Work type filter
- `journal_only` (bool, optional): If True, only return journal articles and letters (default: True)
- `min_citations` (int, optional): Only return works with at least this many citations
- `peer_reviewed_only` (bool, optional): If True, apply balanced peer-review filters (default: True)
- `include_abstract` (bool, optional): Include full paper abstracts when available (default: true)
**Returns**: Publications with DOIs, journals, citations, topics (optionally includes abstracts)

### `search_works`
**Purpose**: Find academic papers by topic
**Parameters**:
- `query` (str): Search query
- `author` (str, optional): Author filter
- `institution` (str, optional): Institution filter
- `publication_year` (int, optional): Year filter
- `type` (str, optional): Work type filter
- `limit` (int, optional): Max results (1-100, default: 5 or env var DEFAULT_SEARCH_WORKS_LIMIT)
- `peer_reviewed_only` (bool, optional): Journal articles only (default: true)
- `search_type` (str, optional): Search mode - "general", "title", or "title_and_abstract" (default: "general")
- `include_abstract` (bool, optional): Include full paper abstracts when available (dynamic default: true for limit ≤ 3, false for limit ≥ 4)
**Returns**: Peer-reviewed papers with full metadata (optionally includes abstracts)

### `get_work_by_id`
**Purpose**: Retrieve a single paper by OpenAlex ID
**Parameters**:
- `work_id` (str): OpenAlex work ID (accepts "W1234567890", "1234567890", or full URL)
- `include_abstract` (bool, optional): Include full paper abstract (default: true)
**Returns**: Single work with complete metadata, DOI, citations, journal info
**Usage**: `get_work_by_id("W2741809807")` or `get_work_by_id("2741809807")`

## ORCID Identity Tools

### `search_orcid_authors`
**Purpose**: Find researchers by ORCID
**Parameters**:
- `name` (str): Author name
- `affiliation` (str, optional): Institutional affiliation
- `max_results` (int, optional): Max results (1-50, default: 5 or env var DEFAULT_ORCID_SEARCH_LIMIT)
**Returns**: ORCID profiles with employment history

### `get_orcid_publications`
**Purpose**: Get publications from ORCID profile
**Parameters**:
- `orcid_id` (str): ORCID identifier
- `max_works` (int, optional): Max works (1-100, default: 5 or env var DEFAULT_ORCID_WORKS_LIMIT)
**Returns**: Complete publication list with DOIs, journals

## Data Structures

### Author Object
```json
{
  "id": "https://openalex.org/A5090973432",
  "display_name": "Author Name",
  "orcid": "https://orcid.org/0000-0000-0000-0000",
  "affiliations": ["Institution Name"],
  "cited_by_count": 123,
  "works_count": 45,
  "h_index": 8,
  "research_fields": ["Field1", "Field2"]
}
```

### Work Object
```json
{
  "id": "https://openalex.org/W4411935046",
  "title": "Paper Title",
  "doi": "10.1234/journal.123456",
  "publication_year": 2024,
  "cited_by_count": 15,
  "journal_name": "Journal Name",
  "is_open_access": true,
  "primary_field": "Research Field",
  "abstract": "Full paper abstract text..."
}
```

## Environment Variable Configuration

You can customize default limits by adding environment variables to your `mcp.json`:

```json
{
  "mcpServers": {
    "alex-mcp": {
      "command": "path/to/alex-mcp/venv/Scripts/python.exe",
      "args": ["-m", "alex_mcp.server"],
      "env": {
        "OPENALEX_MAILTO": "$env:OPENALEX_MAILTO",
        "DEFAULT_SEARCH_AUTHORS_LIMIT": "10",
        "DEFAULT_SEARCH_WORKS_LIMIT": "15",
        "DEFAULT_AUTOCOMPLETE_AUTHORS_LIMIT": "8",
        "DEFAULT_RETRIEVE_AUTHOR_WORKS_LIMIT": "20",
        "DEFAULT_PUBMED_SEARCH_LIMIT": "12",
        "DEFAULT_PUBMED_SAMPLE_SIZE": "7",
        "DEFAULT_ORCID_SEARCH_LIMIT": "6",
        "DEFAULT_ORCID_WORKS_LIMIT": "25"
      }
    }
  }
}
```

**Examples**:
- `search_authors("John Smith")` → Uses `DEFAULT_SEARCH_AUTHORS_LIMIT` (10 in example above)
- `search_authors("John Smith", limit=25)` → Uses explicit parameter (25)
- If no env var set → Uses hardcoded default (5)

## Usage Workflows

### Citation Validation Workflow
**Recommended for validating academic citations:**
1. **Discovery**: Use `search_works(query="Author Year key terms", limit=1)` to find papers
2. **Validation**: Use `get_work_by_id(work_id="W123456789", include_abstract=true)` for detailed verification
3. **Note**: Use `get_work_by_id` specifically, NOT `get_orcid_publications` for citation validation


