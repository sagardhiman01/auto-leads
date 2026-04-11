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

# Engine v26.0: THE GEOGRAPHIC TITAN (B2B RESILIENT)
# Using Region-Locked Bing RSS to bypass Render's AOL/Yahoo 500 blocks.
# Strictly extracts Indian SMB Leads with commercial intent.

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_STORE = "/data" if os.path.exists("/data") else PROJECT_ROOT
DB_PRODUCTION_PATH = os.path.join(DATA_STORE, "leads_production_v3.db")

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger("LEADSFLOW")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]

# THE B2B GUARD: Stripping all useless news, social, and global portal clutter
B2B_GUARD = [
    "news", "times", "express", "lokmat", "livemint", "ndtv", "realtor.com", "zillow", "wikipedia", 
    "facebook", "instagram", "youtube", "linkedin", "magicbricks", "99acres", "housing.com", 
    "justdial", "indiamart", "sulekha", "quikr", "amazon", "flipkart", "yelp"
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9,en-US;q=0.8",
        "DNT": "1",
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
                             (niche, location, lead["Name"], lead.get("Website","None"), lead.get("Phone","None"), lead.get("Email","None"), lead.get("Social","None"), lead.get("Score", 5.0), lead.get("Source", "v26.0")))
                conn.commit()
        except: pass

def resolve_url(url):
    """Bypasses search engine redirect and gets final business URL"""
    try:
        if "bing.com/search" in url or "yahoo.com" in url or "aol.com" in url:
            r = requests.get(url, headers=get_headers(), timeout=8, allow_redirects=True)
            return r.url
        return url
    except: return url

def extract_contacts(html, url):
    email_pattern = r'[a-zA-Z0-9._%+-]+@(?!(?:sentry|github|w3|bootstrap|email|png|jpg|js|gif|css|example)\.)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    phone_pattern = r'(?:\+91|91|0)?[6-9]\d{9}'
    emails = re.findall(email_pattern, html)
    phones = re.findall(phone_pattern, html)
    e = emails[0] if emails else "None"
    p = phones[0] if phones else "None"
    if e.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.css', '.js', '.pdf')): e = "None"
    return e, p

def hunt(niche, location, target):
    print(f">>> Geographic Titan v26.0 Active. Target: {target} leads.", flush=True)
    if "real state" in niche.lower(): niche = niche.lower().replace("real state", "real estate")
    results, seen = [], set()
    
    # RELENTLESS SOURCE: Bing India RSS (Market Locked to Bypass Cloud Blocks)
    print(f"DEBUG: Pinning Sourcing to India Market ({location})...", flush=True)
    # Market parameters for India: cc=IN (CountryCode), setmkt=en-IN (Market), setlang=en-IN (Language)
    q = f'"{niche}" {location} India'
    rss_url = f"https://www.bing.com/search?q={requests.utils.quote(q)}&format=rss&cc=IN&setmkt=en-IN&setlang=en-IN"
    
    try:
        r = requests.get(rss_url, headers=get_headers(), timeout=12)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'xml')
            for item in soup.find_all('item'):
                if len(results) >= target: break
                raw_url = item.link.text if item.link else ""
                title = item.title.text if item.title else ""
                
                # 1. Resolve to actual website
                final_url = resolve_url(raw_url)
                
                # 2. B2B GUARD (No News, No US Portals)
                lower_url = final_url.lower()
                if any(g in lower_url for g in B2B_GUARD): continue
                if any(g in title.lower() for g in ["news", "times", "express", "update", "dailymotion", "weather"]): continue
                
                if final_url and final_url not in seen and "bing.com" not in final_url:
                    seen.add(final_url)
                    # Geofenced Score: .in domains get 9.5
                    score = 9.5 if ".in" in lower_url or "builder" in title.lower() else 8.5
                    results.append({"Name": title, "Website": final_url, "Source": "Titan-Pin", "Score": score})
                    safe_t = title.encode('ascii', 'ignore').decode('ascii')
                    print(f"PROGRESS:{len(results)}:{target}:Found Regional Lead: {safe_t[:35]}", flush=True)
        else:
            print(f"DEBUG: Bing RSS returned status {r.status_code}", flush=True)
    except Exception as e:
        print(f"DEBUG: Sourcing Error: {e}", flush=True)

    # FINAL EXTRACTION
    final_leads = []
    vault = Vault()
    for i, lead in enumerate(results):
        safe_name = lead['Name'].encode('ascii', 'ignore').decode('ascii')
        print(f"PROGRESS:{i+1}:{len(results)}:Deep Scanning: {safe_name[:30]}...", flush=True)
        try:
            time.sleep(random.uniform(0.5, 1.0))
            r = requests.get(lead['Website'], headers=get_headers(), timeout=10)
            e, p = extract_contacts(r.text if r.status_code == 200 else "", lead['Website'])
            lead.update({"Email": e, "Phone": f"W:{p}" if p != "None" else "None", "Social": "None"})
            vault.save(niche, location, lead)
            final_leads.append(lead)
        except:
            lead.update({"Email": "None", "Phone": "None", "Social": "None"})
            vault.save(niche, location, lead)
            final_leads.append(lead)

    print(f">>> Titan Session Finished. {len(final_leads)} leads secured.", flush=True)
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
                    "Company Name": d["Name"], "Website": d["Website"],
                    "WhatsApp": d.get("Phone","None"), "Email ID": d.get("Email","None"),
                    "Social": d.get("Social","None"), "Score": d["Score"], "Source": d.get("Source", "v26.0")
                })
    print("DONE", flush=True)
