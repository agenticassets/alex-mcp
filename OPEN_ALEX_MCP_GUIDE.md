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
      "env": {"OPENALEX_MAILTO": "$env:OPENALEX_MAILTO"}
    }
  }
}
```

**Note**: Set `$env:OPENALEX_MAILTO` in your PowerShell session before using Cursor AI.

## 8 Tools

### Core Academic (OpenAlex)
- `autocomplete_authors` ⭐ - Author disambiguation (start here)
- `search_authors` - Full author profiles with ORCID/affiliations
- `retrieve_author_works` - Publication history by author ID
- `search_works` - Find papers by topic/keywords

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
- Set `limit` to control response size
- Required: `OPENALEX_MAILTO` environment variable

## Status: ✅ All 8 tools operational (<500ms)
