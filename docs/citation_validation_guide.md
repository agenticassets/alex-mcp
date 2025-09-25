# Citation Validation Guide: OpenAlex MCP Best Practices

## Core Problem
Citation validation requires efficient work identification plus content verification. Searching without abstracts first limits scope assessment capabilities.

## Optimal Two-Step Workflow

### Step 1: Discovery (No Abstracts)
```python
# Find work efficiently - limit to 1 result for precision
search_works(query="Author Year key terms", limit=1)
```
**Why?** Author + year + keywords reliably identifies correct works with minimal API overhead.

### Step 2: Validation (With Abstracts)
```python
# Get full details for content verification
get_work_by_id(work_id="W123456789", include_abstract=true)
```
**Why?** Direct paper retrieval with abstracts enables precise scope alignment and overstatement detection.
**Note:** Use `get_work_by_id` tool specifically, NOT `get_orcid_publications`.

## Key Insights from Validation Experience

### Coverage Reality
- **Recent articles (2020+)**: 87% have abstracts, good metadata coverage
- **Older articles (2009)**: Title/author verification possible, abstracts often unavailable
- **Books/monographs**: Poor coverage, rarely have abstracts (KellyXiu2023, DiPasqualeWheaton1996)

### Search Strategy Effectiveness
```text
Most Effective: Author + year + keywords → get OpenAlex ID → retrieve with abstracts
Very Effective: Direct ID retrieval when OpenAlex work ID known
Moderately Effective: Title + author + year for precision
Ineffective: DOI searches, vague queries, full titles alone
```

### Validation Checklist
- [ ] **Metadata Match**: Title/author/year align with bibliography?
- [ ] **Abstract Alignment**: Does abstract support specific cited claim?
- [ ] **Scope Appropriateness**: No overstatement or inappropriate extrapolation?
- [ ] **Methodological Fit**: Citation matches source's actual methods/contribution?

## Essential Best Practices

**Search Optimization**:
- Prioritize author + year combinations for reliable identification
- Use 2-3 key terms from title rather than full titles
- Limit initial searches to 1 result for precision (increase if having difficulty finding paper)

**Abstract Handling**:
- Always retrieve abstracts for content validation when available
- Note when abstracts unavailable (common for older papers)
- Books require manual verification

**Quality Assurance**:
- Cross-reference all findings against bibliography entries
- Document validation confidence levels (High/Medium/Low)
- Flag indexing gaps for manual follow-up

## Success Metrics
- **Coverage**: 85%+ of journal articles findable via author+year searches
- **Abstract Access**: 60%+ of located works have abstracts for validation
- **Metadata Accuracy**: 95%+ title/author matches when works are found
