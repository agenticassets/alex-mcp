# OpenAlex Author Disambiguation MCP Server - Examples

This directory contains comprehensive examples and tests demonstrating the capabilities of the OpenAlex Author Disambiguation MCP Server.

## 🎯 **MCP Server Tools Overview**

Our MCP server provides **6 professional tools** for author disambiguation and institution resolution:

### **1. `disambiguate_author_openalex`** - Main Disambiguation Tool
**Purpose**: Primary author disambiguation with comprehensive analysis and multiple candidate support.

**Parameters**:
- `name` (required): Author name (full name or surname)
- `affiliation` (optional): Institution name or affiliation
- `research_field` (optional): Research field, topic, or area of study
- `orcid` (optional): ORCID identifier for highest confidence matching
- `max_candidates` (optional): Number of candidates to return (default: 5, max: 25)
- `include_detailed_analysis` (optional): Include career analysis and recent works (default: true)

**Returns**: Ranked candidates with confidence scores, match reasoning, and detailed career analysis.

### **2. `search_authors_openalex`** - Advanced Search
**Purpose**: Advanced author search with multiple filters and detailed results.

**Parameters**:
- `name` (required): Author name to search for
- `affiliation` (optional): Filter by institution or affiliation
- `research_field` (optional): Filter by research field or topic
- `orcid` (optional): Search by ORCID identifier
- `limit` (optional): Maximum results (default: 10, max: 25)
- `include_works_sample` (optional): Include recent works analysis (default: true)

**Returns**: List of matching author profiles with comprehensive metadata.

### **3. `get_author_by_openalex_id`** - Profile Retrieval
**Purpose**: Get detailed author information by OpenAlex ID.

**Parameters**:
- `openalex_id` (required): OpenAlex author ID (e.g., 'A5023888391' or full URL)
- `include_works_sample` (optional): Include recent works analysis (default: true)

**Returns**: Complete author profile with career metrics and publication analysis.

### **4. `autocomplete_authors_openalex`** - Type-ahead Search
**Purpose**: Fast autocomplete search for authors - useful for type-ahead functionality.

**Parameters**:
- `query` (required): Partial author name for autocomplete
- `limit` (optional): Maximum suggestions (default: 10, max: 25)

**Returns**: Quick author suggestions for interactive applications.

### **5. `resolve_institution_openalex`** - Institution Resolution ✨
**Purpose**: Resolve institution name or abbreviation to full OpenAlex institution data.

**Parameters**:
- `institution_query` (required): Institution name, abbreviation, or partial name (e.g., 'EMBO', 'MIT', 'Max Planck')

**Returns**: Best matching institution with confidence score and metadata.

**Examples**:
- `MIT` → Massachusetts Institute of Technology
- `Stanford` → Stanford University
- `Max Planck` → Max Planck Society

### **6. `resolve_multiple_institutions_openalex`** - Batch Institution Resolution ✨
**Purpose**: Resolve multiple institution names or abbreviations efficiently in batch.

**Parameters**:
- `institution_queries` (required): Array of institution names/abbreviations to resolve

**Returns**: Dictionary mapping each query to resolved institution data.

## 📁 **Example Files**

### **Core Disambiguation Tests**
- **`test_fiona_watt_disambiguation.py`** - Focused test for Fiona Watt name variations
- **`test_comprehensive_disambiguation.py`** - Multi-author test (Fiona Watt + Jorge Abreu Vicente)
- **`test_enhanced_jorge_disambiguation.py`** - Advanced institutional context disambiguation

### **Institution Resolution Tests**
- **`test_institution_resolution.py`** - Professional institution abbreviation expansion
- **`test_professional_disambiguation_system.py`** - Complete professional workflow demonstration

### **General Tests**
- **`test_openalex_server.py`** - General server functionality tests

### **Legacy Examples**
- **`simple_fiona_example.py`** - Simple standalone example
- **`*.json`** - Historical test results

## 🚀 **Running Examples**

### **Prerequisites**
```bash
# Install dependencies
python3.10 -m pip install -r ../requirements.txt
```

### **Individual Tests**
```bash
# Test Fiona Watt disambiguation
python3.10 test_fiona_watt_disambiguation.py

# Test institution resolution
python3.10 test_institution_resolution.py

# Test complete professional system
python3.10 test_professional_disambiguation_system.py

# Test enhanced Jorge disambiguation
python3.10 test_enhanced_jorge_disambiguation.py

# Test comprehensive multi-author
python3.10 test_comprehensive_disambiguation.py

# Test general server functionality
python3.10 test_openalex_server.py
```

### **Run All Examples**
```bash
# Run all tests in sequence
for test in test_*.py; do
    echo "Running $test..."
    python3.10 "$test"
    echo "---"
done
```

## 🎯 **Key Features Demonstrated**

### **✅ Advanced Disambiguation**
- ML-powered OpenAlex disambiguation engine
- Multi-factor confidence scoring
- ORCID integration for highest accuracy
- Research field context matching
- Alternative name recognition

### **🏛️ Institution Resolution**
- Automatic abbreviation expansion
- Intelligent partial name matching
- Batch processing for efficiency
- Confidence scoring for institution matches
- Alternative name and alias recognition

### **🤖 AI Agent Optimization**
- Multiple candidate returns with ranking
- Detailed confidence reasoning
- Structured decision factors
- Career stage analysis
- Authorship pattern analysis

### **📊 Professional Metadata**
- Comprehensive career metrics
- Publication and citation analysis
- Research topic extraction
- Institutional history tracking
- Recent works sampling

### **🔧 Technical Excellence**
- Full MCP protocol compliance
- Rate limiting and error handling
- Structured JSON responses
- Comprehensive logging
- Async/await optimization

## 💡 **Use Cases**

### **Perfect For**:
- Academic research and bibliometrics
- AI agents requiring author identification
- Research collaboration platforms
- Publication management systems
- Grant and funding applications
- Academic social networks
- Research impact analysis

### **Example Scenarios**:
1. **Disambiguating "J. Smith"** with institutional context
2. **Expanding "MIT"** to "Massachusetts Institute of Technology"
3. **Finding all works by a specific researcher**
4. **Validating author identity with ORCID**
5. **Analyzing career progression and seniority**
6. **Batch processing multiple author queries**

## 🔍 **Test Results Summary**

### **Fiona Watt (EMBO Director)**
- ✅ **Perfect disambiguation** across all name variations
- ✅ **ORCID integration** working flawlessly
- ✅ **Institution matching** (European Molecular Biology Organization)
- ✅ **Career analysis** (Senior Researcher, 60% last-author papers)

### **Jorge Abreu Vicente (Astrophysicist)**
- ✅ **Excellent disambiguation** for full names
- ✅ **Institutional context** helps with ambiguous cases
- ✅ **Multi-candidate analysis** for AI decision-making
- ✅ **Research field matching** (astrophysics, molecular clouds)

### **Institution Resolution**
- ✅ **Common universities** (MIT, Stanford, Harvard, Oxford, Cambridge)
- ✅ **Research organizations** (Max Planck Society)
- ✅ **Specialized institutes** (Instituto de Astrofísica de Canarias)
- ⚠️ **Highly specialized abbreviations** may require manual expansion

## 📚 **Documentation**

For complete API documentation and usage instructions, see:
- **`../README.md`** - Main project documentation
- **`../openalex_author_disambiguation.py`** - Source code with detailed docstrings
- **`../IMPLEMENTATION_SUMMARY.md`** - Technical implementation details

## 🤝 **Contributing**

To add new examples:
1. Create a new test file following the naming pattern `test_*.py`
2. Include comprehensive documentation and comments
3. Add the new test to this README
4. Ensure the test demonstrates specific features or use cases

---

**Note**: All examples use the OpenAlex.org API which provides excellent built-in author disambiguation using machine learning models. The examples demonstrate both the capabilities and limitations of real-world author disambiguation systems.
