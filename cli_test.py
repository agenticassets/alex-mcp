#!/usr/bin/env python3
"""
CLI tool for testing author disambiguation
Usage: python cli_test.py "Author Name" "Affiliation" [field]
Example: python cli_test.py "Fiona Watt" "EMBO"
Example: python cli_test.py "John Smith" "Stanford University" "Machine Learning"
"""

import asyncio
import json
import sys
import httpx
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any

@dataclass
class AuthorProfile:
    """Standardized author profile"""
    name: str
    author_id: str
    service: str
    affiliation: Optional[str] = None
    paper_count: int = 0
    citation_count: int = 0
    h_index: Optional[int] = None
    first_author_papers: int = 0
    last_author_papers: int = 0
    middle_author_papers: int = 0
    seniority_score: float = 0.0
    confidence_score: float = 0.0
    profile_url: Optional[str] = None

    def __post_init__(self):
        # Calculate seniority score
        total_papers = self.first_author_papers + self.last_author_papers + self.middle_author_papers
        if total_papers > 0:
            self.seniority_score = (
                (self.first_author_papers * 0.3 + 
                 self.last_author_papers * 1.0 + 
                 self.middle_author_papers * 0.5) / total_papers
            )

async def search_semantic_scholar(name: str, affiliation: str = None) -> List[AuthorProfile]:
    """Search Semantic Scholar for author"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            url = "https://api.semanticscholar.org/graph/v1/author/search"
            params = {
                "query": name,
                "limit": 5,
                "fields": "authorId,name,affiliations,paperCount,citationCount,hIndex"
            }
            
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            profiles = []
            for author_data in data.get("data", []):
                # Calculate confidence based on affiliation match
                confidence = 0.5
                author_affiliations = author_data.get("affiliations", [])
                
                if affiliation and author_affiliations:
                    for aff in author_affiliations:
                        if affiliation.lower() in aff.lower():
                            confidence += 0.3
                            break
                
                profile = AuthorProfile(
                    name=author_data.get("name", ""),
                    author_id=author_data.get("authorId", ""),
                    service="semantic_scholar",
                    affiliation=", ".join(author_affiliations) if author_affiliations else None,
                    paper_count=author_data.get("paperCount", 0),
                    citation_count=author_data.get("citationCount", 0),
                    h_index=author_data.get("hIndex"),
                    confidence_score=min(confidence, 1.0),
                    profile_url=f"https://www.semanticscholar.org/author/{author_data.get('authorId', '')}"
                )
                profiles.append(profile)
            
            return profiles
            
        except Exception as e:
            print(f"❌ Error searching Semantic Scholar: {e}")
            return []

async def search_openalex(name: str, affiliation: str = None) -> List[AuthorProfile]:
    """Search OpenAlex for author"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            url = "https://api.openalex.org/authors"
            params = {
                "filter": f'display_name.search:"{name}"',
                "per-page": 5,
                "select": "id,display_name,last_known_institutions,works_count,cited_by_count,h_index"
            }
            
            # Don't add affiliation filter if it causes 403 errors
            # if affiliation:
            #     params["filter"] += f',last_known_institutions.display_name.search:"{affiliation}"'
            
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            profiles = []
            for author_data in data.get("results", []):
                # Calculate confidence
                confidence = 0.5
                institutions = author_data.get("last_known_institutions", [])
                if affiliation and institutions:
                    for inst in institutions:
                        if affiliation.lower() in inst.get("display_name", "").lower():
                            confidence += 0.3
                            break
                
                profile = AuthorProfile(
                    name=author_data.get("display_name", ""),
                    author_id=author_data.get("id", "").replace("https://openalex.org/", ""),
                    service="openalex",
                    affiliation=", ".join([inst.get("display_name", "") for inst in institutions]),
                    paper_count=author_data.get("works_count", 0),
                    citation_count=author_data.get("cited_by_count", 0),
                    h_index=author_data.get("h_index"),
                    confidence_score=min(confidence, 1.0),
                    profile_url=author_data.get("id", "")
                )
                profiles.append(profile)
            
            return profiles
            
        except Exception as e:
            print(f"❌ Error searching OpenAlex: {e}")
            return []

async def search_europepmc(name: str, affiliation: str = None) -> List[AuthorProfile]:
    """Search EuropePMC for author"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
            query_parts = [f'AUTH:"{name}"']
            if affiliation:
                query_parts.append(f'AFF:"{affiliation}"')
            
            params = {
                "query": " AND ".join(query_parts),
                "format": "json",
                "pageSize": 25,
                "resultType": "core"
            }
            
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Group papers by author
            author_papers = {}
            for paper in data.get("resultList", {}).get("result", []):
                authors = paper.get("authorList", {}).get("author", [])
                for author in authors:
                    author_name = f"{author.get('firstName', '')} {author.get('lastName', '')}".strip()
                    if not author_name or name.lower() not in author_name.lower():
                        continue
                    
                    if author_name not in author_papers:
                        author_papers[author_name] = {
                            "papers": [],
                            "affiliations": set()
                        }
                    
                    author_papers[author_name]["papers"].append(paper)
                    if author.get("affiliation"):
                        author_papers[author_name]["affiliations"].add(author.get("affiliation"))
            
            profiles = []
            for author_name, data_dict in author_papers.items():
                # Calculate confidence
                confidence = 0.4
                if affiliation and data_dict["affiliations"]:
                    for aff in data_dict["affiliations"]:
                        if affiliation.lower() in aff.lower():
                            confidence += 0.4
                            break
                
                profile = AuthorProfile(
                    name=author_name,
                    author_id=f"europepmc_{hash(author_name)}",
                    service="europepmc",
                    affiliation=", ".join(list(data_dict["affiliations"])[:2]),
                    paper_count=len(data_dict["papers"]),
                    citation_count=sum([int(p.get("citedByCount", 0)) for p in data_dict["papers"]]),
                    confidence_score=min(confidence, 1.0),
                    profile_url=f"https://europepmc.org/search?query=AUTH%3A%22{author_name.replace(' ', '%20')}%22"
                )
                profiles.append(profile)
            
            return profiles
            
        except Exception as e:
            print(f"❌ Error searching EuropePMC: {e}")
            return []

async def disambiguate_author(name: str, affiliation: str = None, field: str = None):
    """Main disambiguation function"""
    print("=" * 70)
    print(f"🔬 AUTHOR DISAMBIGUATION TEST")
    print(f"Author: {name}")
    if affiliation:
        print(f"Affiliation: {affiliation}")
    if field:
        print(f"Field: {field}")
    print("=" * 70)
    
    # Search all databases
    print("\n🔍 Searching databases...")
    
    print("   📚 Semantic Scholar...", end=" ")
    ss_results = await search_semantic_scholar(name, affiliation)
    print(f"✅ {len(ss_results)} profiles")
    
    print("   🌐 OpenAlex...", end=" ")
    oa_results = await search_openalex(name, affiliation)
    print(f"✅ {len(oa_results)} profiles")
    
    print("   🧬 EuropePMC...", end=" ")
    emc_results = await search_europepmc(name, affiliation)
    print(f"✅ {len(emc_results)} profiles")
    
    # Combine and rank results
    all_profiles = ss_results + oa_results + emc_results
    all_profiles.sort(key=lambda x: (x.confidence_score, x.paper_count), reverse=True)
    
    print(f"\n📊 RESULTS SUMMARY")
    print(f"Total candidates found: {len(all_profiles)}")
    print("-" * 70)
    
    if all_profiles:
        print(f"\n🏆 TOP MATCHES:")
        for i, profile in enumerate(all_profiles[:5], 1):
            print(f"\n{i}. {profile.name}")
            print(f"   🏢 Service: {profile.service}")
            print(f"   🎯 Confidence: {profile.confidence_score:.2f}")
            print(f"   🏛️  Affiliation: {profile.affiliation or 'Not specified'}")
            print(f"   📄 Papers: {profile.paper_count}")
            print(f"   📈 Citations: {profile.citation_count}")
            if profile.h_index:
                print(f"   📊 H-index: {profile.h_index}")
            print(f"   🔗 Profile: {profile.profile_url}")
        
        # Best match details
        best_match = all_profiles[0]
        print(f"\n🎯 BEST MATCH DETAILS:")
        print(f"Name: {best_match.name}")
        print(f"Service: {best_match.service}")
        print(f"Author ID: {best_match.author_id}")
        print(f"Confidence Score: {best_match.confidence_score:.2f}")
        print(f"Seniority Score: {best_match.seniority_score:.2f}")
        print(f"Affiliation: {best_match.affiliation or 'Not specified'}")
        print(f"Paper Count: {best_match.paper_count}")
        print(f"Citation Count: {best_match.citation_count}")
        if best_match.h_index:
            print(f"H-index: {best_match.h_index}")
        print(f"Profile URL: {best_match.profile_url}")
        
        # Export to JSON
        safe_name = name.replace(" ", "_").replace(".", "").lower()
        filename = f"{safe_name}_results.json"
        result_data = {
            "query": {"name": name, "affiliation": affiliation, "field": field},
            "total_candidates": len(all_profiles),
            "best_match": asdict(best_match),
            "all_candidates": [asdict(p) for p in all_profiles]
        }
        
        with open(filename, "w") as f:
            json.dump(result_data, f, indent=2)
        print(f"\n💾 Results saved to: {filename}")
    
    else:
        print("❌ No matches found!")
    
    print("\n" + "=" * 70)
    print("✅ Disambiguation completed!")

def main():
    """Main CLI function"""
    if len(sys.argv) < 2:
        print("Usage: python cli_test.py \"Author Name\" [\"Affiliation\"] [\"Field\"]")
        print("Examples:")
        print("  python cli_test.py \"Fiona Watt\"")
        print("  python cli_test.py \"Fiona Watt\" \"EMBO\"")
        print("  python cli_test.py \"John Smith\" \"Stanford University\" \"Machine Learning\"")
        sys.exit(1)
    
    name = sys.argv[1]
    affiliation = sys.argv[2] if len(sys.argv) > 2 else None
    field = sys.argv[3] if len(sys.argv) > 3 else None
    
    asyncio.run(disambiguate_author(name, affiliation, field))

if __name__ == "__main__":
    main()
