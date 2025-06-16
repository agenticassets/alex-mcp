# OpenAlex Author Disambiguation MCP Server - Tools Reference

## 🎯 **Complete MCP Tools Overview**

Our OpenAlex Author Disambiguation MCP Server provides **6 professional tools** for comprehensive author disambiguation and institution resolution.

---

## 🔍 **Core Disambiguation Tools**

### **1. `disambiguate_author_openalex`**
**🎯 Primary author disambiguation with AI-optimized multi-candidate support**

**Purpose**: Main disambiguation tool that leverages OpenAlex's ML-powered disambiguation engine to identify authors with high confidence and detailed analysis.

**Input Parameters**:
```json
{
  "name": "string (required)",              // Author name (full name or surname)
  "affiliation": "string (optional)",       // Institution name or affiliation
  "research_field": "string (optional)",    // Research field, topic, or area of study
  "orcid": "string (optional)",            // ORCID identifier for highest confidence
  "max_candidates": "integer (optional)",   // Number of candidates (default: 5, max: 25)
  "include_detailed_analysis": "boolean (optional)" // Include career analysis (default: true)
}
```

**Returns**: 
- Ranked candidates with confidence scores
- Detailed match reasoning
- Career stage analysis
- Publication metrics and authorship patterns
- Research topics and institutional history

**Example Use Cases**:
- Disambiguating "J. Smith" with institutional context
- Finding the correct "Maria Garcia" in computer science
- Validating author identity for publication systems

---

### **2. `search_authors_openalex`**
**🔍 Advanced author search with multiple filters**

**Purpose**: Comprehensive author search with filtering capabilities for research applications.

**Input Parameters**:
```json
{
  "name": "string (required)",              // Author name to search for
  "affiliation": "string (optional)",       // Filter by institution
  "research_field": "string (optional)",    // Filter by research field
  "orcid": "string (optional)",            // Search by ORCID identifier
  "limit": "integer (optional)",           // Maximum results (default: 10, max: 25)
  "include_works_sample": "boolean (optional)" // Include recent works (default: true)
}
```

**Returns**: List of matching author profiles with comprehensive metadata

**Example Use Cases**:
- Finding all "John Wilson" researchers in physics
- Searching for authors at specific institutions
- Building author directories for research platforms

---

### **3. `get_author_by_openalex_id`**
**📋 Detailed profile retrieval by OpenAlex ID**

**Purpose**: Get complete author information when you have the OpenAlex identifier.

**Input Parameters**:
```json
{
  "openalex_id": "string (required)",       // OpenAlex ID (e.g., 'A5023888391')
  "include_works_sample": "boolean (optional)" // Include recent works (default: true)
}
```

**Returns**: Complete author profile with career metrics and publication analysis

**Example Use Cases**:
- Retrieving full profile for known OpenAlex ID
- Getting updated metrics for existing author records
- Building detailed researcher profiles

---

### **4. `autocomplete_authors_openalex`**
**⚡ Fast type-ahead search for interactive applications**

**Purpose**: Quick autocomplete functionality for user interfaces and interactive systems.

**Input Parameters**:
```json
{
  "query": "string (required)",             // Partial author name
  "limit": "integer (optional)"            // Maximum suggestions (default: 10, max: 25)
}
```

**Returns**: Quick author suggestions for interactive applications

**Example Use Cases**:
- Type-ahead search in web applications
- Author selection interfaces
- Quick name validation systems

---

## 🏛️ **Institution Resolution Tools**

### **5. `resolve_institution_openalex`** ✨
**🏛️ Professional institution name resolution and abbreviation expansion**

**Purpose**: Automatically resolve institution abbreviations and partial names to full OpenAlex institution data.

**Input Parameters**:
```json
{
  "institution_query": "string (required)"  // Institution name, abbreviation, or partial name
}
```

**Returns**: 
- Best matching institution with confidence score
- Full institution name and metadata
- Country, type, and homepage information
- Alternative names and aliases

**Example Transformations**:
- `MIT` → `Massachusetts Institute of Technology`
- `Stanford` → `Stanford University`
- `Max Planck` → `Max Planck Society`
- `EMBO` → `European Molecular Biology Organization` (when available)

**Example Use Cases**:
- Expanding abbreviations in author affiliations
- Standardizing institution names across systems
- Validating institutional affiliations

---

### **6. `resolve_multiple_institutions_openalex`** ✨
**🏛️ Efficient batch institution resolution**

**Purpose**: Resolve multiple institution queries simultaneously for efficiency.

**Input Parameters**:
```json
{
  "institution_queries": ["string", "string", ...] // Array of institution names/abbreviations
}
```

**Returns**: Dictionary mapping each query to resolved institution data

**Example Use Cases**:
- Processing author affiliation lists
- Batch standardization of institution names
- Efficient resolution for large datasets

---

## 🎯 **Key Features Across All Tools**

### **✅ Advanced Disambiguation**
- **ML-powered engine**: Leverages OpenAlex's sophisticated machine learning models
- **Multi-factor scoring**: Combines name matching, ORCID, affiliations, and research fields
- **ORCID integration**: Highest confidence when ORCID identifiers are available
- **Alternative names**: Recognizes various name formats and aliases

### **🏛️ Institution Intelligence**
- **Automatic expansion**: Converts abbreviations to full names
- **Confidence scoring**: Provides match quality indicators
- **Batch processing**: Efficient handling of multiple queries
- **Alternative recognition**: Handles various institution name formats

### **🤖 AI Agent Optimization**
- **Multiple candidates**: Returns ranked options for AI decision-making
- **Structured reasoning**: Detailed confidence explanations
- **Career analysis**: Professional stage and seniority indicators
- **Rich metadata**: Comprehensive context for automated systems

### **📊 Professional Metadata**
- **Career metrics**: H-index, citation counts, publication patterns
- **Research topics**: Extracted from publication history
- **Institutional history**: Current and historical affiliations
- **Authorship patterns**: First/middle/last author analysis for seniority assessment

### **🔧 Technical Excellence**
- **MCP compliance**: Full compatibility with Model Context Protocol
- **Error handling**: Graceful degradation and clear error messages
- **Rate limiting**: Respectful API usage with built-in delays
- **Async optimization**: High-performance async/await implementation

---

## 💡 **Professional Use Cases**

### **Academic Research & Bibliometrics**
- Author identification for citation analysis
- Research collaboration network mapping
- Publication impact assessment
- Grant application author validation

### **AI Agents & Automation**
- Automated author disambiguation in research pipelines
- Publication management system integration
- Research database curation
- Academic social network platforms

### **Research Platforms**
- Scholar profile creation and management
- Institutional research dashboards
- Collaboration recommendation systems
- Research impact visualization

### **Data Quality & Standardization**
- Author name normalization across databases
- Institution name standardization
- Research field classification
- ORCID integration and validation

---

## 🚀 **Getting Started**

### **Installation**
```bash
# Install dependencies
python3.10 -m pip install -r requirements.txt

# Run the MCP server
python3.10 openalex_author_disambiguation.py
```

### **Basic Usage Examples**
```bash
# Test individual tools
cd examples/
python3.10 test_fiona_watt_disambiguation.py
python3.10 test_institution_resolution.py
python3.10 test_professional_disambiguation_system.py
```

### **Integration with MCP Clients**
The server is fully compatible with MCP clients like Claude Desktop. Add the server configuration to your MCP settings to access all tools through the MCP protocol.

---

## 📚 **Documentation & Examples**

- **`examples/`** - Comprehensive test suite and usage examples
- **`examples/README.md`** - Detailed examples documentation
- **`openalex_author_disambiguation.py`** - Source code with detailed docstrings
- **`IMPLEMENTATION_SUMMARY.md`** - Technical implementation details

---

**Note**: All tools leverage the OpenAlex.org API, which provides state-of-the-art author disambiguation using machine learning models trained on millions of academic publications. The system handles real-world complexity including name variations, institutional changes, and research field evolution.
