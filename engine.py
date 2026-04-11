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

# Engine v35.0: THE SCRUB TITAN (JUNK LOCKDOWN)
# Feature 1: Native Script Blacklist (Blocking हिंदी, বাংলা, اردو etc.).
# Feature 2: High-Precision Selectors (Locked to Gold-Standard `.jcn a`).
# Feature 3: Strictly B2B Quality (Platform-only leads, Zero independent website).
# Feature 4: Cloud-IP Immortal (Human-speed throttling for Render).

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

# BLACKLIST: Terms that are NOT businesses (Languages, Nav links, etc.)
# Including NATIVE SCRIPTS that appeared in previous failures
BLACKLIST_RAW = [
    "hindi", "marathi", "punjabi", "tamil", "telugu", "bengali", "urdu", "english", "gujarati", "kannada", "malayalam", "assamese", "odia",
    "हिंदी", "मराठी", "বাংলা", "ਪੰਜਾਬੀ", "اردو", "தமிழ்", "తెలుగు", "ગુજરાતી", "ಕನ್ನಡ", "മലയാളം", "অসমীয়া", "ଓଡ଼ିଆ",
    "home", "about", "contact", "privacy", "terms", "login", "signup", "career", "advertise", "feedback", "help", "listing",
    "sign in", "password", "forgot", "register", "download", "app", "install", "update", "browser", "search", "result", "profile"
]

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

def is_garbage_name(text):
    t = text.lower().strip()
    if len(t) < 3: return True
    # Check against raw and lowercase blacklist
    if any(x == t for x in BLACKLIST_RAW): return True
    if any(x in t for x in ["copyright", "privacy policy", "terms of use"]): return True
    return False

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
                             (niche, location, lead["Name"], "None", "None", lead.get("Email","None"), lead.get("Social","None"), lead.get("Score", 8.5), lead.get("Source", "v35.0")))
                conn.commit()
        except: pass

def probe_registry_scrubbed(niche, location, target):
    """Discovery Hub: Taps into the Registry with ABSOLUTE Precision Selectors"""
    results = []
    print(f"DEBUG: Tapping Registry Scrub Hub for '{niche}' in {location}...", flush=True)
    
    city = location.lower().replace(' ', '-')
    service = niche.lower().replace(' ', '-')
    url = f"https://www.justdial.com/{city}/{service}/"
    
    try:
        r = requests.get(url, headers=get_headers(), timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            # Look for Business Card Containers exclusively
            for card in soup.select('li.cntanr'):
                if len(results) >= target + 5: break
                
                # Title is EXCLUSIVELY in .jcn a for business names
                name_tag = card.select_one('.jcn a')
                if not name_tag: continue
                name = name_tag.text.strip()
                
                if is_garbage_name(name): continue
                
                # Strict Zero-Website Shield
                web_btn = card.select_one('span.web_icw, a[href*="http"]')
                if web_btn: continue
                
                results.append({"Name": name, "Link": "None", "Source": "Registry"})
                print(f"PROGRESS:{len(results)}:{(target*5)}:REGISTRY: {clean_name(name)[:18]}", flush=True)
        time.sleep(random.uniform(5, 8))
    except: pass
    
    # Fallback to Social Mirror if Registry is blocked, but with strict name control
    if not results:
        print("DEBUG: Registry Mirror throttled. Switching to Social Lockdown...", flush=True)
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
                        if not is_garbage_name(name):
                             results.append({"Name": name, "Link": link, "Source": "Social-Index"})
                             print(f"PROGRESS:{len(results)}:{target}:SOCIAL: {clean_name(name)[:18]}", flush=True)
        except: pass
        
    return results

def verify_social(name, location):
    q = f'"{name}" {location} India organic profile'
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
    print(f">>> Scrub Titan v35.0 Active. Purifying {location}...", flush=True)
    
    # 1. SCRUBBED DISCOVERY
    bank = probe_registry_scrubbed(niche, location, target)
    
    final_prospects = []
    vault = Vault()
    for i, lead in enumerate(bank):
        if len(final_prospects) >= target: break
        
        # CLOUD PROTECTOR (Throttling)
        delay = random.uniform(10, 15)
        print(f"DEBUG: Logic Scrub Pause ({delay:.1f}s)...", flush=True)
        time.sleep(delay)
        
        # 2. VERIFICATION (Guaranteed Quality)
        social_link, score = verify_social(lead['Name'], location)
        
        # FINAL SANITY CHECK
        if is_garbage_name(lead['Name']): continue
        
        final_lead = {
            "Name": lead['Name'], "Social": social_link, "Score": score, 
            "Source": f"Scrub+{social_link.split('.')[1].capitalize() if social_link != 'None' else 'Index'}"
        }
        
        vault.save(niche, location, final_lead)
        final_prospects.append(final_lead)
        print(f"PROGRESS:{len(final_prospects)}:{target}:SECURED GOLD: {clean_name(lead['Name'])[:20]}", flush=True)

    print(f">>> Titan Session Finished. {len(final_prospects)} clean prospects secured.", flush=True)
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
                    "Social": d.get("Social","None"), "Score": d["Score"], "Source": d.get("Source", "v35.0")
                })
    print("DONE", flush=True)
