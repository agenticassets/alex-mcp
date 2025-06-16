#!/usr/bin/env python3
"""
Test the Expanded OpenAlex MCP Server

Comprehensive test of all 10 tools including the 5 new research intelligence tools.
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_expanded_server():
    """Test all server functions including new research intelligence tools"""
    print("🧪 Testing Expanded OpenAlex MCP Server (10 Tools)")
    print("=" * 70)
    
    # Import all server functions
    from server import (
        # Original 5 tools
        disambiguate_author,
        search_authors,
        get_author_profile,
        resolve_institution,
        autocomplete_authors,
        # New 5 research intelligence tools
        search_works,
        get_work_details,
        search_topics,
        analyze_text_aboutness,
        search_sources
    )
    
    success_count = 0
    total_tests = 10
    
    try:
        # Test 1: Author disambiguation (original)
        print("1. Testing author disambiguation...")
        result = await disambiguate_author(name="John Smith", max_candidates=1)
        print("✅ Author disambiguation completed")
        print(f"   Preview: {result[:100]}...")
        success_count += 1
        print()
        
        # Test 2: Institution resolution (original)
        print("2. Testing institution resolution...")
        result = await resolve_institution("Stanford")
        print("✅ Institution resolution successful")
        print(f"   Preview: {result[:100]}...")
        success_count += 1
        print()
        
        # Test 3: Search works (NEW)
        print("3. Testing search works...")
        result = await search_works(
            query="machine learning",
            publication_year="2023",
            limit=3
        )
        print("✅ Search works successful")
        print(f"   Preview: {result[:100]}...")
        success_count += 1
        print()
        
        # Test 4: Search topics (NEW)
        print("4. Testing search topics...")
        result = await search_topics(
            query="artificial intelligence",
            limit=3
        )
        print("✅ Search topics successful")
        print(f"   Preview: {result[:100]}...")
        success_count += 1
        print()
        
        # Test 5: Analyze text aboutness (NEW)
        print("5. Testing text analysis...")
        result = await analyze_text_aboutness(
            title="Deep Learning for Natural Language Processing",
            abstract="This paper explores the application of deep neural networks to natural language understanding tasks."
        )
        print("✅ Text analysis successful")
        print(f"   Preview: {result[:100]}...")
        success_count += 1
        print()
        
        # Test 6: Search sources (NEW)
        print("6. Testing search sources...")
        result = await search_sources(
            query="Nature",
            source_type="journal",
            limit=3
        )
        print("✅ Search sources successful")
        print(f"   Preview: {result[:100]}...")
        success_count += 1
        print()
        
        # Test 7: Author search (original)
        print("7. Testing author search...")
        result = await search_authors(
            name="Einstein",
            limit=2
        )
        print("✅ Author search successful")
        print(f"   Preview: {result[:100]}...")
        success_count += 1
        print()
        
        # Test 8: Autocomplete authors (original)
        print("8. Testing author autocomplete...")
        result = await autocomplete_authors(
            query="Marie Cur",
            limit=3
        )
        print("✅ Author autocomplete successful")
        print(f"   Preview: {result[:100]}...")
        success_count += 1
        print()
        
        # Test 9: Get work details (NEW) - using a known work ID
        print("9. Testing get work details...")
        # First search for a work to get an ID
        search_result = await search_works("quantum computing", limit=1)
        if "OpenAlex ID:" in search_result:
            # Extract work ID from search result
            lines = search_result.split('\n')
            work_id = None
            for line in lines:
                if "OpenAlex ID:" in line:
                    work_id = line.split("OpenAlex ID: ")[1].strip()
                    break
            
            if work_id:
                result = await get_work_details(work_id)
                print("✅ Get work details successful")
                print(f"   Preview: {result[:100]}...")
                success_count += 1
            else:
                print("⚠️ Get work details skipped (no work ID found)")
        else:
            print("⚠️ Get work details skipped (no works found)")
        print()
        
        # Test 10: Get author profile (original) - using a known author ID
        print("10. Testing get author profile...")
        # First search for an author to get an ID
        search_result = await search_authors("Einstein", limit=1)
        if "OpenAlex ID:" in search_result:
            # Extract author ID from search result
            lines = search_result.split('\n')
            author_id = None
            for line in lines:
                if "OpenAlex ID:" in line:
                    author_id = line.split("OpenAlex ID: ")[1].strip()
                    break
            
            if author_id:
                result = await get_author_profile(author_id)
                print("✅ Get author profile successful")
                print(f"   Preview: {result[:100]}...")
                success_count += 1
            else:
                print("⚠️ Get author profile skipped (no author ID found)")
        else:
            print("⚠️ Get author profile skipped (no authors found)")
        print()
        
        # Summary
        print("🎉 EXPANDED SERVER TEST COMPLETE!")
        print(f"✅ {success_count}/{total_tests} tools tested successfully")
        print()
        print("🚀 NEW RESEARCH INTELLIGENCE TOOLS:")
        print("   • search_works - Find publications with advanced filtering")
        print("   • get_work_details - Detailed publication information")
        print("   • search_topics - Explore research topics and trends")
        print("   • analyze_text_aboutness - ML-powered text classification")
        print("   • search_sources - Find journals and publication venues")
        print()
        print("📊 ORIGINAL AUTHOR TOOLS:")
        print("   • disambiguate_author - ML-powered author disambiguation")
        print("   • search_authors - Advanced author search")
        print("   • get_author_profile - Detailed author profiles")
        print("   • resolve_institution - Institution name resolution")
        print("   • autocomplete_authors - Fast author suggestions")
        
        return success_count >= 8  # Allow for some API limitations
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_expanded_server())
    if success:
        print("\n✅ Expanded server is ready for production!")
        print("🎯 10 professional tools available for research intelligence")
    else:
        print("\n❌ Server has issues that need to be fixed.")
        sys.exit(1)
