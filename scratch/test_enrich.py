import requests
import time
import re

# Test: Can we enrich business names with contact info using DDGS?
print("=== Contact Enrichment Test ===")

businesses = ["Nirula's Delhi", "Haldiram Delhi", "Park Baluchi Delhi", "Sagar Ratna Delhi"]

try:
    from ddgs import DDGS
    
    phone_re = re.compile(r'(\+91[\s-]?\d{5}[\s-]?\d{5}|\b0\d{2,4}[\s-]?\d{6,8}\b|\b\d{10}\b)')
    email_re = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')
    
    for biz in businesses:
        print(f"\n--- {biz} ---")
        try:
            results = DDGS().text(f"{biz} contact phone number", max_results=5)
            phones = set()
            emails = set()
            website = "None"
            
            for r in results:
                snippet = r.get('body', '') + ' ' + r.get('title', '')
                url = r.get('href', '')
                
                # Extract phones from snippet
                found_phones = phone_re.findall(snippet)
                phones.update(found_phones)
                
                # Extract emails
                found_emails = email_re.findall(snippet)
                emails.update(found_emails)
                
                # First non-platform URL = likely their website
                if website == "None" and url and not any(p in url for p in ['facebook','instagram','youtube','wikipedia']):
                    website = url
                    
            print(f"  Phones: {list(phones)[:2]}")
            print(f"  Emails: {list(emails)[:2]}")
            print(f"  Website: {website[:60]}")
        except Exception as e:
            print(f"  Error: {e}")
        time.sleep(2)
        
except ImportError:
    print("DDGS not available")
