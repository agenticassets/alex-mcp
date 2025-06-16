# OpenAlex Author Disambiguation MCP Server

[![MCP](https://img.shields.io/badge/Model%20Context%20Protocol-Compatible-blue)](https://modelcontextprotocol.io/)
[![Python](https://img.shields.io/badge/Python-3.10+-green)](https://python.org)
[![OpenAlex](https://img.shields.io/badge/OpenAlex-API-orange)](https://openalex.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

A professional Model Context Protocol (MCP) server for author disambiguation and institution resolution using the OpenAlex.org API. Built following MCP best practices with FastMCP for clean, maintainable code.

## 🎯 Features

### 🔍 **Core Capabilities**
- **ML-Powered Author Disambiguation** - Leverage OpenAlex's advanced machine learning models
- **Institution Resolution** - Automatic abbreviation expansion (MIT → Massachusetts Institute of Technology)
- **ORCID Integration** - Highest accuracy matching with ORCID identifiers
- **Confidence Scoring** - Detailed confidence analysis with match reasoning
- **Career Analysis** - Automatic career stage determination and metrics

### 🤖 **AI Agent Optimized**
- **Multiple Candidates** - Return ranked candidates for AI decision-making
- **Rich Metadata** - Comprehensive author profiles with metrics and affiliations
- **Structured Responses** - Clean, parseable output for automated systems
- **Error Handling** - Graceful error handling with informative messages

### 🏛️ **Professional Grade**
- **MCP Best Practices** - Built with FastMCP following official guidelines
- **Tool Annotations** - Proper MCP tool annotations for optimal client integration
- **Resource Management** - Efficient HTTP client management and cleanup
- **Rate Limiting** - Respectful API usage with proper delays

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- MCP-compatible client (like Claude Desktop)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/openalex-author-disambiguation-mcp.git
   cd openalex-author-disambiguation-mcp
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Test the server:**
   ```bash
   python server.py
   ```

### Configuration for Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "openalex-author-disambiguation": {
      "command": "python",
      "args": ["/absolute/path/to/server.py"]
    }
  }
}
```

## 🛠️ Available Tools (10 Professional Tools)

### 🔍 **Author Disambiguation & Search (5 Tools)**

#### 1. **disambiguate_author**
Disambiguate an author using OpenAlex's ML-powered system.

**Parameters:**
- `name` (required): Author name
- `affiliation` (optional): Institution name for improved accuracy
- `research_field` (optional): Research field or topic
- `orcid` (optional): ORCID identifier for highest confidence
- `max_candidates` (optional): Maximum candidates to return (1-25, default: 5)

#### 2. **search_authors**
Search for authors with advanced filtering.

**Parameters:**
- `name` (required): Author name to search
- `affiliation` (optional): Filter by institution
- `research_field` (optional): Filter by research field
- `limit` (optional): Maximum results (1-25, default: 10)

#### 3. **get_author_profile**
Get detailed author profile by OpenAlex ID.

**Parameters:**
- `openalex_id` (required): OpenAlex author ID

#### 4. **resolve_institution**
Resolve institution names and abbreviations.

**Parameters:**
- `institution_query` (required): Institution name or abbreviation

**Examples:**
- `MIT` → `Massachusetts Institute of Technology`
- `Stanford` → `Stanford University`
- `Max Planck` → `Max Planck Society`

#### 5. **autocomplete_authors**
Fast autocomplete search for interactive applications.

**Parameters:**
- `query` (required): Partial author name
- `limit` (optional): Maximum suggestions (1-25, default: 10)

### 📚 **Research Intelligence & Discovery (5 New Tools)**

#### 6. **search_works**
Search for scholarly works (publications) with advanced filtering.

**Parameters:**
- `query` (required): Search query for title, abstract, or content
- `author_name` (optional): Filter by author name
- `publication_year` (optional): Filter by year (e.g., "2023" or "2020-2023")
- `source_type` (optional): Filter by type ("journal-article", "book", "dataset", etc.)
- `topic` (optional): Filter by research topic or field
- `sort_by` (optional): Sort order ("relevance", "cited_by_count", "publication_date")
- `limit` (optional): Maximum results (1-100, default: 20)

#### 7. **get_work_details**
Get comprehensive details about a specific scholarly work.

**Parameters:**
- `work_id` (required): OpenAlex work ID (e.g., 'W2741809807' or full URL)

#### 8. **search_topics**
Search and explore research topics with detailed information.

**Parameters:**
- `query` (required): Topic name or description to search for
- `level` (optional): Topic hierarchy level (0-5, where 0 is most general)
- `limit` (optional): Maximum topics to return (1-50, default: 20)

#### 9. **analyze_text_aboutness**
Analyze text to determine research topics, keywords, and concepts using AI.

**Parameters:**
- `title` (required): Title of the text to analyze
- `abstract` (optional): Abstract or description text (improves accuracy)

#### 10. **search_sources**
Search for publication sources (journals, conferences, repositories).

**Parameters:**
- `query` (required): Source name or description to search for
- `source_type` (optional): Filter by type ("journal", "conference", "repository", "book")
- `subject_area` (optional): Filter by subject area or field
- `limit` (optional): Maximum sources to return (1-50, default: 20)

## 📊 Example Usage

### Author Disambiguation
```python
# Find the correct "Fiona Watt" among multiple researchers
result = await disambiguate_author(
    name="Fiona Watt",
    affiliation="EMBO",
    research_field="stem cell biology"
)
```

**Output:**
```
Found 1 candidate(s) for 'Fiona Watt':

1. Fiona M. Watt
   OpenAlex ID: https://openalex.org/A5068471552
   Confidence: 1.00
   Match reasons: Exact name match, ORCID verified, Affiliation match
   ORCID: https://orcid.org/0000-0001-9151-5154
   Institutions: European Molecular Biology Organization
   Career: Senior Researcher
   Works: 707, Citations: 55,953
   H-index: 126
   Topics: Biology, Genetics, Cell biology
```

### Institution Resolution
```python
# Expand abbreviations automatically
result = await resolve_institution("MIT")
```

**Output:**
```
Institution Resolution for 'MIT':

Best Match: Massachusetts Institute of Technology
OpenAlex ID: https://openalex.org/I63966007
Match Score: 95/100
Country: US
Type: education
Homepage: https://web.mit.edu/
```

## 🏗️ Architecture

### MCP Best Practices
- **FastMCP Framework** - Uses the official FastMCP framework for clean, maintainable code
- **Tool Annotations** - Proper MCP annotations (`readOnlyHint`, `openWorldHint`)
- **Error Handling** - MCP-compliant error responses with `isError` flag
- **Resource Management** - Proper startup/shutdown lifecycle management

### Code Structure
```
server.py                 # Main MCP server with FastMCP
requirements.txt          # Clean, minimal dependencies
examples/                 # Comprehensive test suite
├── test_*.py            # Individual tool tests
└── README.md            # Example documentation
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
cd examples
python test_fiona_watt_disambiguation.py
python test_institution_resolution.py
```

## 🔧 Development

### Adding New Tools

Following MCP best practices with FastMCP:

```python
@mcp.tool(
    annotations={
        "title": "Your Tool Title",
        "readOnlyHint": True,  # If tool doesn't modify state
        "openWorldHint": True  # If tool accesses external APIs
    }
)
async def your_tool(param1: str, param2: int = 10) -> str:
    """
    Tool description for the LLM.
    
    Args:
        param1: Description of required parameter
        param2: Description of optional parameter with default
    """
    # Implementation
    return "Result"
```

### Error Handling

Follow MCP error handling patterns:

```python
try:
    # Tool logic
    return "Success result"
except Exception as e:
    logger.error(f"Error in tool: {e}")
    return f"Error: {str(e)}"
```

## 📚 OpenAlex Integration

### API Features Used
- **Author Search** - Advanced search with filters
- **Author Profiles** - Comprehensive author data
- **Institution Search** - Institution resolution and metadata
- **Autocomplete** - Fast type-ahead suggestions

### Rate Limiting
- Respectful API usage with built-in delays
- Efficient HTTP client with connection pooling
- Proper resource cleanup on shutdown

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Follow MCP best practices
4. Add comprehensive tests
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [OpenAlex](https://openalex.org) for providing the comprehensive academic database
- [Model Context Protocol](https://modelcontextprotocol.io) for the excellent framework
- [FastMCP](https://github.com/modelcontextprotocol/python-sdk) for the clean Python implementation

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/openalex-author-disambiguation-mcp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/openalex-author-disambiguation-mcp/discussions)
- **MCP Documentation**: [Model Context Protocol](https://modelcontextprotocol.io)

---

**Built with ❤️ for the research community**
