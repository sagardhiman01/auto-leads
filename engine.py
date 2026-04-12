import sqlite3
import os
import sys
import re
import requests
import random
import csv
import time
import json

# Engine v39.1: THE IMMORTAL TITAN (ENRICHED EDITION)
# Discovery: OpenStreetMap Overpass API (works from ANY IP)
# Enrichment: DDGS contact search (graceful fallback if blocked on cloud)
# PRIORITY: Businesses WITH existing contact data in OSM are listed first.

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_STORE = "/data" if os.path.exists("/data") else PROJECT_ROOT
DB_PRODUCTION_PATH = os.path.join(DATA_STORE, "leads_production_v3.db")

PHONE_RE = re.compile(r'(\+91[\s-]?\d{5}[\s-]?\d{5}|\b0\d{2,4}[\s-]?\d{6,8}\b)')
EMAIL_RE = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')

NICHE_MAP = {
    "restaurant": {"amenity": "restaurant"},
    "cafe": {"amenity": "cafe"},
    "hotel": {"tourism": "hotel"},
    "gym": {"leisure": "fitness_centre"},
    "salon": {"shop": "beauty"},
    "bakery": {"shop": "bakery"},
    "pharmacy": {"amenity": "pharmacy"},
    "hospital": {"amenity": "hospital"},
    "school": {"amenity": "school"},
    "clinic": {"amenity": "clinic"},
    "dentist": {"amenity": "dentist"},
    "real estate": {"office": "estate_agent"},
    "lawyer": {"office": "lawyer"},
    "insurance": {"office": "insurance"},
    "travel": {"office": "travel_agent"},
    "jewellery": {"shop": "jewelry"}, "jewelry": {"shop": "jewelry"},
    "clothing": {"shop": "clothes"},
    "electronics": {"shop": "electronics"},
    "supermarket": {"shop": "supermarket"},
    "car repair": {"shop": "car_repair"},
    "automobile": {"shop": "car"},
    "furniture": {"shop": "furniture"},
    "mobile": {"shop": "mobile_phone"},
    "grocery": {"shop": "convenience"},
    "florist": {"shop": "florist"},
    "pet": {"shop": "pet"},
    "laundry": {"shop": "laundry"},
    "tailor": {"shop": "tailor"},
    "digital marketing": {"office": "company"},
    "agency": {"office": "company"},
    "it": {"office": "it"},
    "doctor": {"amenity": "doctors"},
}

CITY_BBOX = {
    "delhi": (28.40, 76.80, 28.90, 77.40),
    "new delhi": (28.40, 76.80, 28.90, 77.40),
    "mumbai": (18.85, 72.75, 19.30, 73.05),
    "bangalore": (12.85, 77.45, 13.10, 77.75),
    "bengaluru": (12.85, 77.45, 13.10, 77.75),
    "chennai": (12.90, 80.10, 13.20, 80.35),
    "kolkata": (22.45, 88.25, 22.65, 88.45),
    "hyderabad": (17.30, 78.35, 17.55, 78.60),
    "pune": (18.45, 73.75, 18.65, 73.95),
    "jaipur": (26.80, 75.70, 27.00, 75.90),
    "ahmedabad": (22.95, 72.50, 23.15, 72.70),
    "lucknow": (26.75, 80.85, 26.95, 81.05),
    "chandigarh": (30.65, 76.70, 30.80, 76.85),
    "noida": (28.50, 77.30, 28.65, 77.45),
    "gurgaon": (28.40, 76.95, 28.55, 77.10),
    "gurugram": (28.40, 76.95, 28.55, 77.10),
    "indore": (22.65, 75.80, 22.80, 75.95),
    "bhopal": (23.20, 77.35, 23.35, 77.50),
    "nagpur": (21.10, 79.00, 21.20, 79.15),
    "surat": (21.15, 72.75, 21.25, 72.90),
    "patna": (25.55, 85.05, 25.70, 85.25),
    "kochi": (9.90, 76.20, 10.05, 76.35),
    "agra": (27.10, 77.95, 27.25, 78.10),
    "varanasi": (25.26, 82.95, 25.38, 83.05),
    "amritsar": (31.58, 74.80, 31.70, 74.92),
    "dehradun": (30.25, 77.95, 30.40, 78.15),
    "roorkee": (29.82, 77.85, 29.92, 77.92),
}

GARBAGE_RE = re.compile(
    r"^(hindi|marathi|punjabi|tamil|telugu|bengali|urdu|english|gujarati|kannada|malayalam|"
    r"assamese|odia|हिंदी|मराठी|বাংলা|ਪੰਜਾਬੀ|اردو|தமிழ்|తెలుగు|ગુજરાતી|ಕನ್ನಡ|"
    r"മലయാളം|অসমীয়া|ଓଡ଼ିଆ)$", re.IGNORECASE)

def safe_print(msg):
    try: print(msg, flush=True)
    except: print(msg.encode('ascii', 'ignore').decode(), flush=True)

def is_junk(name):
    n = name.strip()
    if len(n) < 3: return True
    if GARBAGE_RE.match(n): return True
    if n.lower() in ["unknown", "none", "n/a", "?"]: return True
    return False

def get_bbox(location):
    return CITY_BBOX.get(location.lower().strip(), None)

def get_osm_tags(niche):
    nl = niche.lower().strip()
    if nl in NICHE_MAP: return NICHE_MAP[nl]
    for key, tags in NICHE_MAP.items():
        if key in nl or nl in key: return tags
    return {"shop": nl.replace(' ', '_')}

class Vault:
    def __init__(self):
        try:
            with sqlite3.connect(DB_PRODUCTION_PATH) as conn:
                conn.execute("""CREATE TABLE IF NOT EXISTS leads_3 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    niche TEXT, location TEXT, company_name TEXT,
                    website TEXT, phone TEXT, email TEXT,
                    social TEXT, score REAL, source TEXT,
                    UNIQUE(company_name, location))""")
                conn.commit()
        except: pass

    def save(self, niche, location, lead):
        try:
            with sqlite3.connect(DB_PRODUCTION_PATH) as conn:
                conn.execute("INSERT OR REPLACE INTO leads_3 VALUES (NULL,?,?,?,?,?,?,?,?,?)",
                    (niche, location, lead["Name"], lead.get("Website","None"),
                     lead.get("Phone","None"), lead.get("Email","None"),
                     lead.get("Social","None"), lead.get("Score",8.5), "v39.1"))
                conn.commit()
        except: pass

def discover_overpass(niche, location, target):
    safe_print(f"DEBUG: Overpass Discovery for '{niche}' in {location}...")
    bbox = get_bbox(location)
    osm_tags = get_osm_tags(niche)
    
    if not bbox:
        try:
            r = requests.get(
                f"https://nominatim.openstreetmap.org/search?q={location}+India&format=json&limit=1",
                headers={"User-Agent": "LeadsFlow/1.0"}, timeout=10)
            if r.status_code == 200 and r.json():
                bb = r.json()[0].get('boundingbox', [])
                if len(bb) == 4:
                    bbox = (float(bb[0]), float(bb[2]), float(bb[1]), float(bb[3]))
        except: pass
    
    if not bbox:
        bbox = (28.40, 76.80, 28.90, 77.40)  # Delhi default
    
    tag_key = list(osm_tags.keys())[0]
    tag_val = list(osm_tags.values())[0]
    limit = max(target * 4, 40)
    
    query = f"""[out:json][timeout:30];
(
  node["{tag_key}"="{tag_val}"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
  way["{tag_key}"="{tag_val}"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
);
out body {limit};
"""
    results = []
    try:
        r = requests.post("https://overpass-api.de/api/interpreter", data={"data": query}, timeout=35)
        if r.status_code == 200:
            elements = r.json().get('elements', [])
            safe_print(f"DEBUG: Overpass returned {len(elements)} POIs")
            
            # Sort: businesses WITH contacts first
            has_contact = []
            no_contact = []
            for e in elements:
                tags = e.get('tags', {})
                name = tags.get('name', tags.get('name:en', ''))
                if not name or is_junk(name): continue
                
                phone = tags.get('phone', tags.get('contact:phone', 'None'))
                website = tags.get('website', tags.get('contact:website', 'None'))
                email = tags.get('email', tags.get('contact:email', 'None'))
                facebook = tags.get('contact:facebook', 'None')
                
                # Auto-generate Google Maps link for easy contact lookup
                from urllib.parse import quote
                maps_link = f"https://www.google.com/maps/search/{quote(name + ' ' + location)}"
                
                # Use facebook/maps as social link
                social = facebook if facebook != 'None' else maps_link
                
                lead = {"Name": name, "Phone": phone, "Website": website,
                        "Email": email, "Social": social, "Score": 9.8}
                
                if phone != 'None' or email != 'None' or website != 'None':
                    has_contact.append(lead)
                else:
                    no_contact.append(lead)
            
            results = has_contact + no_contact
        else:
            safe_print(f"DEBUG: Overpass status {r.status_code}")
    except Exception as e:
        safe_print(f"DEBUG: Overpass error: {str(e)[:60]}")
    
    return results

def enrich_contact(name, location):
    """Try to find contact info using DDGS search"""
    phone, email, website, social = "None", "None", "None", "None"
    try:
        from ddgs import DDGS
        results = DDGS().text(f"{name} {location} contact phone number", max_results=5)
        for r in results:
            snippet = r.get('body', '') + ' ' + r.get('title', '')
            url = r.get('href', '')
            
            if phone == "None":
                phones = PHONE_RE.findall(snippet)
                if phones: phone = phones[0]
            
            if email == "None":
                emails = EMAIL_RE.findall(snippet)
                if emails: email = emails[0]
            
            if website == "None" and url:
                skip = ['facebook','instagram','youtube','wikipedia','google','bing']
                if not any(s in url.lower() for s in skip):
                    website = url
            
            if social == "None" and url:
                platforms = ['facebook.com', 'instagram.com', 'linkedin.com']
                if any(p in url.lower() for p in platforms):
                    social = url
    except:
        pass
    return phone, email, website, social

def hunt(niche, location, target):
    try:
        if "state" in niche.lower() and "real" in niche.lower():
            niche = "Real Estate"
        
        safe_print(f">>> Immortal Titan v39.1 Active. Target: {target} for '{niche}' in {location}")
        
        # Phase 1: Overpass Discovery
        leads_raw = discover_overpass(niche, location, target)
        safe_print(f"DEBUG: Overpass found {len(leads_raw)} leads")
        
        # Phase 2: DDGS Fallback if Overpass too few
        if len(leads_raw) < target:
            safe_print(f"DEBUG: DDGS Fallback needed ({len(leads_raw)} < {target})...")
            try:
                from ddgs import DDGS
                queries = [f"{niche} {location} India", f"best {niche} in {location}"]
                seen = set(l["Name"].lower() for l in leads_raw)
                for q in queries:
                    try:
                        hits = DDGS().text(q, max_results=15)
                        for h in hits:
                            name = h['title'].split('|')[0].split('-')[0].strip()
                            if not is_junk(name) and name.lower() not in seen:
                                seen.add(name.lower())
                                leads_raw.append({"Name": name, "Website": h.get('href','None'), "Score": 8.5})
                    except: pass
                    time.sleep(2)
            except: pass
            safe_print(f"DEBUG: Total after fallback: {len(leads_raw)}")
        
        # Phase 3: Enrich contacts for leads missing info
        vault = Vault()
        final = []
        seen = set()
        
        for lead in leads_raw:
            if len(final) >= target: break
            nk = lead["Name"].lower().strip()
            if nk in seen: continue
            seen.add(nk)
            
            # If no contact info from Overpass, try DDGS enrichment
            has_info = (lead.get("Phone","None") != "None" or 
                       lead.get("Email","None") != "None" or
                       lead.get("Website","None") != "None")
            
            if not has_info:
                safe_print(f"DEBUG: Enriching '{lead['Name'][:20]}'...")
                phone, email, website, social = enrich_contact(lead["Name"], location)
                lead["Phone"] = phone
                lead["Email"] = email
                lead["Website"] = website
                if social != "None": lead["Social"] = social
                time.sleep(random.uniform(2, 4))
            
            vault.save(niche, location, lead)
            final.append(lead)
            
            cname = lead['Name'][:20].encode('ascii','ignore').decode()
            cphone = lead.get('Phone','None')[:15]
            safe_print(f"PROGRESS:{len(final)}:{target}:SECURED: {cname} | Ph:{cphone}")
        
        safe_print(f">>> Session Complete. {len(final)} prospects secured.")
        return final
    except Exception as e:
        safe_print(f"FATAL_ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    if len(sys.argv) < 4:
        safe_print("Usage: engine.py <niche> <location> <count>")
        sys.exit(1)
    
    n, l, c = sys.argv[1], sys.argv[2], int(sys.argv[3])
    data = hunt(n, l, c)
    
    if data:
        csv_path = os.path.join(PROJECT_ROOT, "leads.csv")
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            fields = ["Company Name", "Website", "WhatsApp", "Email ID", "Social", "Score", "Source"]
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for d in data:
                writer.writerow({
                    "Company Name": d["Name"],
                    "Website": d.get("Website", "None"),
                    "WhatsApp": d.get("Phone", "None"),
                    "Email ID": d.get("Email", "None"),
                    "Social": d.get("Social", "None"),
                    "Score": d["Score"],
                    "Source": "v39.1"
                })
    safe_print("DONE")
