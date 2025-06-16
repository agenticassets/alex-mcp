# OpenAlex Author Disambiguation MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![OpenAlex API](https://img.shields.io/badge/API-OpenAlex.org-blue.svg)](https://openalex.org/)

A specialized Model Context Protocol (MCP) server focused exclusively on **OpenAlex.org** for robust, ML-powered author disambiguation. This implementation leverages OpenAlex's advanced disambiguation algorithms that consider author names, publication patterns, citation networks, ORCID integration, and institutional affiliations.

## 🎯 Why OpenAlex-Only?

After careful analysis, we've focused exclusively on OpenAlex.org because:

- **🧠 Advanced ML Disambiguation**: OpenAlex uses sophisticated machine learning models for author disambiguation
- **🔗 ORCID Integration**: Seamless integration with ORCID for verified author identities
- **📊 Comprehensive Coverage**: Covers 200M+ works and 90M+ authors across all disciplines
- **🏛️ Institutional Data**: Rich institutional affiliation data with ROR integration
- **🆓 Open Access**: Completely free and open API with generous rate limits
- **📈 Consistent Quality**: Single data source ensures consistency and reliability

## ✨ Key Features

### 🔍 Advanced Disambiguation
- **ML-powered matching** using OpenAlex's sophisticated algorithms
- **Confidence scoring** with detailed match reasoning
- **Multiple candidate support** for agentic AI decision-making
- **ORCID integration** for highest-confidence matching

### 📊 Comprehensive Author Profiles
- **Career stage analysis** (Early Career, Mid-Career, Senior Researcher, etc.)
- **Seniority scoring** based on authorship patterns
- **Research metrics** (H-index, i10-index, citation counts)
- **Publication timeline** and career progression
- **Research topics** and concept analysis

### 🚀 Performance Features
- **Fast autocomplete** for type-ahead functionality
- **Advanced filtering** by affiliation, research field, ORCID
- **Batch processing** support for multiple queries
- **Rate limit compliance** with polite API usage

### 🤖 AI-Agent Friendly
- **N-candidate returns** for AI decision-making
- **Structured confidence scoring** for automated selection
- **Rich metadata** for context-aware disambiguation
- **Detailed match reasoning** for explainable AI

## 🛠️ Installation

### Prerequisites
- Python 3.10 or newer
- pip package manager

### Install Dependencies

```bash
# Navigate to the project directory
cd /Users/jabreu/PycharmProjects/author-disambiguation-mcp

# Install required packages
pip install -r requirements.txt

# The new OpenAlex server uses the same dependencies as the original
```

### Required Python Packages
- `mcp>=0.9.0` - Model Context Protocol SDK
- `httpx>=0.25.0` - Async HTTP client for OpenAlex API
- `pydantic>=2.0.0` - Data validation and serialization

## 🚀 Usage

### Running the OpenAlex MCP Server

```bash
# Run the new OpenAlex-focused server
python openalex_author_disambiguation.py
```

### Available Tools

#### 1. `disambiguate_author_openalex`
**Main disambiguation tool** with comprehensive analysis and multiple candidate support.

**Parameters:**
- `name` (required): Author name or surname
- `affiliation` (optional): Institution name or affiliation
- `research_field` (optional): Research field, topic, or area of study
- `orcid` (optional): ORCID identifier for precise matching
- `max_candidates` (optional): Number of candidates to return (default: 5, max: 25)
- `include_detailed_analysis` (optional): Include career analysis (default: true)

**Example:**
```json
{
  "name": "Fiona Watt",
  "affiliation": "King's College London",
  "research_field": "stem cell biology",
  "max_candidates": 3,
  "include_detailed_analysis": true
}
```

#### 2. `search_authors_openalex`
**Advanced search** with multiple filters and detailed results.

#### 3. `get_author_by_openalex_id`
**Get detailed author information** by OpenAlex ID.

#### 4. `autocomplete_authors_openalex`
**Fast autocomplete search** for type-ahead functionality.

### Enhanced Output Format

The server returns comprehensive `OpenAlexAuthorProfile` objects:

```json
{
  "openalex_id": "https://openalex.org/A5023888391",
  "display_name": "Fiona M. Watt",
  "orcid": "https://orcid.org/0000-0001-9151-5154",
  "display_name_alternatives": ["F. Watt", "Fiona Watt"],
  "last_known_institutions": [
    {
      "id": "https://openalex.org/I201448701",
      "display_name": "King's College London",
      "country_code": "GB"
    }
  ],
  "works_count": 245,
  "cited_by_count": 15420,
  "h_index": 68,
  "i10_index": 189,
  "career_stage": "Senior Researcher",
  "seniority_score": 0.82,
  "confidence_score": 0.95,
  "match_reasons": [
    "Exact name match",
    "Affiliation match: King's College London",
    "Research field match: Cell Biology",
    "ORCID verified"
  ],
  "research_topics": [
    "Cell Biology",
    "Stem Cell Research",
    "Developmental Biology"
  ],
  "authorship_positions": {
    "first": 45,
    "middle": 67,
    "last": 133
  },
  "recent_works": [
    {
      "title": "Epidermal stem cell dynamics...",
      "year": 2023,
      "author_position": 8,
      "total_authors": 8,
      "cited_by_count": 12
    }
  ]
}
```

## 🧪 Testing

### Run Comprehensive Tests

```bash
# Test the OpenAlex server with various scenarios
python test_openalex_server.py
```

The test script demonstrates:
- ✅ Basic author disambiguation
- ✅ ORCID-based precise matching
- ✅ Multiple candidate returns for AI agents
- ✅ Autocomplete functionality
- ✅ Advanced search with filters
- ✅ Career stage analysis
- ✅ Authorship pattern analysis

### Example Test Output

```
🚀 OpenAlex Author Disambiguation MCP Server - Comprehensive Test
======================================================================

🔍 Testing Basic Author Disambiguation
==================================================

📚 Test 1: Fiona Watt (stem cell biologist)
Found 3 candidates
Best match: Fiona M. Watt
Confidence: 0.95
Career stage: Senior Researcher
Works: 245, Citations: 15420
H-index: 68
Match reasons: Exact name match, Affiliation match: King's College London, Research field match: Cell Biology, ORCID verified
```

## 🔧 MCP Integration

### Adding to Cline MCP Settings

Add the OpenAlex server to your MCP configuration:

**Location:** `/Users/jabreu/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`

```json
{
  "mcpServers": {
    "openalex-author-disambiguation": {
      "command": "python",
      "args": ["/Users/jabreu/PycharmProjects/author-disambiguation-mcp/openalex_author_disambiguation.py"],
      "env": {}
    }
  }
}
```

### Adding to Claude Desktop

**Location:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "openalex-author-disambiguation": {
      "command": "python",
      "args": ["/Users/jabreu/PycharmProjects/author-disambiguation-mcp/openalex_author_disambiguation.py"],
      "env": {}
    }
  }
}
```

## 📊 Career Stage Analysis

The server provides sophisticated career stage analysis:

### Career Stages
- **Very Early Career**: < 5 publications
- **Early Career (First Author Focus)**: > 60% first author papers
- **Mid-Career (Leadership Role)**: > 40% last author papers
- **Senior Researcher**: High last-author ratio + H-index > 15
- **Established Researcher**: High seniority score (> 0.6)
- **Experienced Researcher**: > 20 publications with mixed patterns

### Seniority Scoring
- **First author papers**: Weight = 0.2 (typically junior researchers)
- **Middle author papers**: Weight = 0.5 (collaboration/contribution)
- **Last author papers**: Weight = 1.0 (typically senior/PI role)

Formula: `(first × 0.2 + middle × 0.5 + last × 1.0) / total_papers`

## 🎯 Use Cases

### For Agentic AI Systems
```python
# Get multiple candidates for AI decision-making
result = await server.disambiguate_author(
    name="John Smith",
    research_field="machine learning",
    max_candidates=5
)

# AI can analyze all candidates and select based on:
# - Confidence scores
# - Career stage appropriateness
# - Research topic alignment
# - Institutional context
```

### For Research Analysis
```python
# Analyze career progression
profile = await server.get_author_by_id("A5023888391")
print(f"Career span: {profile.career_length} years")
print(f"Evolution: {profile.career_stage}")
print(f"Leadership transition: {profile.seniority_score}")
```

### For Institution Mapping
```python
# Find authors by institution and field
authors = await server.search_authors(
    name="",  # Search all
    affiliation="Stanford University",
    research_field="artificial intelligence",
    limit=25
)
```

## 🌟 Advantages Over Multi-Database Approaches

### 1. **Consistency**
- Single data source eliminates conflicts
- Uniform data quality and structure
- Consistent disambiguation logic

### 2. **Advanced Disambiguation**
- ML-powered author matching
- Considers publication patterns and citation networks
- Integrates multiple signals (name, affiliation, ORCID, topics)

### 3. **Rich Metadata**
- Comprehensive author profiles
- Career progression analysis
- Research topic evolution
- Institutional history

### 4. **Performance**
- Single API reduces latency
- No need to merge/deduplicate results
- Consistent rate limiting

### 5. **Reliability**
- OpenAlex has 99.9% uptime
- Generous rate limits (10 requests/second)
- No authentication required

## 📈 API Rate Limits

OpenAlex provides generous rate limits:
- **10 requests per second** (no daily limit)
- **Polite usage encouraged** with User-Agent header
- **No authentication required**
- **Email contact recommended** for high-volume usage

## 🔍 Confidence Scoring

The server uses sophisticated confidence scoring:

### Base Confidence: 0.6
Higher than other databases due to OpenAlex's advanced disambiguation

### Confidence Boosts:
- **Exact name match**: +0.3
- **Partial name match**: +0.2
- **Alternative name match**: +0.1
- **ORCID verified**: +0.1
- **Affiliation match**: +0.2
- **Research field match**: +0.15
- **Active researcher** (>10 works): +0.05

### Maximum Confidence: 1.0

## 🚀 Future Enhancements

- **Caching layer** for repeated queries
- **Batch processing** for multiple authors
- **Research collaboration networks**
- **Temporal analysis** of research evolution
- **Institution ranking integration**
- **Grant funding data** (when available)

## 📚 OpenAlex Resources

- **API Documentation**: https://docs.openalex.org/
- **Author Disambiguation**: https://help.openalex.org/hc/en-us/articles/24347048891543-Author-disambiguation
- **GitHub Repository**: https://github.com/ourresearch/openalex-name-disambiguation
- **OpenAlex Website**: https://openalex.org/

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Test with `python test_openalex_server.py`
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **OpenAlex Team** for providing excellent open science infrastructure
- **Model Context Protocol** for the MCP framework
- **Research community** for open science initiatives

---

**Built with ❤️ for the research community**

*Leveraging OpenAlex.org's world-class author disambiguation for accurate, reliable, and comprehensive author identification.*
