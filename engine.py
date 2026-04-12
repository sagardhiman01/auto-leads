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

# Engine v36.0: THE LOGGING TITAN (DEEP DEBUG EDITION)
# Feature 1: Crash Protection (Global try-except to capture stderr).
# Feature 2: Native Script Lockdown (हिंदी, বাংলা etc block).
# Feature 3: Precision Discovery (.jcn a selective targeting).
# Feature 4: Cloud IP Immortality (8-15s throttles).

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

BLACKLIST_RAW = [
    "hindi", "marathi", "punjabi", "tamil", "telugu", "bengali", "urdu", "english", "gujarati", "kannada", "malayalam", "assamese", "odia",
    "हिंदी", "मराठी", "বাংলা", "ਪੰਜਾਬੀ", "اردو", "தமிழ்", "తెలుగు", "ગુજરાતી", "ಕನ್ನಡ", "മലയാളം", "অসমীয়া", "ଓଡ଼ିଆ",
    "home", "about", "contact", "privacy", "terms", "login", "signup", "career", "advertise", "feedback", "help", "listing"
]

def clean_name(text):
    if not text: return ""
    return text.encode('ascii', 'ignore').decode('ascii').strip()

def is_garbage_name(text):
    t = text.lower().strip()
    if len(t) < 3: return True
    if any(x == t for x in BLACKLIST_RAW): return True
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
                             (niche, location, lead["Name"], "None", "None", lead.get("Email","None"), lead.get("Social","None"), lead.get("Score", 8.5), lead.get("Source", "v36.0")))
                conn.commit()
        except: pass

def probe_registry_scrubbed(niche, location, target):
    results = []
    print(f"DEBUG: Tapping Registry Scrub Hub for '{niche}' in {location}...", flush=True)
    city = location.lower().replace(' ', '-')
    service = niche.lower().replace(' ', '-')
    url = f"https://www.justdial.com/{city}/{service}/"
    
    try:
        r = requests.get(url, headers={
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "en-IN,en;q=0.9,en-US;q=0.8"
        }, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            for card in soup.select('li.cntanr'):
                if len(results) >= target + 5: break
                name_tag = card.select_one('.jcn a')
                if not name_tag: continue
                name = name_tag.text.strip()
                if is_garbage_name(name): continue
                web_btn = card.select_one('span.web_icw, a[href*="http"]')
                if web_btn: continue
                results.append({"Name": name, "Link": "None", "Source": "Registry"})
                print(f"PROGRESS:{len(results)}:{(target+5)}:REGISTRY: {clean_name(name)[:18]}", flush=True)
        time.sleep(random.uniform(5, 8))
    except Exception as e:
        print(f"DEBUG: Registry Mirror Error: {str(e)}", flush=True)
    
    if not results:
        print("DEBUG: Registry Throttled. Switching to Social Lockdown...", flush=True)
        q = f'"{niche}" {location} India (site:facebook.com OR site:zomato.com)'
        url = f"https://www.bing.com/search?q={requests.utils.quote(q)}&cc=IN"
        try:
            r = requests.get(url, headers={"User-Agent": random.choice(USER_AGENTS)}, timeout=12)
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
        except Exception as e:
            print(f"DEBUG: Social Mirror Error: {str(e)}", flush=True)
    return results

def verify_social(name, location):
    q = f'"{name}" {location} India social profile'
    url = f"https://www.bing.com/search?q={requests.utils.quote(q)}&cc=IN"
    final_url = "None"
    score = 8.5
    try:
        r = requests.get(url, headers={"User-Agent": random.choice(USER_AGENTS)}, timeout=10)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            for a in soup.select('.b_algo h2 a, a'):
                link = a.get('href', '').lower()
                if any(p in link for p in PLATFORM_DOMAINS):
                    final_url = link
                    score = 9.8
                    break
    except: pass
    return final_url, score

def hunt(niche, location, target):
    try:
        if "state" in niche.lower() and "real" in niche.lower(): niche = "Real Estate"
        print(f">>> Logging Titan v36.0 Active. Scrubbing {location}...", flush=True)
        
        bank = probe_registry_scrubbed(niche, location, target)
        final_prospects = []
        vault = Vault()
        for i, lead in enumerate(bank):
            if len(final_prospects) >= target: break
            delay = random.uniform(8, 15)
            print(f"DEBUG: Human-Speed Scrub Pause ({delay:.1f}s)...", flush=True)
            time.sleep(delay)
            social_link, score = verify_social(lead['Name'], location)
            if is_garbage_name(lead['Name']): continue
            final_lead = {"Name": lead['Name'], "Social": social_link, "Score": score}
            vault.save(niche, location, final_lead)
            final_prospects.append(final_lead)
            print(f"PROGRESS:{len(final_prospects)}:{target}:SECURED GOLD: {clean_name(lead['Name'])[:20]}", flush=True)

        print(f">>> Titan Session Finished. {len(final_prospects)} clean prospects secured.", flush=True)
        return final_prospects
    except Exception as e:
        print(f"FATAL_ENGINE_ERROR: {str(e)}", flush=True)
        return []

if __name__ == "__main__":
    try:
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
                        "Social": d.get("Social","None"), "Score": d.get("Score", 8.5), "Source": "v36.0"
                    })
        print("DONE", flush=True)
    except Exception as e:
        print(f"CRITICAL_STARTUP_ERROR: {str(e)}", flush=True)
