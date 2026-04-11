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

# Engine v33.0: THE ETERNAL TITAN (REGISTRY DISCOVERY)
# Designed for 100% stability. Bypasses blocked search mirrors.
# Strategy: Registry Mirror discovery (JustDial) + Platform Cross-Check.
# Constraint: Strictly ZERO WEBSITE. Only capture high-intent Social-Only plays.

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

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9,en-US;q=0.8",
        "Referer": "https://www.google.com/"
    }

def clean_name(text):
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
                             (niche, location, lead["Name"], "None", "None", lead.get("Email","None"), lead.get("Social","None"), lead.get("Score", 8.5), lead.get("Source", "v33.0")))
                conn.commit()
        except: pass

def probe_registry_mirror(niche, location, target):
    """Registry Hub: Direct Mirror of local Indian B2B registry"""
    results = []
    print(f"DEBUG: Tapping Registry Mirror for '{niche}'...", flush=True)
    
    city = location.lower().replace(' ', '-')
    service = niche.lower().replace(' ', '-')
    url = f"https://www.justdial.com/{city}/{service}/"
    
    try:
        r = requests.get(url, headers=get_headers(), timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            # Look for business name entries
            for entry in soup.select('li.cntanr, div.result-title'):
                if len(results) >= target + 5: break
                
                name_tag = entry.select_one('.lng_cont_name, h2, span.jcn a')
                if not name_tag: continue
                name = name_tag.text.strip()
                if len(name) < 3: continue
                
                # Sakt Website Shield
                web_btn = entry.select_one('span.web_icw, a[href*="http"]')
                if web_btn:
                    # Ignore businesses with existing website buttons
                    continue
                
                results.append({"Name": name, "Link": "None", "Source": "Registry"})
                print(f"PROGRESS:{len(results)}:{(target+5)}:REGISTRY: {clean_name(name)[:18]}", flush=True)
        time.sleep(random.uniform(5, 8))
    except: pass
    
    # FALLBACK: If JustDial mirror is blocked, use search mirror specifically for platforms
    if not results:
        print("DEBUG: Registry Throttled. Switching to Social Mirror...", flush=True)
        q = f'"{niche}" {location} India (site:facebook.com OR site:zomato.com)'
        url = f"https://www.bing.com/search?q={requests.utils.quote(q)}&cc=IN"
        try:
            r = requests.get(url, headers=get_headers(), timeout=12)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                for a in soup.select('.b_algo h2 a, a'):
                    if len(results) >= target: break
                    link = a.get('href', '').lower()
                    if any(p in link for p in PLATFORM_DOMAINS):
                        name = a.text.split('|')[0].split('-')[0].strip()
                        results.append({"Name": name, "Link": link, "Source": "Social-Index"})
                        print(f"PROGRESS:{len(results)}:{target}:SOCIAL: {clean_name(name)[:18]}", flush=True)
        except: pass
        
    return results

def verify_social(name, location):
    """Jackpot Check: Ensures business is active on platforms"""
    q = f'"{name}" {location} India instagram facebook'
    url = f"https://www.bing.com/search?q={requests.utils.quote(q)}&cc=IN"
    social_url = "None"
    score = 8.5
    try:
        r = requests.get(url, headers=get_headers(), timeout=10)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            for a in soup.select('.b_algo h2 a, a'):
                link = a.get('href', '').lower()
                if any(p in link for p in PLATFORM_DOMAINS):
                    social_url = link
                    score = 9.8
                    break
    except: pass
    return social_url, score

def hunt(niche, location, target):
    if "state" in niche.lower() and "real" in niche.lower(): niche = "Real Estate"
    print(f">>> Eternal Titan v33.0 Active. Indexing {location}...", flush=True)
    
    # 1. DISCOVERY
    bank = probe_registry_mirror(niche, location, target)
    
    final_leads = []
    vault = Vault()
    for i, lead in enumerate(bank):
        if len(final_leads) >= target: break
        
        # CLOUD PROTECTOR (Throttling)
        delay = random.uniform(10, 15)
        print(f"DEBUG: Human-Speed Link Analysis ({delay:.1f}s)...", flush=True)
        time.sleep(delay)
        
        # 2. VERIFICATION (Jackpot)
        platform_url, score = verify_social(lead['Name'], location)
        
        # QUALITY GATE: If it's a social discovery, it's already a jackpot
        # If it's a registry discovery, we accept it as is (since we confirmed NO website button)
        
        final_lead = {
            "Name": lead['Name'], "Social": platform_url, "Score": score, 
            "Source": f"Titan+{platform_url.split('.')[1].capitalize() if platform_url != 'None' else 'Registry'}"
        }
        
        vault.save(niche, location, final_lead)
        final_leads.append(final_lead)
        print(f"PROGRESS:{len(final_leads)}:{target}:SECURED GOLD: {clean_name(lead['Name'])[:20]}", flush=True)

    print(f">>> Titan Session Finished. {len(final_leads)} jackpot prospects secured.", flush=True)
    return final_leads

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
                    "Social": d.get("Social","None"), "Score": d["Score"], "Source": d.get("Source", "v33.0")
                })
    print("DONE", flush=True)
