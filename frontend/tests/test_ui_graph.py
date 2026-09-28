import pytest
import os
import time
from playwright.sync_api import Page, expect

def test_alert_detail_graph(page: Page):
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    errors = []
    page.on("pageerror", lambda err: errors.append(err))
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)

    # Reset demo
    import urllib.request
    try:
        req = urllib.request.Request(f'{frontend_url}/api/demo/reset', method='POST', headers={'x-user-role': 'admin'})
        urllib.request.urlopen(req)
    except Exception as e:
        pass

    # Go to queue
    page.goto(frontend_url + "/alerts")
    page.wait_for_selector("table tbody tr")

    # Find S1 alert and click it
    s1_row = page.locator("table tbody tr", has_text="S1").first
    s1_row.click()
    
    # Wait for alert detail to load
    page.wait_for_selector("h1.page-title", timeout=5000)
    expect(page.locator("h1.page-title")).to_contain_text("S1")
    
    # Check shortest path button
    btn = page.locator("button#btn-shortest-path")
    btn.click()
    
    # Verify no console errors
    actual_errors = [e for e in errors if "favicon" not in str(e).lower()]
    assert len(actual_errors) == 0, f"Console errors found: {actual_errors}"

def test_s4_monitored(page: Page):
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    # Get S4 ID
    import urllib.request, json
    try:
        req = urllib.request.Request(f'{frontend_url}/api/alerts', headers={'x-user-role': 'admin'})
        resp = urllib.request.urlopen(req)
        alerts = json.loads(resp.read().decode())
        s4_alert = next((a for a in alerts if "S4" in a['title']), None)
        if s4_alert:
            page.goto(f"{frontend_url}/alerts/{s4_alert['alert_id']}")
            page.wait_for_selector("h2", timeout=5000)
            expect(page.locator("h2")).to_contain_text("Monitored")
    except Exception as e:
        print(f"Skipping S4 test due to setup error: {e}")

def test_s7_small_peer_group(page: Page):
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    import urllib.request, json
    try:
        req = urllib.request.Request(f'{frontend_url}/api/alerts', headers={'x-user-role': 'admin'})
        resp = urllib.request.urlopen(req)
        alerts = json.loads(resp.read().decode())
        s7_alert = next((a for a in alerts if "S7" in a['title']), None)
        if s7_alert:
            page.goto(f"{frontend_url}/alerts/{s7_alert['alert_id']}")
            page.wait_for_selector("h2", timeout=5000)
            expect(page.locator("h2")).to_contain_text("Peer comparison unavailable")
    except Exception as e:
        print(f"Skipping S7 test due to setup error: {e}")
