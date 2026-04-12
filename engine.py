import sqlite3
import os
import sys
import re
import requests
import random
import csv
import time
from urllib.parse import urlparse

# Engine v38.0: THE ABSOLUTE TITAN (DDGS DISCOVERY)
# ROOT CAUSE FIX: Bing/Google/DDG HTML scrapers ALL return CAPTCHA or 0 results.
# Solution: Use the `ddgs` Python library which uses DuckDuckGo's internal API.
# This is the ONLY reliable free search method that works on both local & Render.

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_STORE = "/data" if os.path.exists("/data") else PROJECT_ROOT
DB_PRODUCTION_PATH = os.path.join(DATA_STORE, "leads_production_v3.db")

PLATFORM_DOMAINS = ["facebook.com", "instagram.com", "zomato.com", "swiggy.com", 
                     "justdial.com", "linkedin.com", "indiamart.com", "magicbricks.com", "99acres.com"]

# Regex to block languages and junk
GARBAGE_RE = re.compile(
    r"^(hindi|marathi|punjabi|tamil|telugu|bengali|urdu|english|gujarati|kannada|malayalam|"
    r"assamese|odia|हिंदी|मराठी|বাংলা|ਪੰਜਾਬੀ|اردو|தமிழ்|తెలుగు|ગુજરાતી|ಕನ್ನಡ|"
    r"മലയാളം|অসমীয়া|ଓଡ଼ିଆ)$", re.IGNORECASE)

JUNK_KEYWORDS = ["login", "signup", "privacy", "terms", "career", "advertise",
                  "about us", "contact us", "cookie", "password", "captcha"]

def safe_print(msg):
    """Unicode-safe print for Render logs"""
    try:
        print(msg, flush=True)
    except:
        print(msg.encode('ascii', 'ignore').decode(), flush=True)

def is_junk(name):
    """Check if a name is garbage (language, nav link, too short)"""
    n = name.strip()
    if len(n) < 4: return True
    if GARBAGE_RE.match(n): return True
    nl = n.lower()
    if any(j in nl for j in JUNK_KEYWORDS): return True
    return False

def extract_business_name(title):
    """Extract clean business name from a search result title"""
    # Remove common suffixes
    name = title.split('|')[0].split(' - ')[0].split('::')[0].strip()
    # Remove "... Facebook", "... Instagram" etc from end
    for p in ['Facebook', 'Instagram', 'LinkedIn', 'Zomato', '...']:
        if name.endswith(p):
            name = name[:-len(p)].strip(' -|')
    return name.strip()

def is_platform_url(url):
    """Check if URL belongs to a social/listing platform"""
    return any(p in url.lower() for p in PLATFORM_DOMAINS)

def has_own_website(url):
    """Check if URL is a business's OWN website (not a platform listing)"""
    if not url: return False
    return not is_platform_url(url) and not any(x in url.lower() for x in 
        ['youtube.com', 'wikipedia.org', 'news18.com', 'indianexpress.com', 
         'timesofindia.com', 'ndtv.com', 'google.com', 'bing.com'])

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
                conn.execute(
                    "INSERT OR REPLACE INTO leads_3 (niche, location, company_name, website, phone, email, social, score, source) VALUES (?,?,?,?,?,?,?,?,?)",
                    (niche, location, lead["Name"], "None", "None", "None", 
                     lead.get("Social","None"), lead.get("Score", 8.5), "v38.0"))
                conn.commit()
        except: pass

def discover_leads(niche, location, target):
    """Use DDGS library for reliable search that works everywhere"""
    from ddgs import DDGS
    
    safe_print(f"DEBUG: DDGS Discovery Engine Active for '{niche}' in {location}...")
    
    # Multiple search queries to maximize coverage
    queries = [
        f"{niche} {location} India",
        f"{niche} near {location} facebook instagram",
        f"best {niche} in {location} India",
        f"top {niche} {location} justdial zomato",
        f"{niche} {location} India linkedin indiamart",
    ]
    
    raw_results = []
    seen_urls = set()
    
    for qi, query in enumerate(queries):
        safe_print(f"DEBUG: Query {qi+1}/{len(queries)}: {query[:40]}...")
        try:
            results = DDGS().text(query, max_results=15)
            for r in results:
                url = r.get('href', '')
                if url in seen_urls: continue
                seen_urls.add(url)
                raw_results.append({
                    'title': r.get('title', ''),
                    'url': url,
                    'body': r.get('body', ''),
                })
            safe_print(f"DEBUG: Got {len(results)} results from query {qi+1}")
        except Exception as e:
            safe_print(f"DEBUG: Query {qi+1} error: {str(e)[:50]}")
        
        # Small delay between queries
        time.sleep(random.uniform(2, 4))
    
    safe_print(f"DEBUG: Total raw results: {len(raw_results)}")
    return raw_results

def filter_and_score(raw_results, niche, location, target):
    """Filter raw results to find genuine B2B leads without websites"""
    leads = []
    seen_names = set()
    
    for r in raw_results:
        if len(leads) >= target: break
        
        title = r['title']
        url = r['url']
        body = r['body']
        
        # Extract business name
        name = extract_business_name(title)
        if is_junk(name): continue
        if name.lower() in seen_names: continue
        
        # Determine if this is a platform listing (GOOD) or own website (BAD)
        url_is_platform = is_platform_url(url)
        url_is_own_site = has_own_website(url)
        
        # Score based on source
        if url_is_platform:
            # JACKPOT: Business on platform = needs a website
            score = 9.8
            social = url
            source_type = "Platform"
        elif url_is_own_site:
            # SKIP: Business already has a website
            continue
        else:
            # News/directory listing - might be useful, lower score
            score = 7.5
            social = "None"
            source_type = "Index"
        
        seen_names.add(name.lower())
        leads.append({
            "Name": name,
            "Social": social,
            "Score": score,
            "Source": source_type,
        })
        safe_print(f"PROGRESS:{len(leads)}:{target}:SECURED: {name[:25].encode('ascii','ignore').decode()}")
    
    return leads

def hunt(niche, location, target):
    """Main hunt function"""
    try:
        # Fix common typos
        if "state" in niche.lower() and "real" in niche.lower():
            niche = "Real Estate"
        
        safe_print(f">>> Absolute Titan v38.0 Active. Target: {target} leads for '{niche}' in {location}")
        
        # Phase 1: Discover
        raw = discover_leads(niche, location, target)
        
        # Phase 2: Filter & Score
        leads = filter_and_score(raw, niche, location, target)
        
        # Phase 3: Save to vault
        vault = Vault()
        for lead in leads:
            vault.save(niche, location, lead)
        
        safe_print(f">>> Session Complete. {len(leads)} genuine prospects secured.")
        return leads
        
    except Exception as e:
        safe_print(f"FATAL_ERROR: {str(e)}")
        return []

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: engine.py <niche> <location> <count>", flush=True)
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
                    "Website": "None",
                    "WhatsApp": "None",
                    "Email ID": "None",
                    "Social": d.get("Social", "None"),
                    "Score": d["Score"],
                    "Source": d.get("Source", "v38.0")
                })
    
    print("DONE", flush=True)
