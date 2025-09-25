#!/usr/bin/env python3
"""
Test script to verify the include_abstract option works correctly in MCP tools.

Tests both search_works and retrieve_author_works functions with include_abstract=True/False.
"""

import asyncio
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from alex_mcp.server import search_works_core, retrieve_author_works_core

async def test_include_abstract():
    """Test the include_abstract option in both search functions."""

    print("🧪 Testing include_abstract option...")
    print("=" * 50)
    print(f"Python path: {sys.path[0]}")
    print(f"Working directory: {os.getcwd()}")

    # Test 1: search_works with include_abstract=False
    print("\n1. Testing search_works with include_abstract=False")
    print("-" * 40)

    result_no_abstract = search_works_core(
        query="machine learning",
        limit=3,
        include_abstract=False
    )

    print(f"Found {len(result_no_abstract.results)} works")
    for i, work in enumerate(result_no_abstract.results[:2], 1):
        print(f"  Work {i}: {work.title[:50]}...")
        print(f"    Abstract included: {work.abstract is not None}")
        if work.abstract:
            print(f"    Abstract length: {len(work.abstract)} chars")

    # Test 2: search_works with include_abstract=True
    print("\n2. Testing search_works with include_abstract=True")
    print("-" * 40)

    result_with_abstract = search_works_core(
        query="machine learning",
        limit=3,
        include_abstract=True
    )

    print(f"Found {len(result_with_abstract.results)} works")
    for i, work in enumerate(result_with_abstract.results[:2], 1):
        print(f"  Work {i}: {work.title[:50]}...")
        print(f"    Abstract included: {work.abstract is not None}")
        if work.abstract:
            print(f"    Abstract length: {len(work.abstract)} chars")
            print(f"    Abstract preview: {work.abstract[:100]}...")

    # Test 3: retrieve_author_works with include_abstract=False
    print("\n3. Testing retrieve_author_works with include_abstract=False")
    print("-" * 40)

    # Use a known author ID for testing
    author_id = "https://openalex.org/A5023888391"  # Yann LeCun (known ML researcher)

    result_author_no_abstract = retrieve_author_works_core(
        author_id=author_id,
        limit=2,
        include_abstract=False
    )

    print(f"Found {len(result_author_no_abstract.results)} works for author")
    for i, work in enumerate(result_author_no_abstract.results[:2], 1):
        print(f"  Work {i}: {work.title[:50] if work.title else 'No title'}...")
        print(f"    Abstract included: {work.abstract is not None}")

    # Test 4: retrieve_author_works with include_abstract=True
    print("\n4. Testing retrieve_author_works with include_abstract=True")
    print("-" * 40)

    result_author_with_abstract = retrieve_author_works_core(
        author_id=author_id,
        limit=2,
        include_abstract=True
    )

    print(f"Found {len(result_author_with_abstract.results)} works for author")
    for i, work in enumerate(result_author_with_abstract.results[:2], 1):
        print(f"  Work {i}: {work.title[:50] if work.title else 'No title'}...")
        print(f"    Abstract included: {work.abstract is not None}")
        if work.abstract:
            print(f"    Abstract length: {len(work.abstract)} chars")
            print(f"    Abstract preview: {work.abstract[:100]}...")

    print("\n✅ Test completed!")

if __name__ == "__main__":
    # Set email for testing if not already set
    if not os.environ.get("OPENALEX_MAILTO"):
        os.environ["OPENALEX_MAILTO"] = "cayman-seagraves@utulsa.edu"
        print(f"Set OPENALEX_MAILTO to: {os.environ['OPENALEX_MAILTO']}")

    print(f"Current OPENALEX_MAILTO: {os.environ.get('OPENALEX_MAILTO')}")

    asyncio.run(test_include_abstract())
