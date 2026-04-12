import requests
from bs4 import BeautifulSoup
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9'
}

# Test 1: SearXNG JSON API (public, no captcha, no rate limiting)
searx_instances = [
    "https://search.inetol.net",
    "https://searx.be",
    "https://search.sapti.me",
]

for instance in searx_instances:
    try:
        url = f"{instance}/search?q=Real+Estate+agents+Delhi+India&format=json"
        r = requests.get(url, headers=headers, timeout=10)
        print(f"SearX [{instance}]: Status={r.status_code}")
        if r.status_code == 200:
            data = r.json()
            results = data.get('results', [])
            print(f"  Found {len(results)} results")
            for item in results[:5]:
                title = item.get('title', '?')[:60]
                link = item.get('url', '?')[:80]
                print(f"  -> {title}")
                print(f"     {link}")
            if results:
                print(f"\n*** WORKING INSTANCE: {instance} ***")
                break
    except Exception as e:
        print(f"SearX [{instance}]: ERROR - {str(e)[:80]}")

# Test 2: Bing with different selectors
print("\n--- Testing Bing with broader selectors ---")
try:
    r = requests.get('https://www.bing.com/search?q=Real+Estate+agents+Delhi+India', headers=headers, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')
    # Try many different selectors
    for sel in ['li.b_algo', '.b_algo', '#b_results li', 'li.b_algo h2', 'h2 a', 'cite']:
        found = soup.select(sel)
        print(f"  Selector '{sel}': {len(found)} matches")
        if found:
            for f in found[:3]:
                print(f"    -> {f.text[:80]}")
except Exception as e:
    print(f"Bing ERROR: {e}")

# Test 3: DuckDuckGo Lite  
print("\n--- Testing DDG Lite ---")
try:
    r = requests.get('https://lite.duckduckgo.com/lite/?q=Real+Estate+agents+Delhi+India', headers=headers, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')
    links = soup.select('a.result-link')
    results_class_a = soup.select('a')
    tds = soup.select('td')
    print(f"DDG Lite: Status={r.status_code} Links={len(links)} All_a={len(results_class_a)} TDs={len(tds)}")
    # Try to find result snippets
    result_snippets = soup.find_all('td', class_='result-snippet')
    print(f"  Snippets: {len(result_snippets)}")
    for s in result_snippets[:3]:
        print(f"  -> {s.text[:80]}")
except Exception as e:
    print(f"DDG Lite ERROR: {e}")
