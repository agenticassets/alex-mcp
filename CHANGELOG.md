# Changelog

All notable changes to the Author Disambiguation MCP Server will be documented in this file.

## [0.1.0] - 2025-01-13

### Added
- Initial release of Author Disambiguation MCP Server
- Support for three major scientific databases:
  - Semantic Scholar API integration
  - OpenAlex API integration  
  - EuropePMC API integration
- Core MCP tools:
  - `disambiguate_author` - Main disambiguation across all databases
  - `search_semantic_scholar` - Semantic Scholar specific search
  - `search_openalex` - OpenAlex specific search
  - `search_europepmc` - EuropePMC specific search
- Author profile standardization with confidence scoring
- Seniority analysis based on authorship positions
- Concurrent API processing for faster results
- Comprehensive error handling and logging
- CLI testing tool (`cli_test.py`)
- Complete documentation and installation guides

### Features
- **Multi-database disambiguation**: Query all three databases simultaneously
- **Confidence scoring**: Intelligent ranking based on affiliation and field matching
- **Seniority analysis**: Calculate author career stage from publication patterns
- **Standardized output**: Consistent data format across all services
- **Rate limit handling**: Graceful degradation when APIs are unavailable
- **MCP integration**: Ready-to-use with Cline and Claude Desktop

### Tested
- ✅ Successfully tested with real author "Fiona Watt" and "EMBO" affiliation
- ✅ Returned 5 candidate profiles from Semantic Scholar
- ✅ Proper error handling for API rate limits and service unavailability
- ✅ JSON output generation and file export functionality

### Technical Details
- Python 3.10+ compatibility
- Async/await architecture for concurrent processing
- httpx for HTTP client operations
- Pydantic for data validation
- Comprehensive logging and error handling
- 30-second timeout protection
- MIT License

### Known Issues
- OpenAlex API may return 403 errors (service-side restriction)
- Semantic Scholar has rate limits (100 requests per 5 minutes)
- EuropePMC search is paper-based, not direct author search

### Future Roadmap
- ORCID integration
- Caching mechanism for repeated queries
- Fuzzy name matching algorithms
- Batch processing capabilities
- Author network analysis
- Enhanced seniority scoring algorithms
