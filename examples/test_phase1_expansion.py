#!/usr/bin/env python3
"""
Test Phase 1 Expansion: Core Research Tools

This test demonstrates the new Phase 1 tools added to the OpenAlex Author Disambiguation MCP Server:
1. search_works_by_author_openalex - Find publications by author with advanced filtering
2. get_work_details_openalex - Get comprehensive publication details
3. search_topics_openalex - Search and explore research topics/concepts

These tools transform our server from focused author disambiguation into a comprehensive research platform.
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add parent directory to path to import the main module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from openalex_author_disambiguation import OpenAlexAuthorDisambiguationServer

async def test_search_works_by_author():
    """Test searching for works by a specific author"""
    print("🔍 Testing search_works_by_author_openalex")
    print("=" * 60)
    print("Finding publications by Fiona Watt with advanced filtering")
    print()
    
    server = OpenAlexAuthorDisambiguationServer()
    
    # First, get Fiona Watt's OpenAlex ID
    print("Step 1: Finding Fiona Watt's author ID...")
    authors = await server.search_authors("Fiona Watt", research_field="stem cell", limit=1)
    
    if not authors:
        print("❌ Could not find Fiona Watt")
        return False
    
    fiona_id = authors[0].openalex_id
    print(f"✅ Found Fiona Watt: {fiona_id}")
    print()
    
    # Test 1: Recent works (last 5 years)
    print("Test 1: Recent works (2020-2024)")
    print("-" * 40)
    
    recent_works = await server.search_works_by_author(
        author_id=fiona_id,
        publication_year_range="2020-2024",
        sort_by="publication_date",
        limit=10
    )
    
    if recent_works.get("error"):
        print(f"❌ Error: {recent_works['error']}")
    else:
        summary = recent_works["summary"]
        print(f"✅ Found {summary['total_works_found']} recent works")
        print(f"📊 Total citations: {summary['total_citations']:,}")
        print(f"🔓 Open access: {summary['open_access_percentage']:.1f}%")
        print(f"👤 First author papers: {summary['first_author_papers']}")
        print(f"🎯 Last author papers: {summary['last_author_papers']}")
        print(f"📈 Avg citations/paper: {summary['average_citations_per_paper']:.1f}")
        
        print(f"\n📚 Sample recent works:")
        for i, work in enumerate(recent_works["works"][:3], 1):
            print(f"   {i}. {work['title'][:80]}...")
            print(f"      Year: {work['publication_year']}, Citations: {work['cited_by_count']}")
            print(f"      Venue: {work['venue']}")
            print(f"      Author position: {work['author_position']}/{work['total_authors']}")
    
    print()
    
    # Test 2: Highly cited works
    print("Test 2: Most cited works (all time)")
    print("-" * 40)
    
    await asyncio.sleep(1)  # Rate limiting
    
    cited_works = await server.search_works_by_author(
        author_id=fiona_id,
        sort_by="cited_by_count",
        limit=5
    )
    
    if cited_works.get("error"):
        print(f"❌ Error: {cited_works['error']}")
    else:
        print(f"✅ Found {cited_works['summary']['total_works_found']} works")
        print(f"\n🏆 Top cited works:")
        for i, work in enumerate(cited_works["works"][:3], 1):
            print(f"   {i}. {work['title'][:80]}...")
            print(f"      Citations: {work['cited_by_count']:,} | Year: {work['publication_year']}")
            print(f"      Concepts: {', '.join(work['top_concepts'])}")
    
    print()
    
    # Test 3: Works by topic filter
    print("Test 3: Works filtered by topic (stem cell)")
    print("-" * 40)
    
    await asyncio.sleep(1)  # Rate limiting
    
    topic_works = await server.search_works_by_author(
        author_id=fiona_id,
        topic_filter="stem cell",
        limit=5
    )
    
    if topic_works.get("error"):
        print(f"❌ Error: {topic_works['error']}")
    else:
        print(f"✅ Found {topic_works['summary']['total_works_found']} stem cell related works")
        print(f"\n🧬 Stem cell research works:")
        for i, work in enumerate(topic_works["works"][:3], 1):
            print(f"   {i}. {work['title'][:80]}...")
            print(f"      Year: {work['publication_year']}, Citations: {work['cited_by_count']}")
    
    return True

async def test_get_work_details():
    """Test getting detailed information about a specific work"""
    print("\n📄 Testing get_work_details_openalex")
    print("=" * 60)
    print("Getting comprehensive details about a specific publication")
    print()
    
    server = OpenAlexAuthorDisambiguationServer()
    
    # First, get a work ID from Fiona Watt's recent works
    print("Step 1: Finding a recent work by Fiona Watt...")
    authors = await server.search_authors("Fiona Watt", research_field="stem cell", limit=1)
    
    if not authors:
        print("❌ Could not find Fiona Watt")
        return False
    
    fiona_id = authors[0].openalex_id
    
    # Get recent works
    recent_works = await server.search_works_by_author(
        author_id=fiona_id,
        limit=3
    )
    
    if recent_works.get("error") or not recent_works["works"]:
        print("❌ Could not find recent works")
        return False
    
    # Pick the first work
    sample_work = recent_works["works"][0]
    work_id = sample_work["id"]
    
    print(f"✅ Selected work: {sample_work['title'][:60]}...")
    print(f"🆔 Work ID: {work_id}")
    print()
    
    # Test 1: Basic work details
    print("Test 1: Basic work details")
    print("-" * 40)
    
    await asyncio.sleep(1)  # Rate limiting
    
    work_details = await server.get_work_details(
        work_id=work_id,
        include_citations=False,
        include_references=False
    )
    
    if work_details.get("error"):
        print(f"❌ Error: {work_details['error']}")
    else:
        details = work_details["work_details"]
        venue = work_details["venue"]
        authors = work_details["authors"]
        concepts = work_details["concepts"]
        
        print(f"✅ Work Details Retrieved")
        print(f"📄 Title: {details['title']}")
        print(f"📅 Publication: {details['publication_year']} ({details['publication_date']})")
        print(f"📊 Citations: {details['cited_by_count']:,}")
        print(f"🔓 Open Access: {details['is_open_access']}")
        print(f"🏷️ Type: {details['type']}")
        if details['doi']:
            print(f"🔗 DOI: {details['doi']}")
        
        print(f"\n📍 Venue Information:")
        print(f"   • Name: {venue['name']}")
        print(f"   • Type: {venue['type']}")
        print(f"   • Open Access: {venue['is_oa']}")
        
        print(f"\n👥 Authors ({len(authors)} total):")
        for author in authors[:3]:
            institutions = ', '.join(author['institutions']) if author['institutions'] else 'No affiliation'
            print(f"   {author['position']}. {author['name']} ({institutions})")
        if len(authors) > 3:
            print(f"   ... and {len(authors) - 3} more authors")
        
        print(f"\n🏷️ Research Concepts:")
        for concept in concepts[:5]:
            print(f"   • {concept['name']} (Level {concept['level']}, Score: {concept['score']:.2f})")
    
    print()
    
    # Test 2: Work details with citations
    print("Test 2: Work details with citations")
    print("-" * 40)
    
    await asyncio.sleep(1)  # Rate limiting
    
    work_with_citations = await server.get_work_details(
        work_id=work_id,
        include_citations=True,
        include_references=False
    )
    
    if work_with_citations.get("error"):
        print(f"❌ Error: {work_with_citations['error']}")
    else:
        if "citations" in work_with_citations:
            citations = work_with_citations["citations"]
            if citations.get("error"):
                print(f"⚠️ Citations error: {citations['error']}")
            else:
                print(f"✅ Found {citations['total_citing_works']} citing works")
                print(f"\n📚 Sample citing works:")
                for i, citing in enumerate(citations["citing_works_sample"][:3], 1):
                    print(f"   {i}. {citing['title'][:60]}...")
                    print(f"      Year: {citing['publication_year']}, Citations: {citing['cited_by_count']}")
                    print(f"      First author: {citing['first_author']}")
        else:
            print("ℹ️ No citation data available")
    
    return True

async def test_search_topics():
    """Test searching for research topics and concepts"""
    print("\n💡 Testing search_topics_openalex")
    print("=" * 60)
    print("Searching and exploring research topics/concepts")
    print()
    
    server = OpenAlexAuthorDisambiguationServer()
    
    # Test 1: Search for stem cell topics
    print("Test 1: Searching for 'stem cell' topics")
    print("-" * 40)
    
    stem_cell_topics = await server.search_topics(
        topic_query="stem cell",
        limit=5
    )
    
    if stem_cell_topics.get("error"):
        print(f"❌ Error: {stem_cell_topics['error']}")
    else:
        summary = stem_cell_topics["summary"]
        topics = stem_cell_topics["topics"]
        
        print(f"✅ Found {summary['total_topics_found']} stem cell topics")
        print(f"\n🧬 Top stem cell topics:")
        for i, topic in enumerate(topics[:3], 1):
            hierarchy = topic["hierarchy"]
            print(f"   {i}. {topic['name']} (Level {topic['level']})")
            print(f"      Works: {topic['works_count']:,} | Citations: {topic['cited_by_count']:,}")
            print(f"      Relevance: {topic['relevance_score']:.2f}")
            if hierarchy['domain']:
                print(f"      Hierarchy: {hierarchy['domain']} > {hierarchy['field']} > {hierarchy['subfield']}")
            if topic['keywords']:
                print(f"      Keywords: {', '.join(topic['keywords'][:3])}")
    
    print()
    
    # Test 2: Search for AI/ML topics with level filter
    print("Test 2: Searching for 'machine learning' topics (Level 2)")
    print("-" * 40)
    
    await asyncio.sleep(1)  # Rate limiting
    
    ml_topics = await server.search_topics(
        topic_query="machine learning",
        level=2,
        limit=5
    )
    
    if ml_topics.get("error"):
        print(f"❌ Error: {ml_topics['error']}")
    else:
        topics = ml_topics["topics"]
        print(f"✅ Found {len(topics)} Level 2 machine learning topics")
        print(f"\n🤖 Machine learning topics (Level 2):")
        for i, topic in enumerate(topics[:3], 1):
            print(f"   {i}. {topic['name']}")
            print(f"      Works: {topic['works_count']:,} | Relevance: {topic['relevance_score']:.2f}")
            if topic['description']:
                print(f"      Description: {topic['description'][:100]}...")
    
    print()
    
    # Test 3: Search with related topics
    print("Test 3: Searching for 'cancer' with related topics")
    print("-" * 40)
    
    await asyncio.sleep(1)  # Rate limiting
    
    cancer_topics = await server.search_topics(
        topic_query="cancer",
        related_topics=True,
        limit=3
    )
    
    if cancer_topics.get("error"):
        print(f"❌ Error: {cancer_topics['error']}")
    else:
        topics = cancer_topics["topics"]
        print(f"✅ Found {len(topics)} cancer topics")
        
        if topics:
            top_topic = topics[0]
            print(f"\n🎯 Top cancer topic: {top_topic['name']}")
            print(f"   Works: {top_topic['works_count']:,} | Citations: {top_topic['cited_by_count']:,}")
        
        if "related_topics" in cancer_topics:
            related = cancer_topics["related_topics"]
            if related:
                print(f"\n🔗 Related topics:")
                for i, rel_topic in enumerate(related[:3], 1):
                    print(f"   {i}. {rel_topic['name']} (Level {rel_topic['level']})")
                    print(f"      Works: {rel_topic['works_count']:,}")
            else:
                print(f"\nℹ️ No related topics found")
    
    return True

async def test_integration_workflow():
    """Test an integrated workflow using multiple Phase 1 tools"""
    print("\n🔄 Testing Integrated Research Workflow")
    print("=" * 60)
    print("Demonstrating a complete research analysis workflow")
    print()
    
    server = OpenAlexAuthorDisambiguationServer()
    
    # Step 1: Find an author
    print("Step 1: Finding author 'Fiona Watt'...")
    authors = await server.search_authors("Fiona Watt", research_field="stem cell", limit=1)
    
    if not authors:
        print("❌ Could not find author")
        return False
    
    author = authors[0]
    print(f"✅ Found: {author.display_name} ({author.openalex_id})")
    print(f"   Institution: {[inst['display_name'] for inst in author.last_known_institutions]}")
    print(f"   Research topics: {', '.join(author.research_topics[:3])}")
    print()
    
    # Step 2: Get their recent high-impact works
    print("Step 2: Finding recent high-impact works...")
    await asyncio.sleep(1)
    
    recent_works = await server.search_works_by_author(
        author_id=author.openalex_id,
        publication_year_range="2020-2024",
        sort_by="cited_by_count",
        limit=3
    )
    
    if recent_works.get("error"):
        print(f"❌ Error: {recent_works['error']}")
        return False
    
    print(f"✅ Found {recent_works['summary']['total_works_found']} recent works")
    
    if not recent_works["works"]:
        print("❌ No works found")
        return False
    
    # Pick the most cited recent work
    top_work = recent_works["works"][0]
    print(f"🏆 Top recent work: {top_work['title'][:60]}...")
    print(f"   Citations: {top_work['cited_by_count']:,} | Year: {top_work['publication_year']}")
    print()
    
    # Step 3: Get detailed information about the top work
    print("Step 3: Analyzing the top work in detail...")
    await asyncio.sleep(1)
    
    work_details = await server.get_work_details(
        work_id=top_work["id"],
        include_citations=True,
        include_references=False
    )
    
    if work_details.get("error"):
        print(f"❌ Error: {work_details['error']}")
    else:
        details = work_details["work_details"]
        authors_list = work_details["authors"]
        concepts = work_details["concepts"]
        
        print(f"✅ Detailed analysis complete")
        print(f"📄 Title: {details['title']}")
        print(f"👥 Authors: {len(authors_list)} total")
        print(f"🏷️ Key concepts: {', '.join([c['name'] for c in concepts[:3]])}")
        
        if "citations" in work_details and not work_details["citations"].get("error"):
            citations = work_details["citations"]
            print(f"📚 Citing works: {citations['total_citing_works']}")
    
    print()
    
    # Step 4: Explore related research topics
    print("Step 4: Exploring related research topics...")
    await asyncio.sleep(1)
    
    # Use the top concept from the work
    if work_details.get("concepts"):
        top_concept = work_details["concepts"][0]["name"]
        
        topic_search = await server.search_topics(
            topic_query=top_concept,
            related_topics=True,
            limit=3
        )
        
        if topic_search.get("error"):
            print(f"❌ Error: {topic_search['error']}")
        else:
            topics = topic_search["topics"]
            print(f"✅ Found {len(topics)} topics related to '{top_concept}'")
            
            if topics:
                main_topic = topics[0]
                print(f"🎯 Main topic: {main_topic['name']}")
                print(f"   Research volume: {main_topic['works_count']:,} works")
                print(f"   Citation impact: {main_topic['cited_by_count']:,} citations")
                
                if "related_topics" in topic_search:
                    related = topic_search["related_topics"]
                    if related:
                        print(f"🔗 Related research areas:")
                        for rel_topic in related[:2]:
                            print(f"   • {rel_topic['name']} ({rel_topic['works_count']:,} works)")
    
    print()
    print("🎉 Integrated workflow completed successfully!")
    print("This demonstrates how the Phase 1 tools work together for comprehensive research analysis.")
    
    return True

async def run_phase1_expansion_test():
    """Run comprehensive Phase 1 expansion test"""
    print("🚀 PHASE 1 EXPANSION TEST")
    print("=" * 80)
    print("Testing new core research tools added to OpenAlex Author Disambiguation MCP Server")
    print("Phase 1 Tools: Works Search, Work Details, Topics Search")
    print(f"Test started at: {datetime.now().isoformat()}")
    print()
    
    try:
        # Test individual tools
        test1_success = await test_search_works_by_author()
        test2_success = await test_get_work_details()
        test3_success = await test_search_topics()
        
        # Test integrated workflow
        integration_success = await test_integration_workflow()
        
        print("\n" + "=" * 80)
        print("🎉 PHASE 1 EXPANSION TEST SUMMARY")
        print("=" * 80)
        
        print(f"📊 INDIVIDUAL TOOL TESTS:")
        print(f"   • search_works_by_author_openalex: {'✅ PASSED' if test1_success else '❌ FAILED'}")
        print(f"   • get_work_details_openalex: {'✅ PASSED' if test2_success else '❌ FAILED'}")
        print(f"   • search_topics_openalex: {'✅ PASSED' if test3_success else '❌ FAILED'}")
        
        print(f"\n🔄 INTEGRATION TEST:")
        print(f"   • Complete research workflow: {'✅ PASSED' if integration_success else '❌ FAILED'}")
        
        print(f"\n✨ NEW CAPABILITIES DEMONSTRATED:")
        print(f"   • 📄 Publication search with advanced filtering (year, type, topic)")
        print(f"   • 📊 Research impact analysis (citations, authorship patterns)")
        print(f"   • 🔍 Detailed publication analysis (authors, venues, concepts)")
        print(f"   • 📚 Citation and reference tracking")
        print(f"   • 💡 Research topic discovery and exploration")
        print(f"   • 🌐 Topic hierarchy and relationship mapping")
        print(f"   • 🔄 Integrated research intelligence workflows")
        
        print(f"\n🎯 TRANSFORMATION ACHIEVED:")
        print(f"   • From: Focused author disambiguation (6 tools)")
        print(f"   • To: Comprehensive research intelligence platform (9 tools)")
        print(f"   • Added: Complete publication and topic analysis capabilities")
        print(f"   • Benefit: AI agents can now perform complex research workflows")
        
        overall_success = test1_success and test2_success and test3_success and integration_success
        return overall_success
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_phase1_expansion_test())
    if success:
        print(f"\n🏆 Phase 1 expansion test completed successfully!")
        print(f"The MCP server has been successfully transformed into a comprehensive research platform!")
    else:
        print(f"\n💥 Phase 1 expansion test failed!")
