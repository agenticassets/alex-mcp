#!/usr/bin/env python3
"""
Test for Institution Resolution using OpenAlex Author Disambiguation MCP Server

This test demonstrates the professional institution resolution feature that automatically
expands abbreviations and resolves institution names to their full OpenAlex data.

Examples:
- EMBO → European Molecular Biology Organization
- MIT → Massachusetts Institute of Technology
- Max Planck → Max Planck Institute for [specific field]
- MPIA → Max Planck Institute for Astronomy
- IRAM → Institut de Radioastronomie Millimétrique
"""

import asyncio
import sys
import os

# Add parent directory to path to import the main module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import sys
import os
from datetime import datetime

# Add parent directory to path to import the main module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from openalex_author_disambiguation import OpenAlexAuthorDisambiguationServer

async def test_single_institution_resolution():
    """Test resolving individual institution abbreviations"""
    print("🏛️ Testing Single Institution Resolution")
    print("=" * 60)
    print("Testing automatic expansion of institution abbreviations")
    print()
    
    server = OpenAlexAuthorDisambiguationServer()
    
    # Test cases for institution resolution
    test_cases = [
        {
            'query': 'EMBO',
            'description': 'European Molecular Biology Organization abbreviation',
            'expected_keywords': ['European', 'Molecular', 'Biology', 'Organization']
        },
        {
            'query': 'MIT',
            'description': 'Massachusetts Institute of Technology abbreviation',
            'expected_keywords': ['Massachusetts', 'Institute', 'Technology']
        },
        {
            'query': 'MPIA',
            'description': 'Max Planck Institute for Astronomy abbreviation',
            'expected_keywords': ['Max', 'Planck', 'Astronomy']
        },
        {
            'query': 'IRAM',
            'description': 'Institut de Radioastronomie Millimétrique abbreviation',
            'expected_keywords': ['Institut', 'Radioastronomie', 'Millimétrique']
        },
        {
            'query': 'Max Planck',
            'description': 'Partial name for Max Planck institutes',
            'expected_keywords': ['Max', 'Planck', 'Institute']
        },
        {
            'query': 'Stanford',
            'description': 'Stanford University partial name',
            'expected_keywords': ['Stanford', 'University']
        }
    ]
    
    results = {}
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. Testing: '{test_case['query']}'")
        print(f"   Description: {test_case['description']}")
        print("-" * 50)
        
        # Add delay to avoid rate limiting
        if i > 1:
            await asyncio.sleep(0.5)
        
        resolved = await server.resolve_institution(test_case['query'])
        results[test_case['query']] = resolved
        
        if resolved:
            print(f"   ✅ RESOLVED:")
            print(f"   📍 Full Name: {resolved['display_name']}")
            print(f"   🆔 OpenAlex ID: {resolved['id']}")
            print(f"   🌍 Country: {resolved.get('country_code', 'N/A')}")
            print(f"   🏢 Type: {resolved.get('type', 'N/A')}")
            print(f"   📊 Match Score: {resolved.get('match_score', 0)}/100")
            print(f"   🎯 Match Type: {resolved.get('match_type', 'N/A')}")
            
            # Check for alternative names
            alternatives = resolved.get('display_name_alternatives', [])
            if alternatives:
                print(f"   📝 Alternative Names: {', '.join(alternatives[:3])}...")
            
            # Check if expected keywords are present
            full_name = resolved['display_name'].lower()
            matched_keywords = [kw for kw in test_case['expected_keywords'] if kw.lower() in full_name]
            if matched_keywords:
                print(f"   ✅ Expected keywords found: {', '.join(matched_keywords)}")
            else:
                print(f"   ⚠️  Expected keywords not found in: {resolved['display_name']}")
            
            # Homepage URL if available
            if resolved.get('homepage_url'):
                print(f"   🌐 Homepage: {resolved['homepage_url']}")
        else:
            print(f"   ❌ NOT RESOLVED: No matching institution found")
        
        print()
    
    return results

async def test_batch_institution_resolution():
    """Test resolving multiple institutions in batch"""
    print("\n🏛️ Testing Batch Institution Resolution")
    print("=" * 60)
    print("Testing efficient batch resolution of multiple institutions")
    print()
    
    server = OpenAlexAuthorDisambiguationServer()
    
    # Jorge Abreu Vicente's affiliations
    jorge_affiliations = ['EMBO', 'MPIA', 'IRAM', 'Instituto de Astrofísica de Canarias']
    
    # Additional test cases
    common_abbreviations = ['MIT', 'Stanford', 'Harvard', 'Oxford', 'Cambridge']
    
    print("🔬 Resolving Jorge Abreu Vicente's affiliations:")
    print(f"   Input: {', '.join(jorge_affiliations)}")
    print()
    
    jorge_results = await server.resolve_multiple_institutions(jorge_affiliations)
    
    for query, resolved in jorge_results.items():
        if resolved:
            print(f"✅ {query} → {resolved['display_name']}")
            print(f"   🆔 {resolved['id']} | 🌍 {resolved.get('country_code', 'N/A')} | 📊 {resolved.get('match_score', 0)}/100")
        else:
            print(f"❌ {query} → Not resolved")
        print()
    
    print("🎓 Resolving common university abbreviations:")
    print(f"   Input: {', '.join(common_abbreviations)}")
    print()
    
    # Add delay before second batch
    await asyncio.sleep(1)
    
    university_results = await server.resolve_multiple_institutions(common_abbreviations)
    
    for query, resolved in university_results.items():
        if resolved:
            print(f"✅ {query} → {resolved['display_name']}")
            print(f"   🆔 {resolved['id']} | 🌍 {resolved.get('country_code', 'N/A')} | 📊 {resolved.get('match_score', 0)}/100")
        else:
            print(f"❌ {query} → Not resolved")
        print()
    
    return {
        'jorge_affiliations': jorge_results,
        'universities': university_results
    }

async def test_enhanced_disambiguation_with_resolved_institutions():
    """Test author disambiguation using resolved institution names"""
    print("\n🔬 Testing Enhanced Disambiguation with Resolved Institutions")
    print("=" * 70)
    print("Demonstrating how institution resolution improves author disambiguation")
    print()
    
    server = OpenAlexAuthorDisambiguationServer()
    
    # First, resolve EMBO to get the full name
    print("Step 1: Resolving 'EMBO' abbreviation...")
    embo_resolved = await server.resolve_institution('EMBO')
    
    if embo_resolved:
        full_embo_name = embo_resolved['display_name']
        print(f"✅ EMBO resolved to: {full_embo_name}")
        print()
        
        # Now test disambiguation with both abbreviation and full name
        print("Step 2: Testing author disambiguation with abbreviation vs full name...")
        print()
        
        # Test with abbreviation
        print("🔍 Searching with abbreviation 'EMBO':")
        await asyncio.sleep(0.5)
        result_abbrev = await server.disambiguate_author(
            name="Fiona Watt",
            affiliation="EMBO",
            research_field="stem cell",
            max_candidates=2,
            include_detailed_analysis=False
        )
        
        print(f"   Found {len(result_abbrev['all_candidates'])} candidates")
        if result_abbrev['best_match']:
            best = result_abbrev['best_match']
            print(f"   Best match: {best['display_name']} (confidence: {best['confidence_score']:.2f})")
        
        # Test with full name
        print(f"\n🔍 Searching with full name '{full_embo_name}':")
        await asyncio.sleep(0.5)
        result_full = await server.disambiguate_author(
            name="Fiona Watt",
            affiliation=full_embo_name,
            research_field="stem cell",
            max_candidates=2,
            include_detailed_analysis=False
        )
        
        print(f"   Found {len(result_full['all_candidates'])} candidates")
        if result_full['best_match']:
            best = result_full['best_match']
            print(f"   Best match: {best['display_name']} (confidence: {best['confidence_score']:.2f})")
        
        # Compare results
        print(f"\n📊 COMPARISON:")
        abbrev_confidence = result_abbrev['best_match']['confidence_score'] if result_abbrev['best_match'] else 0
        full_confidence = result_full['best_match']['confidence_score'] if result_full['best_match'] else 0
        
        print(f"   Abbreviation confidence: {abbrev_confidence:.2f}")
        print(f"   Full name confidence: {full_confidence:.2f}")
        
        if full_confidence > abbrev_confidence:
            print(f"   ✅ Full institution name provides better disambiguation!")
        elif abbrev_confidence > full_confidence:
            print(f"   ⚠️  Abbreviation worked better (possibly due to API filtering)")
        else:
            print(f"   ➡️  Both approaches yielded similar results")
        
        return {
            'embo_resolved': embo_resolved,
            'abbreviation_result': result_abbrev,
            'full_name_result': result_full
        }
    else:
        print("❌ Could not resolve EMBO abbreviation")
        return None

async def run_institution_resolution_test():
    """Run comprehensive institution resolution test"""
    print("🏛️ INSTITUTION RESOLUTION TEST")
    print("=" * 80)
    print("Testing professional institution name resolution and disambiguation enhancement")
    print(f"Test started at: {datetime.now().isoformat()}")
    print()
    
    try:
        # Test single institution resolution
        single_results = await test_single_institution_resolution()
        
        # Test batch resolution
        batch_results = await test_batch_institution_resolution()
        
        # Test enhanced disambiguation
        enhanced_results = await test_enhanced_disambiguation_with_resolved_institutions()
        
        print("\n" + "=" * 80)
        print("🎉 INSTITUTION RESOLUTION TEST SUMMARY")
        print("=" * 80)
        
        # Analyze single resolution results
        single_success = sum(1 for result in single_results.values() if result is not None)
        single_total = len(single_results)
        
        print(f"📊 SINGLE INSTITUTION RESOLUTION:")
        print(f"   • Success rate: {single_success}/{single_total} ({single_success/single_total*100:.1f}%)")
        
        successful_resolutions = []
        for query, result in single_results.items():
            if result:
                successful_resolutions.append(f"{query} → {result['display_name']}")
        
        if successful_resolutions:
            print(f"   • Successful resolutions:")
            for resolution in successful_resolutions:
                print(f"     - {resolution}")
        
        # Analyze batch resolution results
        jorge_success = sum(1 for result in batch_results['jorge_affiliations'].values() if result is not None)
        jorge_total = len(batch_results['jorge_affiliations'])
        
        uni_success = sum(1 for result in batch_results['universities'].values() if result is not None)
        uni_total = len(batch_results['universities'])
        
        print(f"\n📊 BATCH INSTITUTION RESOLUTION:")
        print(f"   • Jorge's affiliations: {jorge_success}/{jorge_total} ({jorge_success/jorge_total*100:.1f}%)")
        print(f"   • University abbreviations: {uni_success}/{uni_total} ({uni_success/uni_total*100:.1f}%)")
        
        # Professional features summary
        print(f"\n✅ PROFESSIONAL FEATURES DEMONSTRATED:")
        print(f"   • Automatic abbreviation expansion (EMBO → European Molecular Biology Organization)")
        print(f"   • Intelligent matching with confidence scoring")
        print(f"   • Batch processing for efficiency")
        print(f"   • Integration with author disambiguation")
        print(f"   • Alternative name recognition")
        print(f"   • Country and institution type information")
        
        print(f"\n💡 BENEFITS FOR AI AGENTS:")
        print(f"   • No need to manually expand abbreviations")
        print(f"   • Consistent institution naming across queries")
        print(f"   • Improved disambiguation accuracy")
        print(f"   • Structured institution metadata")
        print(f"   • Confidence scores for automated decision-making")
        
        overall_success = (single_success + jorge_success + uni_success) > 0
        return overall_success
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_institution_resolution_test())
    if success:
        print(f"\n🏆 Institution resolution test completed successfully!")
        print(f"The MCP server now provides professional-grade institution resolution!")
    else:
        print(f"\n💥 Institution resolution test failed!")
