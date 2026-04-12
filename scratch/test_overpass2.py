import requests
import json

# Test with New Delhi and different area search
print("=== Test 1: Nominatim search for Delhi area ID ===")
try:
    r = requests.get("https://nominatim.openstreetmap.org/search?q=Delhi+India&format=json&limit=5",
                     headers={"User-Agent": "LeadsFlow/1.0"}, timeout=10)
    print(f"Status: {r.status_code}")
    data = r.json()
    for d in data[:3]:
        print(f"  {d.get('display_name','?')[:60]} | osm_id={d.get('osm_id')} type={d.get('osm_type')}")
except Exception as e:
    print(f"ERROR: {e}")

# Test 2: Overpass with bbox (Delhi coordinates)
print("\n=== Test 2: Overpass API with bbox (Delhi restaurants) ===")
# Delhi bbox: 28.4, 76.8, 28.9, 77.4
query = """[out:json][timeout:30];
node["amenity"="restaurant"](28.4,76.8,28.9,77.4);
out body 15;
"""
try:
    r = requests.post("https://overpass-api.de/api/interpreter", data={"data": query}, timeout=35)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        elements = data.get('elements', [])
        print(f"Results: {len(elements)}")
        for e in elements[:10]:
            tags = e.get('tags', {})
            name = tags.get('name', tags.get('name:en', 'Unknown'))
            phone = tags.get('phone', tags.get('contact:phone', 'N/A'))
            website = tags.get('website', 'None')
            print(f"  {name} | Phone: {phone} | Web: {website}")
    else:
        print(f"Response: {r.text[:200]}")
except Exception as e:
    print(f"ERROR: {e}")

# Test 3: Overpass with shops in Delhi bbox
print("\n=== Test 3: Overpass shops in Delhi bbox ===")
query3 = """[out:json][timeout:30];
node["shop"](28.4,76.8,28.9,77.4);
out body 15;
"""
try:
    r = requests.post("https://overpass-api.de/api/interpreter", data={"data": query3}, timeout=35)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        elements = data.get('elements', [])
        print(f"Results: {len(elements)}")
        for e in elements[:10]:
            tags = e.get('tags', {})
            name = tags.get('name', 'Unknown')
            shop_type = tags.get('shop', '?')
            phone = tags.get('phone', 'N/A')
            print(f"  {name} ({shop_type}) | Phone: {phone}")
    else:
        print(f"Response: {r.text[:200]}")
except Exception as e:
    print(f"ERROR: {e}")
