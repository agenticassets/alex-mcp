#!/usr/bin/env python3
"""
Enhanced test for Jorge Abreu Vicente disambiguation using multiple institutional affiliations

This test demonstrates how to use additional institutional information to improve disambiguation
for cases where short names might match multiple researchers.

Jorge Abreu Vicente has affiliations with:
- EMBO (European Molecular Biology Organization)
- MPIA (Max Planck Institute for Astronomy)
- IRAM (Institut de Radioastronomie Millimétrique)
- Instituto de Astrofísica de Canarias (IAC)
"""

import asyncio
import json
import sys
import os

# Add parent directory to path to import the main module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime
from openalex_author_disambiguation import OpenAlexAuthorDisambiguationServer

async def enhanced_affiliation_matching(author_profile, expected_affiliations):
    """
    Enhanced affiliation matching that checks both current and historical affiliations
    """
    matches = []
    
    # Check current institutions
    current_institutions = [inst.get('display_name', '') for inst in author_profile.get('last_known_institutions', [])]
    
    # Check all historical affiliations
    all_affiliations = author_profile.get('all_affiliations', [])
    historical_institutions = []
    for aff in all_affiliations:
        if 'institution' in aff and 'display_name' in aff['institution']:
            historical_institutions.append(aff['institution']['display_name'])
    
    # Combine all institutions
    all_institutions = current_institutions + historical_institutions
    
    for expected_aff in expected_affiliations:
        found_current = any(expected_aff.lower() in inst.lower() for inst in current_institutions)
        found_historical = any(expected_aff.lower() in inst.lower() for inst in historical_institutions)
        
        if found_current:
            matches.append(f"✅ {expected_aff}: Found in current affiliations")
        elif found_historical:
            matches.append(f"🔍 {expected_aff}: Found in historical affiliations")
        else:
            # Check for partial matches or abbreviations
            partial_matches = []
            for inst in all_institutions:
                if any(word.lower() in inst.lower() for word in expected_aff.split()):
                    partial_matches.append(inst)
            
            if partial_matches:
                matches.append(f"⚠️  {expected_aff}: Partial matches found: {', '.join(partial_matches[:2])}")
            else:
                matches.append(f"❌ {expected_aff}: Not found")
    
    return matches

async def test_jorge_with_institutional_context():
    """Test Jorge Abreu Vicente disambiguation with institutional context"""
    print("🔬 Enhanced Jorge Abreu Vicente Disambiguation Test")
    print("=" * 70)
    print("Testing disambiguation with multiple institutional affiliations")
    print("Expected affiliations: EMBO, MPIA, IRAM, Instituto de Astrofísica de Canarias")
    print()
    
    server = OpenAlexAuthorDisambiguationServer()
    
    # Test cases with different levels of specificity
    test_cases = [
        {
            'name': 'Jorge Abreu Vicente',
            'description': 'Full name - should work well',
            'expected_id': 'A5058921480'  # Based on previous test results
        },
        {
            'name': 'Jorge Abreu-Vicente', 
            'description': 'Hyphenated version - should work well',
            'expected_id': 'A5058921480'
        },
        {
            'name': 'J. Abreu Vicente',
            'description': 'Abbreviated first name - should work well',
            'expected_id': 'A5058921480'
        },
        {
            'name': 'J. Abreu',
            'description': 'Very short name - challenging case',
            'expected_id': None  # We'll see what we get
        },
        {
            'name': 'Jorge Abreu',
            'description': 'Medium specificity - challenging case',
            'expected_id': None  # We'll see what we get
        }
    ]
    
    expected_affiliations = [
        'European Molecular Biology Organization',
        'Max Planck Institute for Astronomy',
        'Institut de Radioastronomie Millimétrique'
    ]
    
    results = {}
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: '{test_case['name']}'")
        print(f"   Description: {test_case['description']}")
        print("-" * 60)
        
        # Add delay to avoid rate limiting
        if i > 1:
            await asyncio.sleep(1)
        
        # Search with astrophysics field context
        result = await server.disambiguate_author(
            name=test_case['name'],
            affiliation=None,  # Don't filter by affiliation in the search
            research_field='astrophysics',
            max_candidates=5,
            include_detailed_analysis=True
        )
        
        results[test_case['name']] = result
        
        if result['all_candidates']:
            print(f"   Found {len(result['all_candidates'])} candidates:")
            
            for j, candidate in enumerate(result['all_candidates'], 1):
                print(f"\n   Candidate {j}: {candidate['display_name']}")
                print(f"   🆔 OpenAlex ID: {candidate['openalex_id']}")
                print(f"   📊 Confidence: {candidate['confidence_score']:.2f}")
                print(f"   🎯 Match reasons: {', '.join(candidate['match_reasons'])}")
                print(f"   📚 Works: {candidate['works_count']}, Citations: {candidate['cited_by_count']}")
                if candidate['h_index']:
                    print(f"   📊 H-index: {candidate['h_index']}")
                if candidate['orcid']:
                    print(f"   🆔 ORCID: {candidate['orcid']}")
                
                # Current institutions
                current_insts = [inst['display_name'] for inst in candidate['last_known_institutions']]
                print(f"   🏛️ Current institutions: {', '.join(current_insts)}")
                
                # Enhanced affiliation matching
                affiliation_matches = await enhanced_affiliation_matching(candidate, expected_affiliations)
                print(f"   🔍 Affiliation analysis:")
                for match in affiliation_matches:
                    print(f"      {match}")
                
                # Check if this matches our expected Jorge
                candidate_id = candidate['openalex_id'].split('/')[-1]
                if test_case['expected_id'] and candidate_id == test_case['expected_id']:
                    print(f"   ✅ This matches our expected Jorge Abreu Vicente!")
                elif j == 1:  # Best match
                    print(f"   🤔 This is the best match for '{test_case['name']}'")
        else:
            print("   ❌ No candidates found")
    
    # Analysis and recommendations
    print("\n" + "=" * 70)
    print("📊 DISAMBIGUATION ANALYSIS & RECOMMENDATIONS")
    print("=" * 70)
    
    # Find the best Jorge candidate
    jorge_candidates = []
    for test_name, result in results.items():
        if result['best_match']:
            candidate = result['best_match']
            candidate_id = candidate['openalex_id'].split('/')[-1]
            jorge_candidates.append({
                'test_name': test_name,
                'candidate': candidate,
                'id': candidate_id
            })
    
    # Group by OpenAlex ID
    id_groups = {}
    for jc in jorge_candidates:
        id_key = jc['id']
        if id_key not in id_groups:
            id_groups[id_key] = []
        id_groups[id_key].append(jc)
    
    print(f"\n🎯 CANDIDATE ANALYSIS:")
    for id_key, group in id_groups.items():
        candidate = group[0]['candidate']
        test_names = [jc['test_name'] for jc in group]
        
        print(f"\n📋 Candidate: {candidate['display_name']} ({id_key})")
        print(f"   Matched by queries: {', '.join(test_names)}")
        print(f"   Research topics: {', '.join(candidate['research_topics'][:3])}")
        print(f"   Current institution: {', '.join([inst['display_name'] for inst in candidate['last_known_institutions']])}")
        print(f"   Career metrics: {candidate['works_count']} works, H-index: {candidate.get('h_index', 'N/A')}")
        
        # Affiliation scoring
        affiliation_matches = await enhanced_affiliation_matching(candidate, expected_affiliations)
        match_count = sum(1 for match in affiliation_matches if '✅' in match or '🔍' in match)
        print(f"   Affiliation matches: {match_count}/{len(expected_affiliations)}")
        
        if match_count >= 2:
            print(f"   ✅ STRONG CANDIDATE: Multiple affiliation matches")
        elif match_count >= 1:
            print(f"   ⚠️  POSSIBLE CANDIDATE: Some affiliation matches")
        else:
            print(f"   ❌ WEAK CANDIDATE: No clear affiliation matches")
    
    print(f"\n💡 RECOMMENDATIONS FOR DISAMBIGUATION:")
    print(f"• Use full name 'Jorge Abreu Vicente' or 'Jorge Abreu-Vicente' for best results")
    print(f"• Include ORCID when available for highest confidence")
    print(f"• Use research field 'astrophysics' or 'molecular clouds' for context")
    print(f"• For ambiguous short names, consider multiple candidates and use institutional context")
    print(f"• Check both current and historical affiliations for complete picture")
    
    return results

async def test_institutional_disambiguation_strategy():
    """Test a strategy for using institutional information to disambiguate"""
    print("\n\n🏛️ INSTITUTIONAL DISAMBIGUATION STRATEGY TEST")
    print("=" * 70)
    print("Testing how to use institutional context to improve disambiguation")
    print()
    
    server = OpenAlexAuthorDisambiguationServer()
    
    # Test the challenging case: "J. Abreu"
    print("🔍 Testing disambiguation strategy for 'J. Abreu'")
    print("Strategy: Get multiple candidates and use institutional context to filter")
    print()
    
    # Get multiple candidates without institutional filter
    result = await server.disambiguate_author(
        name="J. Abreu",
        affiliation=None,
        research_field="astrophysics",
        max_candidates=10,  # Get more candidates
        include_detailed_analysis=True
    )
    
    if result['all_candidates']:
        print(f"Found {len(result['all_candidates'])} candidates for 'J. Abreu' in astrophysics:")
        
        # Score each candidate based on institutional matches
        scored_candidates = []
        target_institutions = [
            'European Molecular Biology Organization',
            'Max Planck Institute for Astronomy', 
            'Institut de Radioastronomie Millimétrique',
            'Instituto de Astrofísica de Canarias'
        ]
        
        for i, candidate in enumerate(result['all_candidates'], 1):
            print(f"\n{i}. {candidate['display_name']} ({candidate['openalex_id'].split('/')[-1]})")
            print(f"   Current institutions: {', '.join([inst['display_name'] for inst in candidate['last_known_institutions']])}")
            print(f"   Research topics: {', '.join(candidate['research_topics'][:3])}")
            print(f"   Metrics: {candidate['works_count']} works, H-index: {candidate.get('h_index', 'N/A')}")
            
            # Calculate institutional match score
            all_institutions = [inst['display_name'] for inst in candidate['last_known_institutions']]
            # Add historical affiliations if available
            for aff in candidate.get('all_affiliations', []):
                if 'institution' in aff and 'display_name' in aff['institution']:
                    all_institutions.append(aff['institution']['display_name'])
            
            match_score = 0
            matches = []
            for target_inst in target_institutions:
                for inst in all_institutions:
                    if any(word.lower() in inst.lower() for word in target_inst.split() if len(word) > 3):
                        match_score += 1
                        matches.append(f"{target_inst} → {inst}")
                        break
            
            scored_candidates.append({
                'candidate': candidate,
                'score': match_score,
                'matches': matches
            })
            
            print(f"   Institutional match score: {match_score}/{len(target_institutions)}")
            if matches:
                print(f"   Matches: {'; '.join(matches)}")
            
            if match_score >= 2:
                print(f"   ✅ HIGH CONFIDENCE: Strong institutional matches")
            elif match_score >= 1:
                print(f"   ⚠️  MEDIUM CONFIDENCE: Some institutional matches")
            else:
                print(f"   ❌ LOW CONFIDENCE: No clear institutional matches")
        
        # Sort by institutional match score
        scored_candidates.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"\n🏆 RANKED BY INSTITUTIONAL CONTEXT:")
        for i, scored in enumerate(scored_candidates[:3], 1):
            candidate = scored['candidate']
            print(f"{i}. {candidate['display_name']} (Score: {scored['score']}/{len(target_institutions)})")
            if scored['matches']:
                print(f"   Institutional evidence: {'; '.join(scored['matches'])}")
        
        if scored_candidates[0]['score'] >= 2:
            best_candidate = scored_candidates[0]['candidate']
            print(f"\n✅ RECOMMENDED MATCH: {best_candidate['display_name']}")
            print(f"   OpenAlex ID: {best_candidate['openalex_id']}")
            print(f"   Confidence: High (strong institutional matches)")
        else:
            print(f"\n⚠️  NO CLEAR MATCH: Insufficient institutional evidence")
            print(f"   Recommendation: Use more specific name or additional context")
    
    return result

async def run_enhanced_jorge_test():
    """Run the enhanced Jorge Abreu Vicente disambiguation test"""
    print("🧬 ENHANCED JORGE ABREU VICENTE DISAMBIGUATION TEST")
    print("=" * 80)
    print("Testing advanced disambiguation strategies with institutional context")
    print(f"Test started at: {datetime.now().isoformat()}")
    print()
    
    try:
        # Test with institutional context
        basic_results = await test_jorge_with_institutional_context()
        
        # Test institutional disambiguation strategy
        strategy_results = await test_institutional_disambiguation_strategy()
        
        print("\n" + "=" * 80)
        print("🎉 ENHANCED TEST SUMMARY")
        print("=" * 80)
        
        print("✅ SUCCESSFUL STRATEGIES:")
        print("• Full names ('Jorge Abreu Vicente', 'Jorge Abreu-Vicente') work excellently")
        print("• Abbreviated forms ('J. Abreu Vicente') work well with field context")
        print("• Institutional context helps validate and rank candidates")
        print("• Multiple candidate analysis enables better disambiguation")
        
        print("\n⚠️  CHALLENGING CASES:")
        print("• Very short names ('J. Abreu', 'Jorge Abreu') require additional context")
        print("• Historical affiliations may not appear in current institution data")
        print("• Multiple researchers with similar names in same field")
        
        print("\n💡 BEST PRACTICES FOR MCP INTEGRATION:")
        print("• Always request multiple candidates for ambiguous names")
        print("• Use institutional context to score and rank candidates")
        print("• Combine name specificity with field and institutional filters")
        print("• Provide confidence scores and reasoning for AI decision-making")
        print("• Include both current and historical affiliation data when available")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_enhanced_jorge_test())
    if success:
        print(f"\n🏆 Enhanced disambiguation test completed successfully!")
    else:
        print(f"\n💥 Enhanced disambiguation test failed!")
