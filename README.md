# OpenAlex Author Disambiguation MCP Server

A professional-grade Model Context Protocol (MCP) server for author disambiguation and institution resolution using the OpenAlex.org API.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compatible](https://img.shields.io/badge/MCP-compatible-green.svg)](https://modelcontextprotocol.io/)
[![OpenAlex API](https://img.shields.io/badge/OpenAlex-API-orange.svg)](https://openalex.org/)

## 🎯 **Overview**

This MCP server provides comprehensive author disambiguation and institution resolution capabilities using OpenAlex's advanced machine learning-powered disambiguation system. It's designed for AI agents, research platforms, and academic applications requiring accurate author identification.

### **Key Features**

- **🔍 Advanced Author Disambiguation**: ML-powered disambiguation with confidence scoring
- **🏛️ Institution Resolution**: Automatic abbreviation expansion (MIT → Massachusetts Institute of Technology)
- **🤖 AI Agent Optimized**: Multiple candidate support with detailed reasoning
- **📊 Rich Metadata**: Career analysis, publication metrics, and research topics
- **⚡ Professional Performance**: Rate limiting, error handling, and async optimization

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.10 or higher
- Internet connection for OpenAlex API access

### **Installation**
```bash
# Clone the repository
git clone https://github.com/drAbreu/alex-mcp.git
cd alex-mcp

# Install dependencies
pip install -r requirements.txt

# Test the installation
python openalex_author_disambiguation.py
```

### **Basic Usage**
```bash
# Run example tests
cd examples/
python test_fiona_watt_disambiguation.py
python test_institution_resolution.py
```

## 🎯 **MCP Tools Available**

Our server provides **6 professional tools**:

### **🔍 Core Disambiguation Tools**

1. **`disambiguate_author_openalex`** - Main disambiguation with AI-optimized multi-candidate support
2. **`search_authors_openalex`** - Advanced author search with multiple filters
3. **`get_author_by_openalex_id`** - Detailed profile retrieval by OpenAlex ID
4. **`autocomplete_authors_openalex`** - Fast type-ahead search for interactive applications

### **🏛️ Institution Resolution Tools**

5. **`resolve_institution_openalex`** - Single institution resolution and abbreviation expansion
6. **`resolve_multiple_institutions_openalex`** - Batch institution processing for efficiency

## 📊 **Test Results**

### **✅ Fiona Watt (EMBO Director) - Perfect Success**
All name variations resolve to the same author:
- `F. Watt` → Fiona M. Watt (https://openalex.org/A5068471552)
- `Fiona Watt` → Fiona M. Watt (https://openalex.org/A5068471552)
- `Fiona M. Watt` → Fiona M. Watt (https://openalex.org/A5068471552)
- `Watt FM` → Fiona M. Watt (https://openalex.org/A5068471552)

**Profile Details:**
- **ORCID**: https://orcid.org/0000-0001-9151-5154
- **Institution**: European Molecular Biology Organization (EMBO)
- **Career Stage**: Senior Researcher (60% last-author papers)
- **H-index**: 126, **Citations**: 55,953, **Works**: 707

### **✅ Institution Resolution Success**
- `Stanford` → Stanford University ✅
- `Harvard` → Harvard University ✅
- `Oxford` → University of Oxford ✅
- `Cambridge` → University of Cambridge ✅
- `Max Planck` → Max Planck Society ✅

## 💡 **Use Cases**

### **Perfect For:**
- **Academic Research**: Author identification for citation analysis
- **AI Agents**: Automated author disambiguation in research pipelines
- **Research Platforms**: Scholar profile creation and management
- **Publication Systems**: Author validation and deduplication
- **Grant Applications**: Author identity verification
- **Bibliometrics**: Research impact analysis and collaboration mapping

### **Example Scenarios:**
1. **Disambiguating "J. Smith"** with institutional context
2. **Expanding "MIT"** to "Massachusetts Institute of Technology"
3. **Finding all works by a specific researcher**
4. **Validating author identity with ORCID**
5. **Analyzing career progression and seniority**
6. **Batch processing multiple author queries**

## 🔧 **Technical Features**

### **✅ Advanced Disambiguation**
- ML-powered OpenAlex disambiguation engine
- Multi-factor confidence scoring
- ORCID integration for highest accuracy
- Research field context matching
- Alternative name recognition

### **🏛️ Institution Intelligence**
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

## 📁 **Project Structure**

```
alex-mcp/
├── openalex_author_disambiguation.py  # Main MCP server
├── requirements.txt                   # Dependencies
├── setup.py                          # Package setup
├── README.md                         # This file
├── MCP_TOOLS_REFERENCE.md            # Complete tools documentation
├── PROPOSED_ADDITIONAL_TOOLS.md      # Future expansion plans
├── IMPLEMENTATION_SUMMARY.md         # Technical details
└── examples/                         # Test suite and examples
    ├── README.md                     # Examples documentation
    ├── test_fiona_watt_disambiguation.py
    ├── test_institution_resolution.py
    ├── test_comprehensive_disambiguation.py
    ├── test_enhanced_jorge_disambiguation.py
    ├── test_professional_disambiguation_system.py
    └── test_openalex_server.py
```

## 🚀 **Running Examples**

### **Individual Tests**
```bash
cd examples/

# Test Fiona Watt disambiguation
python test_fiona_watt_disambiguation.py

# Test institution resolution
python test_institution_resolution.py

# Test complete professional system
python test_professional_disambiguation_system.py

# Test enhanced Jorge disambiguation
python test_enhanced_jorge_disambiguation.py

# Test comprehensive multi-author
python test_comprehensive_disambiguation.py

# Test general server functionality
python test_openalex_server.py
```

### **Run All Examples**
```bash
cd examples/
for test in test_*.py; do
    echo "Running $test..."
    python "$test"
    echo "---"
done
```

## 🔮 **Future Expansion**

We have identified **12 additional tools** that would transform this into a comprehensive research intelligence platform:

- **📄 Works & Publications**: Publication search, collaboration discovery, impact analysis
- **💡 Topics & Research Areas**: Trending topics, research area discovery
- **📚 Sources & Venues**: Journal analysis, conference discovery
- **💰 Funding & Publishers**: Grant opportunities, publisher analysis
- **🔍 Advanced Analytics**: Network analysis, text classification

See `PROPOSED_ADDITIONAL_TOOLS.md` for detailed expansion plans.

## 📚 **Documentation**

- **[MCP Tools Reference](MCP_TOOLS_REFERENCE.md)** - Complete API documentation
- **[Examples Documentation](examples/README.md)** - Usage examples and test results
- **[Implementation Summary](IMPLEMENTATION_SUMMARY.md)** - Technical implementation details
- **[Proposed Extensions](PROPOSED_ADDITIONAL_TOOLS.md)** - Future development roadmap

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- **[OpenAlex](https://openalex.org/)** - For providing the excellent open academic database and API
- **[Model Context Protocol](https://modelcontextprotocol.io/)** - For the MCP specification and Python SDK
- **[OurResearch](https://ourresearch.org/)** - For maintaining OpenAlex as a public good

## 📞 **Support**

- **Issues**: [GitHub Issues](https://github.com/drAbreu/alex-mcp/issues)
- **Documentation**: [Project Wiki](https://github.com/drAbreu/alex-mcp/wiki)
- **OpenAlex Support**: [OpenAlex Help](https://openalex.org/help)

---

**Built with ❤️ for the research community**

*Leveraging OpenAlex's state-of-the-art author disambiguation to power the next generation of research tools and AI agents.*
