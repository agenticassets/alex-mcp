#!/usr/bin/env python3
"""
Test script for OpenAlex Author Disambiguation MCP Server

This script demonstrates the capabilities of the new OpenAlex-focused
author disambiguation server with comprehensive examples.
"""

import asyncio
import json
from datetime import datetime
from openalex_author_disambiguation import OpenAlexAuthorDisambiguationServer

async def test_basic_disambiguation():
    """Test basic author disambiguation functionality"""
    print("🔍 Testing Basic Author Disambiguation")
import sys
import os

# Add parent directory to path to import the main module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    print("=" * 50)
    
    server = OpenAlexAuthorDisambiguationServer()
    
    # Test case 1: Well-known researcher
    print("\n📚 Test 1: Fiona Watt (stem cell biologist)")
    result = await server.disambiguate_author(
        name="Fiona Watt",
        affiliation="King's College London",
        research_field="stem cell biology",
        max_candidates=3
    )
    
    print(f"Found {result['disambiguation_summary']['candidates_returned']} candidates")
    if result['best_match']:
        best = result['best_match']
        print(f"Best match: {best['display_name']}")
        print(f"Confidence: {best['confidence_score']:.2f}")
        print(f"Career stage: {best['career_stage']}")
        print(f"Works: {best['works_count']}, Citations: {best['cited_by_count']}")
        print(f"H-index: {best['h_index']}")
        print(f"Match reasons: {', '.join(best['match_reasons'])}")
    
    return result

async def test_disambiguation_with_orcid():
    """Test disambiguation using ORCID for precise matching"""
    print("\n\n🆔 Testing ORCID-based Disambiguation")
    print("=" * 50)
    
    server = OpenAlexAuthorDisambiguationServer()
    
    # Test with a known ORCID
    print("\n📚 Test: Author with known ORCID")
    result = await server.disambiguate_author(
        name="John Smith",  # Common name
        orcid="0000-0002-1825-0097",  # Specific ORCID
        max_candidates=1
    )
    
    if result['best_match']:
        best = result['best_match']
        print(f"ORCID match: {best['display_name']}")
        print(f"ORCID: {best['orcid']}")
        print(f"Confidence: {best['confidence_score']:.2f}")
        print(f"Institution: {[inst['display_name'] for inst in best['last_known_institutions']]}")
    
    return result

async def test_multiple_candidates():
    """Test returning multiple candidates for agentic AI decision-making"""
    print("\n\n👥 Testing Multiple Candidates for AI Decision-Making")
    print("=" * 50)
    
    server = OpenAlexAuthorDisambiguationServer()
    
    # Test with a common name to get multiple candidates
    print("\n📚 Test: Common name 'David Miller' - returning top 5 candidates")
    result = await server.disambiguate_author(
        name="David Miller",
        research_field="computer science",
        max_candidates=5
    )
    
    print(f"Total candidates found: {result['disambiguation_summary']['total_candidates_found']}")
    print(f"Candidates returned: {result['disambiguation_summary']['candidates_returned']}")
    
    print("\n🏆 Top candidates for AI decision-making:")
    for i, candidate in enumerate(result['all_candidates'], 1):
        print(f"\n{i}. {candidate['display_name']}")
        print(f"   Confidence: {candidate['confidence_score']:.2f}")
        print(f"   Career stage: {candidate['career_stage']}")
        print(f"   Works: {candidate['works_count']}, H-index: {candidate['h_index']}")
        print(f"   Research topics: {', '.join(candidate['research_topics'][:3])}")
        if candidate['last_known_institutions']:
            print(f"   Institution: {candidate['last_known_institutions'][0]['display_name']}")
        print(f"   Match reasons: {', '.join(candidate['match_reasons'])}")
    
    return result

async def test_autocomplete():
    """Test autocomplete functionality"""
    print("\n\n⚡ Testing Autocomplete Functionality")
    print("=" * 50)
    
    server = OpenAlexAuthorDisambiguationServer()
    
    # Test autocomplete
    print("\n📚 Test: Autocomplete for 'Einstein'")
    suggestions = await server.autocomplete_authors("Einstein", limit=5)
    
    print(f"Found {len(suggestions)} suggestions:")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"{i}. {suggestion['display_name']}")
        print(f"   Hint: {suggestion.get('hint', 'N/A')}")
        print(f"   Works: {suggestion.get('works_count', 0)}, Citations: {suggestion.get('cited_by_count', 0)}")
    
    return suggestions

async def test_get_by_id():
    """Test getting author by OpenAlex ID"""
    print("\n\n🔗 Testing Get Author by OpenAlex ID")
    print("=" * 50)
    
    server = OpenAlexAuthorDisambiguationServer()
    
    # First get an ID from a search
    search_result = await server.search_authors("Marie Curie", limit=1)
    if search_result:
        author_id = search_result[0].openalex_id
        print(f"\n📚 Test: Getting author details for ID: {author_id}")
        
        profile = await server.get_author_by_id(author_id)
        if profile:
            print(f"Author: {profile.display_name}")
            print(f"Career span: {profile.first_publication_year} - {profile.last_publication_year}")
            print(f"Career length: {profile.career_length} years")
            print(f"Seniority score: {profile.seniority_score:.2f}")
            print(f"Career stage: {profile.career_stage}")
            print(f"Authorship pattern: First: {profile.authorship_positions['first']}, "
                  f"Middle: {profile.authorship_positions['middle']}, "
                  f"Last: {profile.authorship_positions['last']}")
            
            if profile.recent_works:
                print(f"\nRecent works sample:")
                for work in profile.recent_works[:3]:
                    print(f"  • {work['title']} ({work['year']})")
                    print(f"    Position: {work['author_position']}/{work['total_authors']}, "
                          f"Citations: {work['cited_by_count']}")
        
        return profile
    
    return None

async def test_advanced_search():
    """Test advanced search with multiple filters"""
    print("\n\n🔬 Testing Advanced Search with Multiple Filters")
    print("=" * 50)
    
    server = OpenAlexAuthorDisambiguationServer()
    
    # Test advanced search
    print("\n📚 Test: Advanced search - 'Smith' at 'Stanford' in 'machine learning'")
    profiles = await server.search_authors(
        name="Smith",
        affiliation="Stanford University",
        research_field="machine learning",
        limit=3
    )
    
    print(f"Found {len(profiles)} matching authors:")
    for i, profile in enumerate(profiles, 1):
        print(f"\n{i}. {profile.display_name}")
        print(f"   Confidence: {profile.confidence_score:.2f}")
        print(f"   Institution: {[inst['display_name'] for inst in profile.last_known_institutions]}")
        print(f"   Research areas: {', '.join(profile.research_topics[:3])}")
        print(f"   Career metrics: {profile.works_count} works, {profile.cited_by_count} citations")
    
    return profiles

async def demonstrate_career_analysis():
    """Demonstrate detailed career stage analysis"""
    print("\n\n📈 Demonstrating Career Stage Analysis")
    print("=" * 50)
    
    server = OpenAlexAuthorDisambiguationServer()
    
    # Get authors at different career stages
    test_cases = [
        ("Fiona Watt", "EMBO"),  # Senior researcher
    ]
    
    for name, field in test_cases:
        print(f"\n📚 Analyzing: {name}")
        result = await server.disambiguate_author(
            name=name,
            research_field=field,
            max_candidates=1,
            include_detailed_analysis=True
        )
        
        if result['best_match']:
            author = result['best_match']
            print(f"Name: {author['display_name']}")
            print(f"Career stage: {author['career_stage']}")
            print(f"Seniority score: {author['seniority_score']:.2f}")
            print(f"Career span: {author['first_publication_year']} - {author['last_publication_year']}")
            print(f"Total works: {author['works_count']}")
            print(f"Authorship pattern:")
            print(f"  • First author: {author['authorship_positions']['first']} papers")
            print(f"  • Middle author: {author['authorship_positions']['middle']} papers")
            print(f"  • Last author: {author['authorship_positions']['last']} papers")
            print(f"H-index: {author['h_index']}, Citations: {author['cited_by_count']}")

async def run_comprehensive_test():
    """Run all tests in sequence"""
    print("🚀 OpenAlex Author Disambiguation MCP Server - Comprehensive Test")
    print("=" * 70)
    print(f"Test started at: {datetime.now().isoformat()}")
    
    try:
        # Run all test functions
        await test_basic_disambiguation()
        await test_disambiguation_with_orcid()
        await test_multiple_candidates()
        await test_autocomplete()
        await test_get_by_id()
        await test_advanced_search()
        await demonstrate_career_analysis()
        
        print("\n\n✅ All tests completed successfully!")
        print("=" * 70)
        print("\n🎯 Key Features Demonstrated:")
        print("• Advanced ML-based author disambiguation using OpenAlex")
        print("• Confidence scoring with detailed match reasoning")
        print("• Multiple candidate support for agentic AI decision-making")
        print("• Career stage analysis and seniority scoring")
        print("• ORCID integration for precise matching")
        print("• Comprehensive author profiles with research metrics")
        print("• Fast autocomplete functionality")
        print("• Advanced search with multiple filters")
        print("• Detailed authorship pattern analysis")
        
        print("\n📊 This server provides:")
        print("• Higher accuracy than multi-database approaches")
        print("• Consistent data source (OpenAlex.org)")
        print("• Advanced disambiguation algorithms")
        print("• Rich metadata for informed decision-making")
        print("• Support for N-candidate returns for AI agents")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_comprehensive_test())
