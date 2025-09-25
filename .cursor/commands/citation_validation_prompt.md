# Citation Validation Command

## Validation Workflow
Analyze citation positioning in paper narrative and evidence type (methodological, empirical, theoretical). Validate each citation using OpenAlex MCP tools following optimized protocol.

## OpenAlex MCP Protocol

**Step 1 - Discovery (No Abstracts):**
- **Priority 1**: `search_works(query="exact title from bibliography")` - Most reliable for finding exact matches
- **Priority 2**: `search_works(query="Author Year key terms")` - When title unknown or too long
- **Priority 3**: DOI-based searches if available: `search_works(query="doi:10.xxxx/xxxxx")`
- **Note**: Remove `limit=1` parameter - let tool return default results, expand only if needed (limit must be numeric if used)
- Why: Exact title searches have highest precision; author+year works for disambiguation

**Step 2 - Validation (With Abstracts):**
- Retrieve: `get_work_by_id(work_id="W123456789", include_abstract=true)`  # explicitly request abstracts
- Why: Direct paper retrieval with abstracts enables precise scope alignment and overstatement detection
- **Note**: Use `get_work_by_id` tool specifically, NOT `get_orcid_publications`

**Coverage Reality:**
- Recent articles (2020+): 87% have abstracts, good metadata
- Older articles (2009): Title/author verification possible, abstracts often missing
- Books/monographs: Poor coverage, require manual verification (KellyXiu2023, DiPasqualeWheaton1996)
- Working papers: Often not indexed until published

**Search Effectiveness (Revised):**
- ✅ **Exact title searches** → most reliable for precision matching
- ✅ Author + year + keywords → good for disambiguation when title unknown
- ✅ DOI-based searches → reliable when DOI available from bibliography
- ✅ Direct ID retrieval when OpenAlex work ID known
- ⚠️ Broad keyword searches → use only as last resort (high false positives)
- ❌ DOI searches marked as ineffective (actually work well when formatted correctly)

## Validation Standards

**Citation Integrity:**
- Metadata matches bibliography (title/author/year)?
- Appropriate positioning for contribution type?

**Scope Alignment:**
- Abstract supports specific cited claim?
- No inappropriate extrapolation beyond source findings?

**Methodological Appropriateness:**
- AI/ML citations: Work actually uses claimed methods?
- Theoretical citations: Work establishes cited principles?

**Common Issues:**
- Overstatement, scope creep, methodological misrepresentation, temporal inconsistency

## Deliverables

Document each citation with:
- **Accuracy**: Metadata verification (✓/✗) + confidence level
- **Scope**: Abstract-to-claim mapping analysis
- **Issues**: Specific problems with evidence quotes
- **Confidence**: High/Medium/Low + justification
- **Recommendations**: Corrections/clarifications needed

**Format:** Markdown with headers, abstract quotes, specific recommendations.

References: @citation_validation_guide.md @open-alex-mcp.mdc @mcp.json

## Best Practices
- Verify citation keys against bibliography first
- Group citations by type (articles vs books) for efficiency
- Flag indexing gaps for manual follow-up
- Read abstracts before scope assessment
- Conservative validation approach

# Target Citations/Section:

**IMPORTANT**: If I don't provide that target citations/section, then ask me for it.