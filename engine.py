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

# Engine v25.0: THE RESILIENT VOYAGER
# Primary: Yahoo Search | Secondary: AOL Search
# Specifically tuned for high-latency/blocked cloud environments like Render.

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_STORE = "/data" if os.path.exists("/data") else PROJECT_ROOT
DB_PRODUCTION_PATH = os.path.join(DATA_STORE, "leads_production_v3.db")

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger("LEADSFLOW")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

B2B_GUARD = [
    "news", "times", "express", "lokmat", "livemint", "ndtv", "realtor.com", "zillow", "wikipedia", 
    "facebook", "instagram", "youtube", "linkedin", "magicbricks", "99acres", "housing.com", 
    "justdial", "indiamart", "sulekha", "quikr", "amazon", "flipkart", "yelp", "tripadvisor"
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive"
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
                             (niche, location, lead["Name"], lead.get("Website","None"), lead.get("Phone","None"), lead.get("Email","None"), lead.get("Social","None"), lead.get("Score", 5.0), lead.get("Source", "v25.0")))
                conn.commit()
        except: pass

def extract_contacts(html, url):
    email_pattern = r'[a-zA-Z0-9._%+-]+@(?!(?:sentry|github|w3|bootstrap|email|png|jpg|js|gif|css|example)\.)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    phone_pattern = r'(?:\+91|91|0)?[6-9]\d{9}'
    emails = re.findall(email_pattern, html)
    phones = re.findall(phone_pattern, html)
    e = emails[0] if emails else "None"
    p = phones[0] if phones else "None"
    if e.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.css', '.js', '.pdf')): e = "None"
    return e, p

def hunt_provider(engine_name, search_url, q, target, seen):
    """Generic Scraper for traditional search engines"""
    results = []
    print(f"DEBUG: Attempting {engine_name} Strategy...", flush=True)
    try:
        r = requests.get(search_url, headers=get_headers(), timeout=12)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            # Custom selectors for Yahoo/AOL
            links = []
            if "yahoo" in engine_name.lower() or "aol" in engine_name.lower():
                links = soup.select('h3.title a') or soup.find_all('a', class_='ac-algo')
            
            for link_tag in links:
                if len(results) >= target: break
                link = link_tag.get('href', '')
                title = link_tag.text
                
                # Cleanup potential redirect links
                if "/RU=" in link:
                    match = re.search(r'RU=(.*?)/RK=', link)
                    if match: link = requests.utils.unquote(match.group(1))
                
                if not link.startswith('http'): continue
                if any(g in link.lower() for g in B2B_GUARD): continue
                
                if link and link not in seen:
                    seen.add(link)
                    results.append({"Name": title, "Website": link, "Source": f"{engine_name}-Scout", "Score": 8.0})
                    print(f"PROGRESS:Found: {title[:30]}...", flush=True)
        else:
            print(f"DEBUG: {engine_name} returned status {r.status_code}", flush=True)
    except Exception as e:
        print(f"DEBUG: {engine_name} Error: {e}", flush=True)
    return results

def hunt(niche, location, target):
    print(f">>> Voyager Engine v25.0 Active. Target: {target} leads.", flush=True)
    results, seen = [], set()
    q = f'"{niche}" {location} India'

    # PROVIDER 1: YAHOO SEARCH (Highly Resilient)
    yahoo_url = f"https://search.yahoo.com/search?p={requests.utils.quote(q)}"
    results.extend(hunt_provider("Yahoo", yahoo_url, q, target, seen))

    # PROVIDER 2: AOL SEARCH (Fallback)
    if len(results) < target:
        aol_url = f"https://search.aol.com/aol/search?q={requests.utils.quote(q)}"
        results.extend(hunt_provider("AOL", aol_url, q, target - len(results), seen))

    if not results:
        print("DEBUG: All providers blocked or timed out. Last attempt: Manual Search Mirrors...", flush=True)

    # CONTACT EXTRACTION
    final_leads = []
    vault = Vault()
    for i, lead in enumerate(results):
        safe_name = lead['Name'].encode('ascii', 'ignore').decode('ascii')
        print(f"PROGRESS:{i+1}:{len(results)}:Harvesting: {safe_name[:30]}...", flush=True)
        try:
            time.sleep(random.uniform(0.5, 1.2))
            r = requests.get(lead['Website'], headers=get_headers(), timeout=10)
            e, p = extract_contacts(r.text if r.status_code == 200 else "", lead['Website'])
            lead.update({"Email": e, "Phone": f"W:{p}" if p != "None" else "None", "Social": "None"})
            vault.save(niche, location, lead)
            final_leads.append(lead)
        except:
            lead.update({"Email": "None", "Phone": "None", "Social": "None"})
            vault.save(niche, location, lead)
            final_leads.append(lead)

    print(f">>> Voyager Session Finished. {len(final_leads)} leads secured.", flush=True)
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
                    "Social": d.get("Social","None"), "Score": d["Score"], "Source": d.get("Source", "v25.0")
                })
    print("DONE", flush=True)
