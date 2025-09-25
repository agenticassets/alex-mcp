# Alex-MCP Quick Guide

## Setup (Windows/Cursor AI)
**Note**: Requires `$env:OPENALEX_MAILTO` environment variable set to your email address for OpenAlex API access.

**1. Set Environment Variable** (Required):
```powershell
$env:OPENALEX_MAILTO = "your-email@domain.com"
```

**2. Cursor AI Config** (`mcp.json`):
```json
{
  "mcpServers": {
    "alex-mcp": {
      "command": "C:/path/to/alex-mcp/venv/Scripts/alex-mcp.exe",
      "env": {
        "OPENALEX_MAILTO": "$env:OPENALEX_MAILTO",
        "DEFAULT_SEARCH_AUTHORS_LIMIT": "10",
        "DEFAULT_SEARCH_WORKS_LIMIT": "15",
        "DEFAULT_AUTOCOMPLETE_AUTHORS_LIMIT": "8",
        "DEFAULT_RETRIEVE_AUTHOR_WORKS_LIMIT": "20"
      }
    }
  }
}
```

**🔧 Configurable Defaults**: All functions default to **5** results, but you can customize via environment variables in `mcp.json` (see above). Explicit `limit` parameters always override defaults.

**Note**: Set `$env:OPENALEX_MAILTO` in your PowerShell session before using Cursor AI.

## 9 Tools

### Core Academic (OpenAlex)
- `autocomplete_authors` ⭐ - Author disambiguation (start here)
- `search_authors` - Full author profiles with ORCID/affiliations
- `retrieve_author_works` - Publication history by author ID
- `search_works` - Find papers by topic/keywords
- `get_work_by_id` - Retrieve single paper by OpenAlex ID

### Medical (PubMed)
- `search_pubmed` - Medical literature search
- `pubmed_author_sample` - Author institutional analysis

### Identity (ORCID)
- `search_orcid_authors` - Find researchers by name/affiliation
- `get_orcid_publications` - Publications from ORCID profile

## Usage Examples

```python
# Author disambiguation
candidates = await autocomplete_authors("John Smith", context="Harvard")

# Author details
author = await search_authors("Cayman Seagraves", institution="UTulsa")

# Publications
works = await retrieve_author_works("https://openalex.org/A5090973432")

# Paper search
papers = await search_works("real estate AI", limit=10)

# Get specific paper by ID
paper = await get_work_by_id("W2741809807")

# Medical research
pubmed = await search_pubmed("machine learning", max_results=5)

# ORCID lookup
orcid_works = await get_orcid_publications("0000-0002-6124-7440")
```

## Key Fields

**Author**: `id`, `display_name`, `orcid`, `affiliations`, `cited_by_count`, `works_count`, `h_index`

**Work**: `id`, `title`, `doi`, `publication_year`, `cited_by_count`, `journal_name`, `is_open_access`, `abstract` (optional)

## Tips
- Start with `autocomplete_authors` for disambiguation
- Use ORCID IDs for precision
- **Defaults**: All functions return **5** results by default
- **Custom limits**: Set environment variables in `mcp.json` to change defaults
- **Override**: Use explicit `limit` parameters to override both defaults and env vars
- Required: `OPENALEX_MAILTO` environment variable

## Default Configuration Examples

**Without custom env vars** (hardcoded defaults):
```python
search_authors("John Smith")        # Returns 5 authors
search_works("AI research")         # Returns 5 papers
autocomplete_authors("Jane Doe")    # Returns 5 candidates
```

**With custom env vars** (from mcp.json above):
```python
search_authors("John Smith")        # Returns 10 authors (from DEFAULT_SEARCH_AUTHORS_LIMIT)
search_works("AI research")         # Returns 15 papers (from DEFAULT_SEARCH_WORKS_LIMIT)
autocomplete_authors("Jane Doe")    # Returns 8 candidates (from DEFAULT_AUTOCOMPLETE_AUTHORS_LIMIT)
```

**With explicit parameters** (always wins):
```python
search_authors("John Smith", limit=25)     # Returns 25 authors (overrides env var)
search_works("AI research", limit=50)      # Returns 50 papers (overrides env var)
```

## Status: ✅ All 9 tools operational (<500ms)
