<div align="center">
  <img src="img/oam_logo_rectangular.png" alt="OpenAlex MCP Server" width="600"/>
  
  # OpenAlex Author Disambiguation MCP Server

  [![MCP](https://img.shields.io/badge/Model%20Context%20Protocol-Compatible-blue)](https://modelcontextprotocol.io/)
  [![Python](https://img.shields.io/badge/Python-3.10+-green)](https://python.org)
  [![OpenAlex](https://img.shields.io/badge/OpenAlex-API-orange)](https://openalex.org)
  [![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
</div>

A professional Model Context Protocol (MCP) server for author disambiguation and institution resolution using the OpenAlex.org API. Built following MCP best practices with FastMCP for clean, maintainable code.

## 🎯 Features

### 🔍 **Core Capabilities**
- **ML-Powered Author Disambiguation** - Leverage OpenAlex's advanced machine learning models
- **Institution Resolution** - Automatic abbreviation expansion (MIT → Massachusetts Institute of Technology)
- **ORCID Integration** - Highest accuracy matching with ORCID identifiers
- **Confidence Scoring** - Detailed confidence analysis with match reasoning
- **Career Analysis** - Automatic career stage determination and metrics

### 🤖 **Agent Optimized**
- **Multiple Candidates** - Return ranked candidates for automated decision-making
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

For detailed installation instructions, see [INSTALL.md](INSTALL.md).

1. **Clone the repository:**
   ```bash
   git clone https://github.com/drAbreu/alex-mcp.git
   cd alex-mcp
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install the package:**
   ```bash
   pip install -e .
   ```

4. **Run the server:**
   ```bash
   ./run_alex_mcp.sh
   ```

## ⚙️ MCP Configuration

### Claude Desktop Configuration

Add to your Claude Desktop configuration file:

```json
{
  "mcpServers": {
    "alex-mcp": {
      "command": "/path/to/alex-mcp/run_alex_mcp.sh"
    }
  }
}
```

Replace `/path/to/alex-mcp` with the actual path to the repository on your system.

## 🛠️ Available Tools

### 🔍 **Author Disambiguation & Search**

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
Get detailed author profile by OpenAlex ID, including recent articles.

**Parameters:**
- `openalex_id` (required): OpenAlex author ID
- `max_works` (optional): Maximum number of recent articles to include (default: 10)

#### 4. **resolve_institution**
Resolve institution names and abbreviations.

**Parameters:**
- `institution_query` (required): Institution name or abbreviation

**Examples:**
- `MIT` → `Massachusetts Institute of Technology`
- `Stanford` → `Stanford University`
- `Max Planck` → `Max Planck Society`

#### 5. **author_autocomplete**
Get autocomplete suggestions for author names.

**Parameters:**
- `query` (required): Partial author name to autocomplete
- `limit` (optional): Maximum suggestions (1-25, default: 10)

### 📚 **Research Intelligence & Discovery**

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

#### 9. **analyze_topics**
Analyze text to determine research topics, keywords, and concepts using machine learning.

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
- **Error Handling** - MCP-compliant error responses
- **Resource Management** - Proper startup/shutdown lifecycle management

### Code Structure
```
src/alex_mcp/           # Main package directory
├── __init__.py        # Package initialization
└── server.py          # MCP server implementation
run_server.py           # Script to run the server
run_alex_mcp.sh         # Shell script to run the server in the virtual environment
requirements.txt        # Dependencies
INSTALL.md              # Installation instructions
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [OpenAlex](https://openalex.org) for providing the comprehensive academic database
- [Model Context Protocol](https://modelcontextprotocol.io) for the excellent framework
- [FastMCP](https://github.com/modelcontextprotocol/python-sdk) for the clean Python implementation

---

**Built with ❤️ for the research community**
