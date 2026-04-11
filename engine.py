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

# Engine v22.1: THE ANTI-BLOCK SCOUT
# Improved for Render deployments with better proxy-like behavior and fallbacks.

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_STORE = "/data" if os.path.exists("/data") else PROJECT_ROOT
DB_PRODUCTION_PATH = os.path.join(DATA_STORE, "leads_production_v3.db")

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger("LEADSFLOW")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"
]

# THE B2B GUARD: Blocks all News, generic portals, and non-business entities
B2B_GUARD = [
    "news", "times", "express", "lokmat", "livemint", "ndtv", "realtor.com", "zillow", "wikipedia", 
    "facebook", "instagram", "youtube", "linkedin", "magicbricks", "99acres", "housing.com", 
    "justdial", "indiamart", "sulekha", "quikr", "amazon", "flipkart", "yelp", "tripadvisor"
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
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
        except Exception as e:
            print(f"VAULT INIT ERROR: {e}", flush=True)

    def save(self, niche, location, lead):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("INSERT OR REPLACE INTO leads_3 (niche, location, company_name, website, phone, email, social, score, source) VALUES (?,?,?,?,?,?,?,?,?)",
                             (niche, location, lead["Name"], lead.get("Website","None"), lead.get("Phone","None"), lead.get("Email","None"), lead.get("Social","None"), lead.get("Score", 5.0), lead.get("Source","v22.1")))
                conn.commit()
        except: pass

def extract_contacts(html, url):
    # Improved Regex for global and local patterns
    email_pattern = r'[a-zA-Z0-9._%+-]+@(?!(?:sentry|github|w3|bootstrap|email|png|jpg|js|gif|css|example)\.)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    phone_pattern = r'(?:\+91|91|0)?[6-9]\d{9}'
    
    emails = re.findall(email_pattern, html)
    phones = re.findall(phone_pattern, html)
    
    e = emails[0] if emails else "None"
    p = phones[0] if phones else "None"
    
    # Filter out common false positives
    if e.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.css', '.js')): e = "None"
    
    return e, p

def hunt(niche, location, target):
    print(f">>> Anti-Block Scout v22.1 Engaged. Target: {target} leads for {niche} in {location}", flush=True)
    results, seen = [], set()
    
    # ADVANCED SEARCH STRATEGY
    queries = [
        f'"{niche}" {location} India -news -times -facebook',
        f'site:.in "{niche}" {location} contact',
        f'"{niche}" {location} "office" "contact"'
    ]
    
    for q_idx, q in enumerate(queries):
        if len(results) >= target: break
        print(f"DEBUG: Executing Search Query {q_idx+1}/{len(queries)}...", flush=True)
        try:
            time.sleep(random.uniform(1, 3))
            # Trying DuckDuckGo with a simple GET first (less suspicious than POST for some WAFs)
            r = requests.get(f'https://html.duckduckgo.com/html/?q={q}', headers=get_headers(), timeout=15)
            
            if r.status_code != 200:
                print(f"DEBUG: DDG returned status {r.status_code}. Attempting POST fallback...", flush=True)
                r = requests.post('https://html.duckduckgo.com/html/', data={'q': q}, headers=get_headers(), timeout=15)
            
            if "ddg-captcha" in r.text.lower() or "verification" in r.text.lower():
                print("DEBUG: ALERT - Blocked by DDG (Captcha/Verification).", flush=True)
                continue

            soup = BeautifulSoup(r.text, 'html.parser')
            items = soup.select('.result')
            print(f"DEBUG: Found {len(items)} raw results in this page.", flush=True)

            for res in items:
                if len(results) >= target: break
                link_tag = res.select_one('a.result__url')
                title_tag = res.select_one('.result__title')
                
                if link_tag and title_tag:
                    link = link_tag.get('href', '').strip()
                    title = title_tag.text.strip()
                    
                    # Clean the link (sometimes DDG wraps it)
                    if "/l/?" in link:
                        match = re.search(r'uddg=(.*?)&', link)
                        if match: link = requests.utils.unquote(match.group(1))

                    # STRICT B2B GUARD
                    if any(g in link.lower() for g in B2B_GUARD): continue
                    
                    if link and link not in seen:
                        seen.add(link)
                        score = 9.0 if ".in" in link.lower() else 7.5
                        results.append({"Name": title, "Website": link, "Source": "DDG-Web", "Score": score})
                        safe_t = title.encode('ascii', 'ignore').decode('ascii')
                        print(f"PROGRESS:{len(results)}:{target}:Found Business: {safe_t[:30]}...", flush=True)
        except Exception as e:
            print(f"DEBUG: Query {q_idx+1} Error: {e}", flush=True)

    if not results:
        print("DEBUG: No results found after all queries. Potentially blocked or zero matches.", flush=True)

    # CONTACT EXTRACTION (Silent Phase)
    final_leads = []
    vault = Vault()
    for i, lead in enumerate(results):
        safe_name = lead['Name'].encode('ascii', 'ignore').decode('ascii')
        print(f"PROGRESS:{i+1}:{len(results)}:Harvesting: {safe_name[:30]}...", flush=True)
        try:
            time.sleep(random.uniform(1.0, 2.0))
            r = requests.get(lead['Website'], headers=get_headers(), timeout=10)
            e, p = extract_contacts(r.text if r.status_code == 200 else "", lead['Website'])
            lead.update({"Email": e, "Phone": f"W:{p}" if p != "None" else "None", "Social": "None"})
            vault.save(niche, location, lead)
            final_leads.append(lead)
        except:
            lead.update({"Email": "None", "Phone": "None", "Social": "None"})
            vault.save(niche, location, lead)
            final_leads.append(lead)

    print(f">>> Scout complete. {len(final_leads)} leads secured.", flush=True)
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
                    "Social": d.get("Social","None"), "Score": d["Score"], "Source": d.get("Source","v22.1")
                })
    print("DONE", flush=True)
