from ddgs import DDGS

# Test broader queries for lead quantity
queries = [
    "Real Estate agents Delhi India",
    "property dealers Delhi Facebook Instagram",
    "Real Estate Delhi justdial indiamart",
]

seen = set()
for q in queries:
    results = DDGS().text(q, max_results=15)
    for r in results:
        title = r['title'][:50]
        url = r['href'][:70]
        if title not in seen:
            seen.add(title)
            print(f"{title}")
            print(f"  {url}")
            print()

print(f"\n=== TOTAL UNIQUE: {len(seen)} ===")
