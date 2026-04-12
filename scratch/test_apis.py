import requests
import json

# Test 1: DuckDuckGo Instant Answer API (fully free, no auth needed)
print("=== Test 1: DDG Instant API ===")
r = requests.get('https://api.duckduckgo.com/?q=Real+Estate+Delhi+India&format=json', 
                  headers={'User-Agent':'Mozilla/5.0'}, timeout=10)
print(f"DDG API: Status={r.status_code}")
data = r.json()
related = data.get('RelatedTopics', [])
print(f"Related Topics: {len(related)}")
for t in related[:5]:
    if isinstance(t, dict):
        txt = t.get("Text", "?")[:80]
        print(f"  -> {txt}")

# Test 2: Google Custom Search (free tier: 100 queries/day)
print("\n=== Test 2: Google Places approach ===")

# Test 3: Use Python duckduckgo-search library
print("\n=== Test 3: duckduckgo_search lib ===")
try:
    from duckduckgo_search import DDGS
    with DDGS() as ddgs:
        results = list(ddgs.text("Real Estate agents Delhi India", max_results=10))
        print(f"DDGS results: {len(results)}")
        for r in results[:5]:
            print(f"  -> {r['title'][:60]}")
            print(f"     {r['href'][:80]}")
except ImportError:
    print("duckduckgo_search not installed. Testing pip install...")
except Exception as e:
    print(f"DDGS error: {e}")
