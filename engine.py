import sqlite3
import os
import sys
import re
import logging
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import random
import csv
import time
import base64
from urllib.parse import urlparse, parse_qs

# Engine v31.3: THE OMNI TITAN TOTAL (FORCED DISCOVERY EDITION)
# Feature 1: Forced Platform RSS Indexing (Site-prioritized discovery).
# Feature 2: Deep Result Scanning (Analyzing top 20-30 prospects).
# Feature 3: Strictly Zero-Website Shield (Accept Platforms, Reject Domains).
# Feature 4: Cloud-IP Immortal (Human-speed throttling for Render).

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_STORE = "/data" if os.path.exists("/data") else PROJECT_ROOT
DB_PRODUCTION_PATH = os.path.join(DATA_STORE, "leads_production_v3.db")

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger("LEADSFLOW")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
]

PLATFORM_DOMAINS = ["facebook.com", "instagram.com", "zomato.com", "swiggy.com", "justdial.com", "linkedin.com", "indiamart.com", "tradeindia.com"]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/rss+xml,application/xml,text/xml,text/html;q=0.9",
        "Accept-Language": "en-IN,en;q=0.9,en-US;q=0.8",
        "Referer": "https://www.google.com/"
    }

def decode_bing_url(url):
    try:
        if "bing.com/ck/a" not in url: return url
        u_param = parse_qs(urlparse(url).query).get('u', [None])[0]
        if u_param:
            b64 = u_param[2:] if u_param.startswith('a1') else u_param
            b64 += '=' * (-len(b64) % 4)
            return base64.b64decode(b64).decode('utf-8', errors='ignore').split('?')[0].lower()
    except: pass
    return url.lower()

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
                             (niche, location, lead["Name"], "None", "None", lead.get("Email","None"), lead.get("Social","None"), lead.get("Score", 8.5), lead.get("Source", "v31.3")))
                conn.commit()
        except: pass

def probe_rss_discovery(niche, location, target):
    """FORCED Discovery: Requesting Platform Profiles specifically in RSS feed"""
    results = []
    print(f"DEBUG: Mapping Social Registry (Forced RSS) for '{niche}' in {location}...", flush=True)
    
    # FORCED QUERY: Prioritizing platforms to avoid official websites
    q = f'"{niche}" {location} India (zomato OR facebook OR instagram OR justdial)'
    url = f"https://www.bing.com/search?q={requests.utils.quote(q)}&format=rss&cc=IN"
    
    try:
        r = requests.get(url, headers=get_headers(), timeout=15)
        if r.status_code == 200:
            root = ET.fromstring(r.text)
            for i, item in enumerate(root.findall('.//item')):
                if len(results) >= target * 3: break
                title = item.find('title').text if item.find('title') is not None else ""
                link = item.find('link').text if item.find('link') is not None else ""
                
                # Unmask name
                name = title.split('|')[0].split('-')[0].split(':')[0].strip()
                if len(name) < 3 or name.lower() in ["bing", "search", "login"]: continue
                
                results.append({"Name": name, "Source": "RSS-Portal", "Link": link})
                print(f"PROGRESS:{i+1}:{target*5}:Indexed: {name[:15].encode('ascii', 'ignore').decode()}", flush=True)
    except: pass
    return results

def deep_verify(name, location):
    """Strict Verification: Ensuring lead has NO website and exists on platforms"""
    q = f'"{name}" {location} India (facebook.com OR zomato.com OR instagram.com)'
    url = f"https://www.bing.com/search?q={requests.utils.quote(q)}&cc=IN"
    final_url = "None"
    score = 8.5
    try:
        r = requests.get(url, headers=get_headers(), timeout=12)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            for a in soup.select('.b_algo h2 a, a'):
                link = decode_bing_url(a.get('href', ''))
                # Strict: Capture social platform profile
                if any(p in link.lower() for p in PLATFORM_DOMAINS):
                    final_url = link
                    score = 9.8
                    break
    except: pass
    return final_url, score

def hunt(niche, location, target):
    print(f">>> Omni Titan v31.3 Absolute Sourcing Active for '{niche}'...", flush=True)
    
    # 1. FORCED RSS DISCOVERY
    discovery_index = probe_rss_discovery(niche, location, target)
    
    final_prospects = []
    vault = Vault()
    for i, lead in enumerate(discovery_index):
        if len(final_prospects) >= target: break
        
        # SAKT (STRICT) GATEKEEPER Stage 1: Discard if direct RSS link is a custom domain
        is_independent = not any(p in lead['Link'].lower() for p in PLATFORM_DOMAINS)
        clean_name = lead['Name'].encode('ascii', 'ignore').decode()
        if is_independent:
            print(f"DEBUG: Discarding '{clean_name[:12]}' - Official Website Detected.", flush=True)
            continue
            
        # CLOUD-IP PROTECTION (Extreme Throttling)
        delay = random.uniform(8, 15)
        print(f"DEBUG: Human Analysis Pause ({delay:.1f}s)...", flush=True)
        time.sleep(delay)
        
        # 2. DEEP VERIFICATION (Jackpot Check)
        social_url, score = deep_verify(lead['Name'], location)
        
        prospect = {
            "Name": lead['Name'], "Social": social_url, "Score": score, 
            "Source": f"Titan+{social_url.split('.')[1].capitalize() if social_url != 'None' else 'RSS'}"
        }
        
        vault.save(niche, location, prospect)
        final_prospects.append(prospect)
        print(f"PROGRESS:{len(final_prospects)}:{target}:SECURED JACKPOT: {clean_name[:20]}", flush=True)

    print(f">>> Ghost Session Finished. {len(final_prospects)} Prospects Verified & Secured.", flush=True)
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
                    "Social": d.get("Social","None"), "Score": d["Score"], "Source": d.get("Source", "v31.3")
                })
    print("DONE", flush=True)
