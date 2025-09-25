# Citation Validation Guide: OpenAlex MCP Best Practices

## Core Problem
Citation validation requires efficient work identification plus content verification. The challenge is finding the right balance between search precision and content access for validation.

## Optimal Two-Step Workflow

### Step 1: Discovery (Prioritized Search Strategy)
```python
# Priority 1: Exact title search (most reliable)
search_works(query="exact title from bibliography")

# Priority 2: Author + year + keywords (when title unknown)
search_works(query="Author Year key terms")

# Priority 3: DOI-based search (when DOI available)
search_works(query="doi:10.xxxx/xxxxx")
```
**Why?** Exact title searches provide highest precision for finding exact matches. Author+year works for disambiguation. Remove limit parameters to avoid tool errors - let defaults work.

### Step 2: Validation (With Abstracts)
```python
# Get full details for content verification
get_work_by_id(work_id="W123456789", include_abstract=true)  # explicitly request abstracts
```
**Why?** Direct paper retrieval with abstracts enables precise scope alignment and overstatement detection.
**Note:** Use `get_work_by_id` tool specifically, NOT `get_orcid_publications`.

## Key Insights from Validation Experience

### Coverage Reality
- **Recent articles (2020+)**: 87% have abstracts, good metadata coverage
- **Older articles (2009)**: Title/author verification possible, abstracts often unavailable
- **Books/monographs**: Poor coverage, rarely have abstracts (KellyXiu2023, DiPasqualeWheaton1996)
- **Working papers**: Often not indexed until published - require manual verification

### Search Strategy Effectiveness (Revised)
```text
Most Effective: Exact title searches → highest precision matching
Very Effective: Author + year + keywords → good for disambiguation
Effective: DOI-based searches → reliable when DOI available from bibliography
Moderately Effective: Title + author + year → for precision when needed
Limited Use: Broad keyword searches → high false positives, use as last resort
```

### Validation Checklist
- [ ] **Metadata Match**: Title/author/year align with bibliography?
- [ ] **Abstract Alignment**: Does abstract support specific cited claim?
- [ ] **Scope Appropriateness**: No overstatement or inappropriate extrapolation?
- [ ] **Methodological Fit**: Citation matches source's actual methods/contribution?

## Essential Best Practices

**Search Optimization**:
- **Priority 1**: Start with exact title from bibliography - highest success rate for precision
- **Priority 2**: Use author + year + key terms when title search fails or title is unknown
- **Priority 3**: Try DOI searches when DOI available from bibliography
- **Fallback**: Broad keyword searches only as last resort (high false positive risk)

**Abstract Handling**:
- Always use `include_abstract=true` in `get_work_by_id` calls for validation
- Note when abstracts unavailable (common for older papers, books, working papers)
- Working papers and unpublished manuscripts require manual verification
- Books/monographs rarely have abstracts in OpenAlex

**Quality Assurance**:
- Cross-reference all findings against bibliography entries first
- Document validation confidence levels (High/Medium/Low) with justifications
- Flag indexing gaps for manual follow-up (especially working papers)
- Be conservative about scope claims - verify abstract supports specific citation

## Success Metrics (Updated)
- **Coverage**: 90%+ of published journal articles findable via title or author+year searches
- **Abstract Access**: 70%+ of located works have abstracts for validation (higher for recent papers)
- **Metadata Accuracy**: 95%+ title/author matches when works are found
- **Working Paper Gap**: ~80% of working papers not indexed until publication
