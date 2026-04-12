import requests
import time

# Try multiple Overpass endpoints
endpoints = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

q = """[out:json][timeout:30];
(
  node["name"~"real estate|property|realty",i](28.40,76.80,28.90,77.40);
  way["name"~"real estate|property|realty",i](28.40,76.80,28.90,77.40);
  node["office"~"estate_agent|property",i](28.40,76.80,28.90,77.40);
  way["office"~"estate_agent|property",i](28.40,76.80,28.90,77.40);
);
out body 30;
"""

for ep in endpoints:
    print(f"\nTrying {ep}...")
    try:
        r = requests.post(ep, data={"data": q}, timeout=35)
        print(f"Status={r.status_code}")
        if r.status_code == 200:
            data = r.json()
            elems = data.get("elements", [])
            print(f"Results={len(elems)}")
            for e in elems[:15]:
                tags = e.get("tags", {})
                name = tags.get("name", "?")
                phone = tags.get("phone", tags.get("contact:phone", "-"))
                print(f"  {name[:50]} | Ph: {phone}")
            break
    except Exception as e:
        print(f"Error: {str(e)[:60]}")
    time.sleep(3)
