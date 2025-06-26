<div align="center">
  <img src="img/oam_logo_rectangular.png" alt="OpenAlex MCP Server" width="600"/>
  
  # OpenAlex Author Disambiguation MCP Server

  [![MCP](https://img.shields.io/badge/Model%20Context%20Protocol-Compatible-blue)](https://modelcontextprotocol.io/)
  [![Python](https://img.shields.io/badge/Python-3.10+-green)](https://python.org)
  [![OpenAlex](https://img.shields.io/badge/OpenAlex-API-orange)](https://openalex.org)
  [![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
  [![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-brightgreen)](https://your-docs-or-marketplace-link)
</div>

A professional Model Context Protocol (MCP) server for author disambiguation and institution resolution using the OpenAlex.org API. Built following MCP best practices with FastMCP for clean, maintainable code.

---

## 🎯 Features

### 🔍 Core Capabilities
- **ML-Powered Author Disambiguation**: Leverage OpenAlex's advanced machine learning models.
- **Institution Resolution**: Automatic abbreviation expansion (e.g., MIT → Massachusetts Institute of Technology).
- **ORCID Integration**: Highest accuracy matching with ORCID identifiers.
- **Confidence Scoring**: Detailed confidence analysis with match reasoning.
- **Career Analysis**: Automatic career stage determination and metrics.

### 🤖 Agent Optimized
- **Multiple Candidates**: Return ranked candidates for automated decision-making.
- **Rich Metadata**: Comprehensive author profiles with metrics and affiliations.
- **Structured Responses**: Clean, parseable output for automated systems.
- **Error Handling**: Graceful error handling with informative messages.

### 🏛️ Professional Grade
- **MCP Best Practices**: Built with FastMCP following official guidelines.
- **Tool Annotations**: Proper MCP tool annotations for optimal client integration.
- **Resource Management**: Efficient HTTP client management and cleanup.
- **Rate Limiting**: Respectful API usage with proper delays.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- MCP-compatible client (e.g., Claude Desktop)

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

---

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


---

## 🤖 Using with OpenAI Agents

You can load this MCP server in your OpenAI agent workflow using the [`agents.mcp.MCPServerStdio`](https://github.com/openai/openai-agents) interface. This allows you to launch and interact with the server programmatically.

### Example: Loading with `MCPServerStdio`

```python
from agents.mcp import MCPServerStdio

async with MCPServerStdio(
    name="OpenAlex MCP For Author disambiguation and works",
    cache_tools_list=True,
    params={
        "command": "uvx",
        "args": [
            "--from", "git+https://github.com/drAbreu/alex-mcp.git@4.0.0",
            "alex-mcp"
        ],
        "env": {
            "OPENALEX_MAILTO": "you@email.com"
        }  # Set your OpenAlex API email here!
    },
    client_session_timeout_seconds=10
) as alex_mcp:
    await alex_mcp.connect()
    # Now you can call tools via alex_mcp

```

> **Note:**  
> The `OPENALEX_MAILTO` environment variable is required for OpenAlex API access.  
> Replace with your own email address.

---

### Example: Loading Directly with `uvx`

You can also launch the MCP server directly using [`uvx`](https://github.com/openai/uvx):

```bash
uvx --from git+https://github.com/drAbreu/alex-mcp.git@4.0.0 alex-mcp
```

You can pass environment variables as needed:

```bash
OPENALEX_MAILTO=you@email.com uvx --from git+https://github.com/drAbreu/alex-mcp.git@4.0.0 alex-mcp
```


---

## 🛠️ Available Tools

### 1. **disambiguate_author**
Disambiguate an author using OpenAlex's ML-powered system.

**Parameters:**
- `name` (required): Author name
- `affiliation` (optional): Institution name for improved accuracy
- `research_field` (optional): Research field or topic
- `orcid` (optional): ORCID identifier for highest confidence
- `max_candidates` (optional): Maximum candidates to return (1-25, default: 5)

**Returns:**  
A ranked list of candidate authors with confidence scores and detailed metadata.

---

### 2. **search_authors**
Search for authors with advanced filtering.

**Parameters:**
- `name` (required): Author name to search
- `affiliation` (optional): Filter by institution
- `research_field` (optional): Filter by research field
- `limit` (optional): Maximum results (1-25, default: 10)

**Returns:**  
A list of authors matching the query, including OpenAlex IDs, affiliations, and metrics.

---

### 3. **get_author_profile**
Get detailed author profile by OpenAlex ID, including recent articles.

**Parameters:**
- `openalex_id` (required): OpenAlex author ID
- `max_works` (optional): Maximum number of recent articles to include (default: 10)

**Returns:**  
A detailed author profile with works, metrics, and affiliations.

---

### 4. **resolve_institution**
Resolve institution names and abbreviations.

**Parameters:**
- `institution_query` (required): Institution name or abbreviation

**Returns:**  
The resolved institution name, OpenAlex ID, and related metadata.

---

## 🧪 Example Usage

### Disambiguate an Author

```python
from src.alex_mcp.server import search_authors_core

results = search_authors_core(
    "J Abreu Vicente",
    institution=None,
    topic="Astronomy and Astrophysics",
    country_code=None,
    limit=20
)
print(results)
```

### Retrieve Author Works

```python
from src.alex_mcp.server import retrieve_author_works_core

works = retrieve_author_works_core(
    author_id="https://openalex.org/A5058921480",
    limit=20
)
print(works)
```

---

## 🧑‍💻 Development & Testing

- All source code is in `src/alex_mcp/`.
- Example notebooks and test scripts are in the `examples/` directory.
- To run tests:
  ```bash
  pytest examples/
  ```

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## 🌐 Links

- [OpenAlex API Documentation](https://docs.openalex.org/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastMCP](https://github.com/ContextualAI/fastmcp)
