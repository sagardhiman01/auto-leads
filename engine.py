import sqlite3
import os
import sys
import re
import logging
import requests
from bs4 import BeautifulSoup
import random
import csv
import time
import base64
from urllib.parse import urlparse, parse_qs

# Engine v32.2: THE OMNI TITAN GHOUL (UNIVERSAL RESILIENCE)
# Designed for 100% stability on Cloud IPs using Multi-Mirror Fallback.
# Feature 1: Unicode-Safe Core (Handling Indian business names without crashes).
# Feature 2: Multi-Mirror Discovery (Bing + DuckDuckGo Proxy Sequential Probing).
# Feature 3: Strict B2B Filter (Collecting platforms ONLY, Rejecting existing websites).

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_STORE = "/data" if os.path.exists("/data") else PROJECT_ROOT
DB_PRODUCTION_PATH = os.path.join(DATA_STORE, "leads_production_v3.db")

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger("LEADSFLOW")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]

PLATFORM_DOMAINS = ["facebook.com", "instagram.com", "zomato.com", "swiggy.com", "justdial.com", "linkedin.com", "indiamart.com", "magicbricks.com", "99acres.com"]
GARBAGE_KEYWORDS = ["CRA Result", "Account", "Login", "Profile", "Privacy", "Manage", "Sign in", "Metadata", "Bing", "Search"]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9,en-US;q=0.8",
        "Referer": "https://www.google.com/"
    }

def safe_str(text):
    """Universal Unicode handling for stable logging and storage"""
    if not text: return ""
    return text.encode('ascii', 'ignore').decode('ascii').strip()

class Vault:
    def __init__(self):
        self.db_path = DB_PRODUCTION_PATH
        try:
            with sqlite3.connect(self.db_path) as conn:
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
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("INSERT OR REPLACE INTO leads_3 (niche, location, company_name, website, phone, email, social, score, source) VALUES (?,?,?,?,?,?,?,?,?)",
                             (niche, location, lead["Name"], "None", "None", lead.get("Email","None"), lead.get("Social","None"), lead.get("Score", 8.5), lead.get("Source", "v32.2")))
                conn.commit()
        except: pass

def probe_mirror(niche, location, target, mirror_type="bing"):
    """Multi-Mirror Discovery: Handles both Bing and DuckDuckGo proxies"""
    results = []
    print(f"DEBUG: Tapping {mirror_type.upper()} Mirror for '{niche}'...", flush=True)
    
    q = f'"{niche}" {location} India (facebook OR instagram OR justdial)'
    if mirror_type == "bing":
        url = f"https://www.bing.com/search?q={requests.utils.quote(q)}&cc=IN"
    else:
        url = f"https://duckduckgo.com/html/?q={requests.utils.quote(q)}"
        
    try:
        r = requests.get(url, headers=get_headers(), timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            # Look for H2/H3 headlines and result links
            selectors = ['.b_algo h2 a', '.result__title a', 'h2 a', 'h3 a']
            for selector in selectors:
                if results: break
                for a in soup.select(selector):
                    if len(results) >= target * 2: break
                    link = a.get('href', '').lower()
                    title = a.text.strip()
                    
                    if any(x.lower() in title.lower() for x in GARBAGE_KEYWORDS): continue
                    
                    name = title.split('|')[0].split('-')[0].split(':')[0].strip()
                    if len(name) < 3: continue
                    
                    results.append({"Name": name, "Link": link, "Source": mirror_type.capitalize()})
                    print(f"PROGRESS:{len(results)}:{(target*2)}:Indexed: {safe_str(name)[:15]}", flush=True)
        time.sleep(random.uniform(5, 10))
    except: pass
    return results

def verify_and_score(name, location):
    q = f'"{name}" {location} India social'
    url = f"https://www.bing.com/search?q={requests.utils.quote(q)}&cc=IN"
    found_url = "None"
    score = 8.8
    try:
        r = requests.get(url, headers=get_headers(), timeout=12)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            for a in soup.select('.b_algo h2 a, a'):
                link = a.get('href', '').lower()
                if any(p in link for p in PLATFORM_DOMAINS):
                    found_url = link
                    score = 9.8
                    break
    except: pass
    return found_url, score

def hunt(niche, location, target):
    if "state" in niche.lower() and "real" in niche.lower(): niche = "Real Estate"
    print(f">>> Omni Titan Ghoul v32.2 Active. Prospected for '{niche}' in {location}...", flush=True)
    
    # 1. MULTI-MIRROR DISCOVERY
    discovery_bank = probe_mirror(niche, location, target, "bing")
    if not discovery_bank:
        discovery_bank = probe_mirror(niche, location, target, "duckduckgo")
        
    final_prospects = []
    vault = Vault()
    for i, lead in enumerate(discovery_bank):
        if len(final_prospects) >= target: break
        
        # Sakt Gatekeeper (Stage 1): Discard if direct Mirror link is a custom domain
        is_independent = not any(p in lead['Link'].lower() for p in PLATFORM_DOMAINS)
        if is_independent: continue
            
        # Throttling for Cloud Safety
        delay = random.uniform(8, 15)
        print(f"DEBUG: Analysis Delay ({delay:.1f}s)...", flush=True)
        time.sleep(delay)
        
        # 2. VERIFICATION
        social_url, score = verify_and_score(lead['Name'], location)
        
        final_lead = {
            "Name": lead['Name'], "Social": social_url, "Score": score, 
            "Source": f"Titan+{social_url.split('.')[1].capitalize() if social_url != 'None' else 'Index'}"
        }
        
        vault.save(niche, location, final_lead)
        final_prospects.append(final_lead)
        print(f"PROGRESS:{len(final_prospects)}:{target}:SECURED JACKPOT: {safe_str(lead['Name'])[:20]}", flush=True)

    print(f">>> Ghost Session Finished. {len(final_prospects)} jackpot prospects secured.", flush=True)
    return final_prospects

if __name__ == "__main__":
    if len(sys.argv) < 4: sys.exit(1)
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
                    "Company Name": d["Name"], "Website": "None",
                    "WhatsApp": "None", "Email ID": "None",
                    "Social": d.get("Social","None"), "Score": d["Score"], "Source": d.get("Source", "v32.2")
                })
    print("DONE", flush=True)
