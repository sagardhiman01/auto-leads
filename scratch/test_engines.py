import requests
import time
import sys

def test_engine(name, url):
    print(f"Testing {name} ({url})...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    try:
        start = time.time()
        r = requests.get(url, headers=headers, timeout=10)
        duration = time.time() - start
        print(f"  Result: Status {r.status_code} in {duration:.2f}s")
        if r.status_code == 200:
            return True
    except Exception as e:
        print(f"  Result: FAILED - {e}")
    return False

if __name__ == "__main__":
    targets = [
        ("Google", "https://www.google.com/search?q=test"),
        ("Bing", "https://www.bing.com/search?q=test"),
        ("DuckDuckGo", "https://html.duckduckgo.com/html/?q=test"),
        ("Yahoo", "https://search.yahoo.com/search?p=test"),
        ("YellowPages", "https://www.yellowpages.com/search?search_terms=test&geo_location_terms=Mumbai")
    ]
    
    results = {}
    for name, url in targets:
        results[name] = test_engine(name, url)
    
    print("\n--- TEST SUMMARY ---")
    for name, ok in results.items():
        print(f"{name}: {'✅ OK' if ok else '❌ BLOCKED'}")
