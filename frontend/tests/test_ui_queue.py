import os
import re
import time
import subprocess
import socket
from playwright.sync_api import Page, expect

def test_alert_queue(page: Page):
    # This test assumes the backend and frontend are already running
    # The verify script will manage the processes
    
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    
    errors = []
    page.on("pageerror", lambda err: errors.append(err))
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    
    # Warm up Vite compilation
    try:
        page.goto(frontend_url + "/alerts")
        page.wait_for_selector("table tbody tr", timeout=15000)
    except Exception:
        pass
        
    # Reset demo before testing
    import urllib.request
    try:
        req = urllib.request.Request(f'{frontend_url}/api/demo/reset', method='POST', headers={'x-user-role': 'admin'})
        urllib.request.urlopen(req)
    except Exception as e:
        pass
        
    start_time = time.time()
    
    page.goto(frontend_url + "/alerts")
    
    try:
        page.wait_for_selector("table tbody tr")
    except Exception as e:
        print("Console Errors:", errors)
        raise
    load_time = time.time() - start_time
    assert load_time < 5.0, f"Load time too slow: {load_time}s"
    
    # Check no console errors (ignoring 404s for favicon etc if any)
    actual_errors = [e for e in errors if "favicon" not in str(e).lower()]
    assert len(actual_errors) == 0, f"Console errors found: {actual_errors}"
    
    # Check S1 alert is at the top
    first_row = page.locator("table tbody tr").first
    expect(first_row).to_contain_text("S1")
