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
from duckduckgo_search import DDGS

# Engine v23.0: THE STEALTH GHOST
# Uses high-level API wrappers to bypass Render network blocks.

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_STORE = "/data" if os.path.exists("/data") else PROJECT_ROOT
DB_PRODUCTION_PATH = os.path.join(DATA_STORE, "leads_production_v3.db")

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger("LEADSFLOW")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]

B2B_GUARD = [
    "news", "times", "express", "lokmat", "livemint", "ndtv", "realtor.com", "zillow", "wikipedia", 
    "facebook", "instagram", "youtube", "linkedin", "magicbricks", "99acres", "housing.com", 
    "justdial", "indiamart", "sulekha", "quikr", "amazon", "flipkart", "yelp", "tripadvisor"
]

def get_headers():
    return {"User-Agent": random.choice(USER_AGENTS)}

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
        except Exception as e:
            print(f"VAULT ERROR: {e}", flush=True)

    def save(self, niche, location, lead):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("INSERT OR REPLACE INTO leads_3 (niche, location, company_name, website, phone, email, social, score, source) VALUES (?,?,?,?,?,?,?,?,?)",
                             (niche, location, lead["Name"], lead.get("Website","None"), lead.get("Phone","None"), lead.get("Email","None"), lead.get("Social","None"), lead.get("Score", 5.0), lead.get("Source","v23.0")))
                conn.commit()
        except: pass

def extract_contacts(html, url):
    email_pattern = r'[a-zA-Z0-9._%+-]+@(?!(?:sentry|github|w3|bootstrap|email|png|jpg|js|gif|css|example)\.)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    phone_pattern = r'(?:\+91|91|0)?[6-9]\d{9}'
    
    emails = re.findall(email_pattern, html)
    phones = re.findall(phone_pattern, html)
    
    e = emails[0] if emails else "None"
    p = phones[0] if phones else "None"
    
    if e.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.css', '.js')): e = "None"
    return e, p

def hunt(niche, location, target):
    print(f">>> Ghost Scout v23.0 Active. Target: {target} for {niche} in {location}", flush=True)
    results, seen = [], set()
    
    q = f'"{niche}" {location} India -news -times -facebook'
    
    try:
        print(f"DEBUG: Initializing stealth API session...", flush=True)
        with DDGS() as ddgs:
            # Using the text search method which is much more robust
            ddgs_gen = ddgs.text(q, region='in-en', safesearch='off', timelimit='y')
            
            for r in ddgs_gen:
                if len(results) >= target: break
                
                title = r.get('title', '')
                link = r.get('href', '')
                
                if any(g in link.lower() for g in B2B_GUARD): continue
                
                if link and link not in seen:
                    seen.add(link)
                    score = 9.0 if ".in" in link.lower() else 7.5
                    results.append({"Name": title, "Website": link, "Source": "Ghost-API", "Score": score})
                    safe_t = title.encode('ascii', 'ignore').decode('ascii')
                    print(f"PROGRESS:{len(results)}:{target}:Found: {safe_t[:30]}...", flush=True)

    except Exception as e:
        print(f"DEBUG: Critical Search Error: {e}", flush=True)

    if not results:
        print("DEBUG: Ghost Scout returned 0 results. Checking network status...", flush=True)

    final_leads = []
    vault = Vault()
    for i, lead in enumerate(results):
        safe_name = lead['Name'].encode('ascii', 'ignore').decode('ascii')
        print(f"PROGRESS:{i+1}:{len(results)}:Extracting: {safe_name[:30]}...", flush=True)
        try:
            time.sleep(random.uniform(0.5, 1.5))
            r = requests.get(lead['Website'], headers=get_headers(), timeout=12)
            e, p = extract_contacts(r.text if r.status_code == 200 else "", lead['Website'])
            lead.update({"Email": e, "Phone": f"W:{p}" if p != "None" else "None", "Social": "None"})
            vault.save(niche, location, lead)
            final_leads.append(lead)
        except:
            lead.update({"Email": "None", "Phone": "None", "Social": "None"})
            vault.save(niche, location, lead)
            final_leads.append(lead)

    print(f">>> Ghost Session Complete. {len(final_leads)} leads secured.", flush=True)
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
                    "Social": d.get("Social","None"), "Score": d["Score"], "Source": d.get("Source","v23.0")
                })
    print("DONE", flush=True)
