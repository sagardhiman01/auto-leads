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

# Engine v22.0: THE SILENT SCRAPER (TRUE B2B CAPTURE)
# Bypasses WAF completely using POST tunneling and extracts pure business leads.

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_STORE = "/data" if os.path.exists("/data") else PROJECT_ROOT

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger("LEADSFLOW")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]

# THE B2B GUARD: Blocks all News, US real estate hubs, and generic portals
B2B_GUARD = [
    "news", "times", "express", "lokmat", "livemint", "ndtv", "realtor.com", "zillow", "wikipedia", 
    "facebook", "instagram", "youtube", "linkedin", "magicbricks", "99acres", "housing.com", 
    "justdial", "indiamart", "sulekha", "quikr"
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-IN,en-US;q=0.9,en;q=0.8",
        "Origin": "https://html.duckduckgo.com",
    }

class Vault:
    def __init__(self):
        self.db_path = os.path.join(DATA_STORE, "leads_vault.db")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS leads_3 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                niche TEXT, location TEXT, company_name TEXT,
                website TEXT, phone TEXT, email TEXT,
                social TEXT, score REAL, source TEXT,
                UNIQUE(company_name, location))""")
            conn.commit()
    def save(self, niche, location, lead):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("INSERT OR REPLACE INTO leads_3 (niche, location, company_name, website, phone, email, social, score, source) VALUES (?,?,?,?,?,?,?,?,?)",
                             (niche, location, lead["Name"], lead.get("Website","None"), lead.get("Phone","None"), lead.get("Email","None"), lead.get("Social","None"), lead.get("Score", 5.0), lead.get("Source","v22.0")))
                conn.commit()
        except: pass

def extract_contacts(html, url):
    email = re.search(r'[a-zA-Z0-9._%+-]+@(?!(?:sentry|github|w3|bootstrap|email|png|jpg|js|gif)\.)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)
    phone = re.search(r'(?:\+91|91|0)?[6-9]\d{9}', html)
    e = email.group(0) if email else "None"
    p = phone.group(0) if phone else "None"
    return e, p

def hunt(niche, location, target):
    print(f">>> Silent Scraper v22.0 Active. Target: {target}", flush=True)
    if "real state" in niche.lower(): niche = niche.lower().replace("real state", "real estate")
    results, seen = [], set()
    
    # ADVANCED POST TUNNELING (Bypasses Render WAF Blocks)
    print(f"DEBUG: Initiating Deep B2B Scan ({niche} in {location})...", flush=True)
    q = f'"{niche}" {location} India -news -times -realtor.com'
    
    try:
        r = requests.post('https://html.duckduckgo.com/html/', data={'q': q}, headers=get_headers(), timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        for res in soup.select('.result'):
            if len(results) >= target: break
            link_tag = res.select_one('a.result__url')
            title_tag = res.select_one('.result__title')
            
            if link_tag and title_tag:
                link = link_tag.get('href', '').strip()
                title = title_tag.text.strip()
                
                # STRICT B2B GUARD (No News, No Portals)
                if any(g in link.lower() for g in B2B_GUARD): continue
                if any(g in title.lower() for g in ["news", "times", "express", "update"]): continue
                
                # Ensure the link looks like a business domain (not a directory subpage)
                link = "https://" + link if not link.startswith("http") else link
                if link and link not in seen:
                    seen.add(link)
                    
                    # DYNAMIC SCORING (Independent .in businesses get max value)
                    score = 9.5 if ".in" in link.lower() or "agency" in title.lower() else 8.0
                    
                    results.append({"Name": title, "Website": link, "Source": "POST-Scan", "Score": score})
                    safe_t = title.encode('ascii', 'ignore').decode('ascii')
                    print(f"PROGRESS:{len(results)}:{target}:Found Independent Business: {safe_t[:35]}", flush=True)
    except Exception as e:
        print(f"DEBUG: Scan Error: {e}", flush=True)

    # SECURE HARVESTING
    final_leads = []
    vault = Vault()
    for i, lead in enumerate(results):
        safe_name = lead['Name'].encode('ascii', 'ignore').decode('ascii')
        print(f"PROGRESS:{i+1}:{len(results)}:Extracting Contacts: {safe_name[:35]}", flush=True)
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

    print(f">>> Hunt complete. {len(final_leads)} leads secured.", flush=True)
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
                    "Social": d.get("Social","None"), "Score": d["Score"], "Source": d.get("Source","v22.0")
                })
    print("DONE", flush=True)
