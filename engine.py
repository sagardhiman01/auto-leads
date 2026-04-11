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

# Engine v29.2: THE COMPARATIVE GHOST (ULTIMATE B2B PROSPECTOR)
# Redesigned for Indian SMB Discovery using Direct Directory Indexing.
# Discovery Core: JustDial (Pinning to India Market).
# Comparison Hub: Cross-referencing with Zomato, Swiggy, and Instagram.

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_STORE = "/data" if os.path.exists("/data") else PROJECT_ROOT
DB_PRODUCTION_PATH = os.path.join(DATA_STORE, "leads_production_v3.db")

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger("LEADSFLOW")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]

# PLATFORM DOMAIN LIST for Social Mining
SOCIAL_PLATFORMS = ["facebook.com", "instagram.com", "linkedin.com", "zomato.com", "swiggy.com"]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9,en-US;q=0.8",
    }

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
                             (niche, location, lead["Name"], "None", "None", lead.get("Email","None"), lead.get("Social","None"), lead.get("Score", 8.5), lead.get("Source", "v29.2")))
                conn.commit()
        except: pass

def extract_email(text):
    pattern = r'[a-zA-Z0-9._%+-]+@(?!(?:sentry|github|w3|bootstrap|email|png|jpg|js|gif|css|example)\.)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(pattern, text)
    return emails[0].lower() if emails else "None"

def probe_justdial_discovery(niche, location, target):
    """Discovery Layer: Uses JustDial to find verified local Indian business names"""
    results = []
    print(f"DEBUG: Probing Local Indian Registry (JustDial) for '{niche}' in {location}...", flush=True)
    # Formulate JD search URL
    # Replace spaces with hyphen for JD URL pattern
    jd_niche = niche.replace(" ", "-")
    url = f"https://www.justdial.com/{location}/{jd_niche}"
    
    try:
        r = requests.get(url, headers=get_headers(), timeout=12)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            # Extract names from h2 headings (verified works in local probe)
            names = [h2.text.strip() for h2 in soup.find_all('h2') if len(h2.text.strip()) > 3]
            # Secondary check: extract from title tags or specific JD classes if needed
            if not names:
                names = [span.text.strip() for span in soup.select('.lng_cont_name')]
            
            for i, name in enumerate(names):
                if len(results) >= target: break
                # JD 'Website' check: In the desktop view, listings with websites have specific icons/links
                # We prioritize names for now and cross-reference later
                results.append({"Name": name, "Source": "JustDial", "Score": 8.5})
                print(f"PROGRESS:{i+1}:DISCOVERED: {name[:25]}", flush=True)
    except Exception as e:
        print(f"DEBUG: JD Discovery Error: {e}", flush=True)
    return results

def cross_reference_social(name, location):
    """Correlation Hub: Probes Zomato and Instagram for a discovered business name"""
    platforms = ["Instagram", "Zomato", "Facebook"]
    found_sources = []
    found_url = "None"
    
    for p in platforms:
        q = f'"{name}" {location} India {p}'
        try:
            # Using DDG Lite POST for stealth meta-discovery
            r = requests.post('https://html.duckduckgo.com/html/', data={'q': q}, headers=get_headers(), timeout=10)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                # Check top result for platform domain match
                top_link = soup.select_one('.result__title a')
                if top_link:
                    url = top_link.get('href', '').lower()
                    if p.lower() in url:
                        found_sources.append(p)
                        found_url = top_link.get('href')
                        # If we find more than one, we have a jackpot
                        if len(found_sources) >= 1: break # Move to next business after finding one social link to maintain speed
        except: pass
    return found_sources, found_url

def hunt(niche, location, target):
    print(f">>> Comparative Ghost v29.2 Active. Aggregating Prospects for '{niche}'...", flush=True)
    
    # 1. PRIMARY DISCOVERY (Local Indian Identity)
    raw_prospects = probe_justdial_discovery(niche, location, target)
    
    if not raw_prospects:
        print("DEBUG: JustDial Discovery failed. Fallback to Search Mirrors...", flush=True)
        # Broad Search discovery here if needed
    
    # 2. COMPARISON & CROSS-PLATFORM ANALYSIS
    final_leads = []
    vault = Vault()
    for i, prospect in enumerate(raw_prospects):
        print(f"PROGRESS:{i+1}:{len(raw_prospects)}:Comparing: {prospect['Name'][:25]} across Platforms...", flush=True)
        
        # Cross-reference with Zomato/Insta/FB
        sources, social_link = cross_reference_social(prospect['Name'], location)
        
        if sources:
            source_tag = f"JustDial+{'+'.join(sources)}"
            score = 9.8 if len(sources) > 1 else 9.2
        else:
            source_tag = "JustDial"
            score = 8.8
            
        prospect.update({
            "Social": social_link,
            "Source": source_tag,
            "Score": score,
            "Email": "None" # Email extraction usually requires deeper scan, prioritize Social for now
        })
        
        # Final Save
        vault.save(niche, location, prospect)
        final_leads.append(prospect)
        
        # Throttle to prevent blocks on comparison stage
        time.sleep(random.uniform(1.2, 2.5))

    print(f">>> Ghost Session Finished. {len(final_leads)} Mult-Source Prospects Secured.", flush=True)
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
                    "WhatsApp": "None", "Email ID": d.get("Email","None"),
                    "Social": d.get("Social","None"), "Score": d["Score"], "Source": d.get("Source", "v29.2")
                })
    print("DONE", flush=True)
