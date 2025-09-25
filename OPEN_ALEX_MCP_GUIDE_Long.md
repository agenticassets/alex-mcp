# Alex-MCP Usage Guide

## 🚀 Quick Start

### 1. Installation
```bash
git clone https://github.com/drAbreu/alex-mcp.git
cd alex-mcp
python -m venv venv
venv\Scripts\activate  # Windows
pip install -e .
```

### 2. Cursor AI Configuration
Add to your `mcp.json`:
```json
{
  "mcpServers": {
    "alex-mcp": {
      "command": "C:/path/to/alex-mcp/venv/Scripts/alex-mcp.exe",
      "env": {
        "OPENALEX_MAILTO": "your-email@domain.com"
      }
    }
  }
}
```

### 3. Environment Setup
```bash
export OPENALEX_MAILTO=your-email@domain.com
```

## 🛠️ Available Tools

### Academic Research Core

#### `autocomplete_authors` ⭐ **RECOMMENDED FIRST STEP**
**Purpose**: Smart author disambiguation with institutional context
```python
# Best for initial author searches
candidates = await autocomplete_authors(
    "John Smith",
    context="Harvard University",
    limit=5
)
# Returns: Ranked candidates with institution hints, citation counts
```

#### `search_authors`
**Purpose**: Comprehensive author search with full metadata
```python
authors = await search_authors(
    name="Cayman Seagraves",
    institution="University of Tulsa",
    limit=10
)
# Returns: ORCID, affiliations, citation metrics, research fields
```

#### `retrieve_author_works`
**Purpose**: Get complete publication history
```python
works = await retrieve_author_works(
    author_id="https://openalex.org/A5090973432",
    limit=20,
    order_by="citations",  # or "date"
    include_abstract=True  # optional: include full paper abstracts
)
# Returns: Publications with DOIs, journals, citations, topics (optionally includes abstracts)
```

#### `search_works`
**Purpose**: Find academic papers by topic
```python
papers = await search_works(
    query="machine learning healthcare",
    limit=15,
    peer_reviewed_only=True,
    include_abstract=True  # optional: include full paper abstracts
)
# Returns: Peer-reviewed papers with full metadata (optionally includes abstracts)
```

### Medical Research (PubMed)

#### `search_pubmed`
**Purpose**: Search PubMed medical literature
```python
results = await search_pubmed(
    query="COVID-19 vaccines",
    search_type="keywords",
    max_results=10
)
# Returns: PMIDs, titles, authors, journals, DOIs
```

#### `pubmed_author_sample`
**Purpose**: Analyze author institutional patterns
```python
profile = await pubmed_author_sample(
    author_name="Dr. Smith",
    sample_size=5
)
# Returns: Institutional keywords, name variants, email patterns
```

### Researcher Identity (ORCID)

#### `search_orcid_authors`
**Purpose**: Find researchers by ORCID
```python
researchers = await search_orcid_authors(
    name="Marie Curie",
    affiliation="Sorbonne",
    max_results=5
)
# Returns: ORCID profiles with affiliations
```

#### `get_orcid_publications`
**Purpose**: Get publications from ORCID profile
```python
publications = await get_orcid_publications(
    orcid_id="0000-0000-0000-0000",
    max_works=20
)
# Returns: Complete publication list with DOIs
```

## 📊 Data Structure

### Author Profile
```json
{
  "id": "https://openalex.org/A5090973432",
  "display_name": "Cayman Seagraves",
  "orcid": "https://orcid.org/0000-0002-6124-7440",
  "current_affiliations": ["University of Tulsa"],
  "cited_by_count": 7,
  "works_count": 10,
  "h_index": 2,
  "research_fields": ["Economics", "Finance"]
}
```

### Work/Paper
```json
{
  "id": "https://openalex.org/W4411935046",
  "title": "Optimizing Real Estate Portfolios...",
  "doi": "10.1080/10835547.2025.2513145",
  "publication_year": 2025,
  "cited_by_count": 0,
  "journal_name": "Journal of Real Estate Portfolio Management",
  "is_open_access": false,
  "primary_field": "Housing Market and Economics",
  "abstract": "Full paper abstract (when include_abstract=true)"
}
```

## 🎯 Best Practices

### 1. Start with Autocomplete
```python
# Always start here for author disambiguation
candidates = await autocomplete_authors("Author Name")
```

### 2. Use ORCID for Precision
```python
# ORCID provides most accurate identity resolution
publications = await get_orcid_publications("0000-0000-0000-0000")
```

### 3. Filter Strategically
```python
# Focus on high-impact work
works = await retrieve_author_works(
    author_id=author_id,
    type="journal-article",
    order_by="citations",
    min_citations=5
)
```

### 4. Combine Sources
```python
# Academic + Medical research
openalex_papers = await search_works("cancer immunotherapy")
pubmed_results = await search_pubmed("cancer immunotherapy")
```

## ⚡ Performance Tips

- **Autocomplete first**: Fastest way to disambiguate authors
- **Limit results**: Use `limit` parameter to control response size
- **Filter by year**: Add `publication_year` for recent work
- **ORCID preferred**: Most reliable for individual researchers
- **Batch operations**: Process multiple authors efficiently

## 🔧 Troubleshooting

### Common Issues
- **No results**: Check spelling, try broader search terms
- **Wrong author**: Use `autocomplete_authors` for disambiguation
- **Rate limits**: Built-in respectful API usage (no action needed)
- **Email required**: Set `OPENALEX_MAILTO` environment variable

### Environment Variables
```bash
# Required
OPENALEX_MAILTO=your-email@domain.com

# Optional
OPENALEX_MAX_AUTHORS=100
OPENALEX_USER_AGENT=research-agent-v1.0
```

## 📈 Use Cases

### Academic Research
- Author disambiguation and career tracking
- Citation analysis and impact assessment
- Research field identification
- Collaboration network analysis

### Medical Research
- PubMed literature reviews
- Author institutional analysis
- Medical publication tracking

### Researcher Profiling
- ORCID identity verification
- Publication completeness checking
- Cross-platform research aggregation

---

**Status**: ✅ All 8 tools tested and operational
**Performance**: <500ms response times
**Data Sources**: OpenAlex, PubMed, ORCID
**Compatibility**: Cursor AI, Claude Desktop, OpenAI Agents
