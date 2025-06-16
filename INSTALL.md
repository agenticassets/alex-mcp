# Installation and Setup Guide

## Quick Start

1. **Install Dependencies**
   ```bash
   cd /Users/jabreu/PycharmProjects/author-disambiguation-mcp
   pip install -r requirements.txt
   ```

2. **Test the Server**
   ```bash
   python test_server.py
   ```

3. **The server is already configured in your MCP settings!**
   - Location: `/Users/jabreu/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
   - Server name: `author-disambiguation`

## Available MCP Tools

Once the server is running, you'll have access to these tools:

### 1. `disambiguate_author`
**Main tool** - Searches all databases and returns ranked results

**Usage Example:**
```json
{
  "name": "John Smith",
  "affiliation": "Stanford University", 
  "field": "Machine Learning",
  "keywords": "neural networks"
}
```

### 2. `search_semantic_scholar`
Search only Semantic Scholar database

### 3. `search_openalex` 
Search only OpenAlex database

### 4. `search_europepmc`
Search only EuropePMC database

## Testing Individual APIs

You can test each service individually:

```python
import asyncio
from main import AuthorDisambiguationServer

async def test():
    server = AuthorDisambiguationServer()
    
    # Test Semantic Scholar
    results = await server.search_semantic_scholar("Einstein", "Princeton")
    print(f"Found {len(results)} profiles")
    
    await server.http_client.aclose()

asyncio.run(test())
```

## Expected Output Format

Each author profile includes:
- **Basic Info**: name, author_id, service, affiliation
- **Metrics**: paper_count, citation_count, h_index
- **Seniority Analysis**: first/last/middle author paper counts + seniority score
- **Confidence**: matching confidence score
- **Recent Papers**: list of recent publications

## Troubleshooting

### Import Errors
If you get MCP import errors:
```bash
pip install mcp>=0.9.0
```

### Network Issues
- Check internet connection
- APIs may have rate limits:
  - Semantic Scholar: 100 requests per 5 minutes
  - OpenAlex: 10 requests per second
  - EuropePMC: No explicit limits

### Server Not Starting
1. Check Python version: `python --version` (needs 3.10+)
2. Check dependencies: `pip list | grep mcp`
3. Run test script: `python test_server.py`

## Usage in MCP Client

Once configured, you can use commands like:

```
"Search for author John Smith at Stanford University in Machine Learning"
```

The system will automatically use the `disambiguate_author` tool to:
1. Query all three databases simultaneously
2. Calculate confidence and seniority scores
3. Return ranked results with the best matches first

## API Rate Limits & Best Practices

- **Semantic Scholar**: Be respectful, max 100 requests per 5 minutes
- **OpenAlex**: Max 10 requests per second, no daily limit
- **EuropePMC**: No explicit limits, but don't abuse

The server includes automatic error handling and will continue working even if one API fails.
