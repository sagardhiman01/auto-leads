import sqlite3
import os
import sys
import re
import random
import csv
import time

# Engine v38.1: THE ABSOLUTE TITAN (FIXED FILTER)
# ROOT CAUSE: v38.0 found 10 results on Render but filter rejected ALL of them
# because they were business websites (not platform listings).
# FIX: Accept ALL search results as leads. Score platform ones higher.
# The user wants LEADS to contact - not just platform-only businesses.

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_STORE = "/data" if os.path.exists("/data") else PROJECT_ROOT
DB_PRODUCTION_PATH = os.path.join(DATA_STORE, "leads_production_v3.db")

PLATFORM_DOMAINS = ["facebook.com", "instagram.com", "zomato.com", "swiggy.com", 
                     "justdial.com", "linkedin.com", "indiamart.com", "magicbricks.com", "99acres.com"]

# Regex to block languages and junk navigation
GARBAGE_RE = re.compile(
    r"^(hindi|marathi|punjabi|tamil|telugu|bengali|urdu|english|gujarati|kannada|malayalam|"
    r"assamese|odia|हिंदी|मराठी|বাংলা|ਪੰਜਾਬੀ|اردو|தமிழ்|తెలుగు|ગુજરાતી|ಕನ್ನಡ|"
    r"മലയാളം|অসমীয়া|ଓଡ଼ିଆ)$", re.IGNORECASE)

# Sites that are NOT businesses (news, wikipedia, etc.)
SKIP_DOMAINS = ["youtube.com", "wikipedia.org", "news18.com", "indianexpress.com",
                "timesofindia.com", "ndtv.com", "google.com", "bing.com", 
                "economictimes.com", "businesstoday.in", "moneycontrol.com",
                "hindustantimes.com", "thehindu.com", "mynation.com", "thepatriot.in"]

def safe_print(msg):
    try:
        print(msg, flush=True)
    except:
        print(msg.encode('ascii', 'ignore').decode(), flush=True)

def is_junk_name(name):
    n = name.strip()
    if len(n) < 4: return True
    if GARBAGE_RE.match(n): return True
    nl = n.lower()
    if any(j in nl for j in ["login", "signup", "privacy", "terms", "career", 
                              "cookie", "password", "captcha", "advertise"]): return True
    return False

def extract_name(title):
    name = title.split('|')[0].split(' - ')[0].split('::')[0].strip()
    for suffix in ['Facebook', 'Instagram', 'LinkedIn', 'Zomato', 'JustDial', '...']:
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip(' -|:')
    return name.strip()

def is_news_site(url):
    return any(d in url.lower() for d in SKIP_DOMAINS)

def is_platform(url):
    return any(d in url.lower() for d in PLATFORM_DOMAINS)

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
                    "INSERT OR REPLACE INTO leads_3 VALUES (NULL,?,?,?,?,?,?,?,?,?)",
                    (niche, location, lead["Name"], lead.get("Website","None"), "None", "None",
                     lead.get("Social","None"), lead.get("Score", 8.5), "v38.1"))
                conn.commit()
        except: pass

def hunt(niche, location, target):
    try:
        # Fix common typos
        if "state" in niche.lower() and "real" in niche.lower():
            niche = "Real Estate"
        
        safe_print(f">>> Absolute Titan v38.1 Active. Target: {target} for '{niche}' in {location}")
        
        # Import ddgs inside function for clean error reporting
        from ddgs import DDGS
        
        # Multiple queries for maximum coverage
        queries = [
            f"{niche} {location} India",
            f"{niche} near {location} facebook instagram",
            f"best {niche} in {location} India",
            f"top {niche} {location} justdial zomato",
            f"{niche} {location} India linkedin indiamart",
        ]
        
        raw = []
        seen_urls = set()
        
        for qi, query in enumerate(queries):
            safe_print(f"DEBUG: Query {qi+1}/{len(queries)}: {query[:40]}...")
            try:
                results = DDGS().text(query, max_results=15)
                for r in results:
                    url = r.get('href', '')
                    if url not in seen_urls:
                        seen_urls.add(url)
                        raw.append(r)
                safe_print(f"DEBUG: Got {len(results)} from query {qi+1}")
            except Exception as e:
                safe_print(f"DEBUG: Query {qi+1} err: {str(e)[:50]}")
            time.sleep(random.uniform(2, 4))
        
        safe_print(f"DEBUG: Total raw: {len(raw)}")
        
        # FILTER: Accept ALL results except news sites and junk names
        leads = []
        seen_names = set()
        vault = Vault()
        
        for r in raw:
            if len(leads) >= target: break
            
            title = r.get('title', '')
            url = r.get('href', '')
            
            # Skip news/media sites
            if is_news_site(url): continue
            
            # Extract and validate name
            name = extract_name(title)
            if is_junk_name(name): continue
            if name.lower() in seen_names: continue
            seen_names.add(name.lower())
            
            # Score: Platform listings get higher score
            if is_platform(url):
                score = 9.8
                social = url
                website = "None"
            else:
                score = 8.5
                social = "None"
                website = url
            
            lead = {"Name": name, "Social": social, "Website": website, "Score": score}
            vault.save(niche, location, lead)
            leads.append(lead)
            safe_print(f"PROGRESS:{len(leads)}:{target}:SECURED: {name[:25].encode('ascii','ignore').decode()}")
        
        safe_print(f">>> Session Complete. {len(leads)} prospects secured.")
        return leads
        
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
                    "WhatsApp": "None",
                    "Email ID": "None",
                    "Social": d.get("Social", "None"),
                    "Score": d["Score"],
                    "Source": "v38.1"
                })
    
    safe_print("DONE")
