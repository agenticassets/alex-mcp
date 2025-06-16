#!/usr/bin/env python3
"""
Test the OpenAlex Author Disambiguation MCP Server

Simple test to verify the server works correctly with the new FastMCP implementation.
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_server():
    """Test the server functions directly"""
    print("🧪 Testing OpenAlex Author Disambiguation MCP Server")
    print("=" * 60)
    
    # Import server functions
    from server import (
        disambiguate_author,
        search_authors,
        get_author_profile,
        resolve_institution,
        autocomplete_authors
    )
    
    try:
        # Test 1: Author disambiguation
        print("1. Testing author disambiguation...")
        result = await disambiguate_author(
            name="Fiona Watt",
            affiliation="EMBO",
            research_field="stem cell",
            max_candidates=1
        )
        print("✅ Author disambiguation successful")
        print(f"Result preview: {result[:200]}...")
        print()
        
        # Test 2: Institution resolution
        print("2. Testing institution resolution...")
        result = await resolve_institution("MIT")
        print("✅ Institution resolution successful")
        print(f"Result preview: {result[:200]}...")
        print()
        
        # Test 3: Author search
        print("3. Testing author search...")
        result = await search_authors(
            name="John Smith",
            limit=3
        )
        print("✅ Author search successful")
        print(f"Result preview: {result[:200]}...")
        print()
        
        print("🎉 All tests passed! MCP server is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_server())
    if success:
        print("\n✅ Server is ready for MCP clients!")
    else:
        print("\n❌ Server has issues that need to be fixed.")
        sys.exit(1)
