"""
Quick API Test Script
Tests all FastAPI endpoints
"""

import asyncio
import httpx
from pprint import pprint

BASE_URL = "http://localhost:8000"


async def test_health():
    """Test health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/health")
        print(f"Status: {response.status_code}")
        pprint(response.json())


async def test_get_drugs():
    """Test get all drugs"""
    print("\n=== Testing Get All Drugs ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/drugs/?limit=5")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Total drugs: {data['total']}")
        print(f"Returned: {len(data['drugs'])}")
        if data['drugs']:
            print(f"First drug: {data['drugs'][0]['brand_name']}")


async def test_get_drug_by_id():
    """Test get specific drug"""
    print("\n=== Testing Get Drug by ID ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/drugs/1")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Drug: {data['brand_name']} ({data['generic_name']})")
            print(f"Sections: {len(data['sections'])}")


async def test_semantic_search():
    """Test semantic search"""
    print("\n=== Testing Semantic Search ===")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/search/semantic",
            json={
                "query": "What are the side effects and warnings?",
                "top_k": 3
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data['results'])} results in {data['execution_time_ms']:.2f}ms")
            if data['results']:
                print(f"Top result: {data['results'][0]['drug_name']} - {data['results'][0]['section_title']}")
                print(f"Similarity: {data['results'][0]['similarity_score']:.4f}")


async def test_chat():
    """Test chat endpoint"""
    print("\n=== Testing Chat Endpoint ===")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/chat/ask",
            json={
                "message": "What are the common side effects of GLP-1 medications?",
                "conversation_id": None,
                "drug_id": None
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response preview: {data['response'][:200]}...")
            print(f"Citations: {len(data['citations'])}")


async def test_platform_analytics():
    """Test platform analytics"""
    print("\n=== Testing Platform Analytics ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/analytics/platform")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Total drugs: {data['total_drugs']}")
            print(f"Total sections: {data['total_sections']}")
            print(f"Total embeddings: {data['total_embeddings']}")
            print(f"Unique manufacturers: {data['unique_manufacturers']}")


async def test_drug_analytics():
    """Test drug analytics"""
    print("\n=== Testing Drug Analytics ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/analytics/drug/1")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Drug: {data['drug_name']}")
            print(f"Sections: {data['section_count']}")
            print(f"Chunks: {data['chunk_count']}")
            print(f"Avg chunk size: {data['avg_chunk_size']} chars")


async def test_compare_drugs():
    """Test drug comparison"""
    print("\n=== Testing Drug Comparison ===")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/analytics/compare",
            json={
                "drug_ids": [1, 2],
                "comparison_type": "side_by_side",
                "attributes": ["indications", "warnings"]
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Comparing {len(data['comparisons'])} drugs")
            print(f"Similarities: {len(data['similarities'])}")
            print(f"Differences: {len(data['differences'])}")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("FastAPI Endpoint Tests")
    print("=" * 60)
    
    tests = [
        test_health,
        test_get_drugs,
        test_get_drug_by_id,
        test_semantic_search,
        test_chat,
        test_platform_analytics,
        test_drug_analytics,
        test_compare_drugs
    ]
    
    for test in tests:
        try:
            await test()
        except Exception as e:
            print(f"\n❌ Error in {test.__name__}: {str(e)}")
    
    print("\n" + "=" * 60)
    print("Tests Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
