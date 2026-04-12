import requests
import json

# Test 1: Overpass API (OpenStreetMap) - Free, no auth, no IP blocking
print("=== Test 1: Overpass API (Restaurants in Delhi) ===")
query = """
[out:json][timeout:25];
area["name"="Delhi"]["admin_level"="2"]->.a;
node["amenity"="restaurant"](area.a);
out body 20;
"""
try:
    r = requests.post("https://overpass-api.de/api/interpreter", data={"data": query}, timeout=30)
    print(f"Status: {r.status_code}")
    data = r.json()
    elements = data.get('elements', [])
    print(f"Results: {len(elements)}")
    for e in elements[:10]:
        tags = e.get('tags', {})
        name = tags.get('name', tags.get('name:en', '?'))
        cuisine = tags.get('cuisine', 'N/A')
        phone = tags.get('phone', tags.get('contact:phone', 'N/A'))
        website = tags.get('website', tags.get('contact:website', 'None'))
        fb = tags.get('contact:facebook', 'None')
        print(f"  {name} | Cuisine: {cuisine} | Phone: {phone} | Website: {website} | FB: {fb}")
except Exception as e:
    print(f"ERROR: {e}")

# Test 2: Overpass API (Real Estate in Delhi)
print("\n=== Test 2: Overpass API (Real Estate in Delhi) ===")
query2 = """
[out:json][timeout:25];
area["name"="Delhi"]["admin_level"="2"]->.a;
node["office"="estate_agent"](area.a);
out body 20;
"""
try:
    r = requests.post("https://overpass-api.de/api/interpreter", data={"data": query2}, timeout=30)
    print(f"Status: {r.status_code}")
    data = r.json()
    elements = data.get('elements', [])
    print(f"Results: {len(elements)}")
    for e in elements[:10]:
        tags = e.get('tags', {})
        name = tags.get('name', tags.get('name:en', '?'))
        phone = tags.get('phone', tags.get('contact:phone', 'N/A'))
        website = tags.get('website', 'None')
        print(f"  {name} | Phone: {phone} | Website: {website}")
except Exception as e:
    print(f"ERROR: {e}")

# Test 3: Broader search with shop/office tags
print("\n=== Test 3: Overpass API (All shops in Delhi, first 20) ===")
query3 = """
[out:json][timeout:25];
area["name"="Delhi"]["admin_level"="2"]->.a;
(
  node["shop"](area.a);
  node["office"](area.a);
);
out body 20;
"""
try:
    r = requests.post("https://overpass-api.de/api/interpreter", data={"data": query3}, timeout=30)
    print(f"Status: {r.status_code}")
    data = r.json()
    elements = data.get('elements', [])
    print(f"Results: {len(elements)}")
    for e in elements[:10]:
        tags = e.get('tags', {})
        name = tags.get('name', '?')
        shop_type = tags.get('shop', tags.get('office', '?'))
        phone = tags.get('phone', tags.get('contact:phone', 'N/A'))
        website = tags.get('website', 'None')
        print(f"  {name} ({shop_type}) | Phone: {phone} | Website: {website}")
except Exception as e:
    print(f"ERROR: {e}")
