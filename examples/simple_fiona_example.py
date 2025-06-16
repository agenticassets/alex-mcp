#!/usr/bin/env python3
"""
Simple Fiona Watt Disambiguation Example - Semantic Scholar Only

This example demonstrates author disambiguation using only Semantic Scholar,
which provides the most reliable results. It focuses on clear seniority 
classification and practical disambiguation.
"""

import asyncio
import json
import httpx
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class AuthorProfile:
    """Simplified author profile focused on key metrics"""
    name: str
    author_id: str
    affiliation: Optional[str] = None
    paper_count: int = 0
    citation_count: int = 0
    h_index: Optional[int] = None
    first_author_papers: int = 0
    last_author_papers: int = 0
    middle_author_papers: int = 0
    career_stage: str = "Unknown"  # Early, Mid, Late Career
    confidence_score: float = 0.0
    profile_url: Optional[str] = None

    def __post_init__(self):
        # Calculate career stage based on first + last author papers
        total_papers = self.first_author_papers + self.last_author_papers + self.middle_author_papers
        if total_papers > 0:
            # Focus on first and last author papers for career stage
            senior_papers = self.first_author_papers + self.last_author_papers
            senior_ratio = senior_papers / total_papers
            
            # Classification based on total papers and senior authorship ratio
            if total_papers >= 20 and self.last_author_papers >= 5:
                self.career_stage = "Late Career"
            elif total_papers >= 10 and senior_ratio >= 0.4:
                self.career_stage = "Mid Career"
            elif total_papers >= 3:
                self.career_stage = "Early Career"
            else:
                self.career_stage = "Very Early Career"

async def search_semantic_scholar_simple(name: str, affiliation: str = None) -> List[AuthorProfile]:
    """Search Semantic Scholar with simplified, reliable approach"""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            url = "https://api.semanticscholar.org/graph/v1/author/search"
            params = {
                "query": name,
                "limit": 10,
                "fields": "authorId,name,affiliations,paperCount,citationCount,hIndex,papers.title,papers.year,papers.authors"
            }
            
            print(f"🔍 Searching Semantic Scholar for: {name}")
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            profiles = []
            for author_data in data.get("data", []):
                # Calculate authorship positions
                first_author = last_author = middle_author = 0
                papers = author_data.get("papers", [])
                
                for paper in papers:
                    authors = paper.get("authors", [])
                    if not authors:
                        continue
                        
                    # Find this author's position in the paper
                    author_positions = [i for i, a in enumerate(authors) 
                                     if a.get("authorId") == author_data.get("authorId")]
                    
                    for pos in author_positions:
                        if pos == 0:
                            first_author += 1
                        elif pos == len(authors) - 1:
                            last_author += 1
                        else:
                            middle_author += 1
                
                # Calculate confidence score
                confidence = 0.5  # Base confidence for name match
                author_affiliations = author_data.get("affiliations", [])
                
                # Boost confidence if affiliation matches
                if affiliation and author_affiliations:
                    for aff in author_affiliations:
                        if affiliation.lower() in aff.lower():
                            confidence += 0.3
                            break
                
                # Create profile
                profile = AuthorProfile(
                    name=author_data.get("name", ""),
                    author_id=author_data.get("authorId", ""),
                    affiliation=", ".join(author_affiliations) if author_affiliations else None,
                    paper_count=author_data.get("paperCount", 0),
                    citation_count=author_data.get("citationCount", 0),
                    h_index=author_data.get("hIndex"),
                    first_author_papers=first_author,
                    last_author_papers=last_author,
                    middle_author_papers=middle_author,
                    confidence_score=min(confidence, 1.0),
                    profile_url=f"https://www.semanticscholar.org/author/{author_data.get('authorId', '')}"
                )
                profiles.append(profile)
            
            return profiles
            
        except Exception as e:
            print(f"❌ Error searching Semantic Scholar: {e}")
            return []

async def run_simple_fiona_example():
    """Run simple, focused Fiona Watt disambiguation"""
    
    print("=" * 70)
    print("🧬 FIONA WATT AUTHOR DISAMBIGUATION")
    print("   Using Semantic Scholar (Most Reliable)")
    print("=" * 70)
    print("Author: Fiona Watt")
    print("Affiliation: EMBO")
    print("Expected: Prominent stem cell biologist")
    print("=" * 70)
    
    # Search parameters
    name = "Fiona Watt"
    affiliation = "EMBO"
    
    # Search Semantic Scholar
    profiles = await search_semantic_scholar_simple(name, affiliation)
    
    if not profiles:
        print("❌ No profiles found!")
        return
    
    print(f"\n✅ Found {len(profiles)} author profiles")
    print("=" * 70)
    
    # Sort by confidence, then by citation count
    profiles.sort(key=lambda x: (x.confidence_score, x.citation_count), reverse=True)
    
    # Show all candidates
    print("\n📋 ALL CANDIDATES:")
    print("-" * 70)
    
    for i, profile in enumerate(profiles, 1):
        print(f"\n{i}. {profile.name}")
        print(f"   📊 Papers: {profile.paper_count} | Citations: {profile.citation_count} | H-index: {profile.h_index}")
        print(f"   👤 Career Stage: {profile.career_stage}")
        print(f"   📝 Authorship: {profile.first_author_papers} first, {profile.last_author_papers} last, {profile.middle_author_papers} middle")
        print(f"   🎯 Confidence: {profile.confidence_score:.2f}")
        if profile.affiliation:
            print(f"   🏛️  Affiliation: {profile.affiliation}")
        print(f"   🔗 Profile: {profile.profile_url}")
    
    # Best match analysis
    best_match = profiles[0]
    print(f"\n🏆 BEST MATCH ANALYSIS")
    print("=" * 70)
    print(f"Name: {best_match.name}")
    print(f"Semantic Scholar ID: {best_match.author_id}")
    print(f"Career Stage: {best_match.career_stage}")
    print(f"Confidence Score: {best_match.confidence_score:.2f}")
    print(f"Research Output: {best_match.paper_count} papers, {best_match.citation_count} citations")
    if best_match.h_index:
        print(f"H-index: {best_match.h_index}")
    
    # Career stage explanation
    total_papers = best_match.first_author_papers + best_match.last_author_papers + best_match.middle_author_papers
    if total_papers > 0:
        print(f"\nCareer Stage Analysis:")
        print(f"• First author papers: {best_match.first_author_papers} ({best_match.first_author_papers/total_papers*100:.1f}%)")
        print(f"• Last author papers: {best_match.last_author_papers} ({best_match.last_author_papers/total_papers*100:.1f}%)")
        print(f"• Middle author papers: {best_match.middle_author_papers} ({best_match.middle_author_papers/total_papers*100:.1f}%)")
        
        if best_match.career_stage == "Late Career":
            print("→ Senior researcher with established lab (many last author papers)")
        elif best_match.career_stage == "Mid Career":
            print("→ Established researcher transitioning to independence")
        elif best_match.career_stage == "Early Career":
            print("→ Early career researcher, likely postdoc or new PI")
        else:
            print("→ Very early career, likely graduate student or early postdoc")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"fiona_watt_simple_{timestamp}.json"
    
    result_data = {
        "query": {
            "name": name,
            "affiliation": affiliation,
            "timestamp": datetime.now().isoformat()
        },
        "results": {
            "total_candidates": len(profiles),
            "best_match": asdict(best_match),
            "all_candidates": [asdict(p) for p in profiles]
        },
        "summary": {
            "search_successful": True,
            "primary_database": "semantic_scholar",
            "best_match_career_stage": best_match.career_stage,
            "best_match_confidence": best_match.confidence_score
        }
    }
    
    with open(filename, 'w') as f:
        json.dump(result_data, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {filename}")
    
    # Summary insights
    print(f"\n🔬 KEY INSIGHTS")
    print("=" * 70)
    print("✅ Semantic Scholar provides reliable author disambiguation")
    print("✅ Career stage classification based on authorship patterns")
    print("✅ Confidence scoring helps identify best matches")
    print(f"✅ Found {len(profiles)} potential matches for Fiona Watt")
    
    if best_match.confidence_score > 0.7:
        print("✅ High confidence match found!")
    elif best_match.confidence_score > 0.5:
        print("⚠️  Moderate confidence - may need additional validation")
    else:
        print("⚠️  Low confidence - consider additional search criteria")
    
    print(f"\n🎯 RECOMMENDATION")
    print("-" * 70)
    print(f"Best candidate: {best_match.name}")
    print(f"Reason: {best_match.career_stage} researcher with {best_match.citation_count} citations")
    print(f"Confidence: {best_match.confidence_score:.2f}")
    
    print(f"\n✅ Simple disambiguation completed successfully!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_simple_fiona_example())
