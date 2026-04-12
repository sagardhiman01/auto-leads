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
from urllib.parse import quote

# Engine v37.1: THE OMNISCIENT MASTER (SURFACE-DISCOVERY EDITION)
# Strategy: Multi-Surface Rotation (Registry -> Social Index -> Portal Hubs).
# Goal: 100% discovery rate even on throttled cloud IPs.
# Quality: Absolute Native-Script & Garbage Rejection (Regex).

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

# OMNI-BLACKLIST: Regex for languages and native scripts (Odia, Hindi, etc.)
GARBAGE_PATTERN = re.compile(r"(hindi|marathi|punjabi|tamil|telugu|bengali|urdu|english|gujarati|kannada|malayalam|assamese|odia|हिंदी|मराठी|বাংলা|ਪੰਜਾਬੀ|اردو|தமிழ்|తెలుగు|ગુજરાતી|ಕನ್ನಡ|മലയാളം|অসমীয়া|ଓଡ଼ିଆ|about|contact|privacy|terms|login|signup|career|advertise|feedback|help|listing|result|bing|search|profile)", re.IGNORECASE)

def clean_log(text):
    if not text: return ""
    return text.encode('ascii', 'ignore').decode('ascii').strip()

def is_garbage(text):
    t = text.strip()
    if len(t) < 3: return True
    if GARBAGE_PATTERN.search(t): return True
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
                             (niche, location, lead["Name"], "None", "None", lead.get("Email","None"), lead.get("Social","None"), lead.get("Score", 8.5), lead.get("Source", "v37.1")))
                conn.commit()
        except: pass

def probe_mirror(niche, location, target, surface="registry"):
    results = []
    print(f"DEBUG: Tapping {surface.upper()} Surface for '{niche}' in {location}...", flush=True)
    
    headers = {"User-Agent": random.choice(USER_AGENTS), "Accept-Language": "en-IN,en;q=0.9"}
    
    if surface == "registry":
        city = location.lower().replace(' ', '-')
        service = niche.lower().replace(' ', '-')
        url = f"https://www.justdial.com/{city}/{service}/"
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                for card in soup.select('li.cntanr'):
                    name_tag = card.select_one('.jcn a')
                    if not name_tag: continue
                    name = name_tag.text.strip()
                    if is_garbage(name): continue
                    if card.select_one('span.web_icw, a[href*="http"]'): continue # No Website Check
                    results.append({"Name": name, "Source": "Registry"})
                    print(f"PROGRESS Discovery: {clean_log(name)[:18]}", flush=True)
        except: pass

    elif surface == "social":
        q = f'site:facebook.com "{niche}" {location} India'
        url = f"https://www.bing.com/search?q={quote(q)}&cc=IN"
        try:
            r = requests.get(url, headers=headers, timeout=12)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                for a in soup.select('.b_algo h2 a, a'):
                    link = a.get('href', '').lower()
                    if "facebook.com" in link:
                        name = a.text.split('|')[0].split('-')[0].strip()
                        if not is_garbage(name):
                             results.append({"Name": name, "Social": link, "Source": "Facebook"})
                             print(f"PROGRESS Discovery (FB): {clean_log(name)[:18]}", flush=True)
        except: pass

    return results

def verify_and_score(name, location):
    q = f'"{name}" {location} India platform presence'
    url = f"https://www.bing.com/search?q={quote(q)}&cc=IN"
    social_url = "None"
    score = 8.5
    try:
        r = requests.get(url, headers={"User-Agent": random.choice(USER_AGENTS)}, timeout=10)
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
    try:
        if "state" in niche.lower() and "real" in niche.lower(): niche = "Real Estate"
        print(f">>> Omniscient Master v37.1 Active. Indexing {location}...", flush=True)
        
        final_leads = []
        vault = Vault()
        
        # Phase 1: Registry Discovery
        raw_bank = probe_mirror(niche, location, target, "registry")
        
        # Phase 2: Social Discovery Fallback (if Registry is low)
        if len(raw_bank) < target:
            social_bank = probe_mirror(niche, location, target, "social")
            raw_bank.extend(social_bank)

        for lead in raw_bank:
            if len(final_leads) >= target: break
            
            # Cloud IPM Protection
            delay = random.uniform(8, 15)
            print(f"DEBUG: Analyzing {clean_log(lead['Name'])[:15]} ({delay:.1f}s)...", flush=True)
            time.sleep(delay)
            
            social_link = lead.get("Social", "None")
            score = 9.8 if social_link != "None" else 8.5
            
            if social_link == "None":
                social_link, score = verify_and_score(lead['Name'], location)
            
            # Sakt Quality Gate
            if is_garbage(lead['Name']): continue
            
            final_lead = {"Name": lead['Name'], "Social": social_link, "Score": score}
            vault.save(niche, location, final_lead)
            final_leads.append(final_lead)
            print(f"PROGRESS:{len(final_leads)}:{target}:SECURED PLATINUM: {clean_log(lead['Name'])[:20]}", flush=True)

        print(f">>> Titan Session Finished. {len(final_leads)} prospects secured.", flush=True)
        return final_leads
    except Exception as e:
        print(f"FATAL_CRASH: {str(e)}", flush=True)
        return []

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
                    "Social": d.get("Social","None"), "Score": d["Score"], "Source": "v37.1"
                })
    print("DONE", flush=True)
