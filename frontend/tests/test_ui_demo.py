import os
import pytest
from playwright.sync_api import Page, expect

def test_full_demo_sequence(page: Page):
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

    # 1. Queue -> S1 Alert -> Graph + Evidence -> Case creation
    page.goto(frontend_url + "/alerts")
    page.wait_for_selector("table tbody tr")
    s1_row = page.locator("table tbody tr", has_text="S1").first
    s1_row.click()
    page.wait_for_selector("h1.page-title")
    expect(page.locator("h1.page-title")).to_contain_text("S1")
    
    # Check graph and evidence
    page.locator("text=Shortest evidence path").click()
    # Just wait a moment for animation if any
    page.wait_for_timeout(500)
    
    # Assign Case + Note
    page.locator("text=Create Case").click()
    page.wait_for_selector("h1.page-title:has-text('Case Workspace')")
    
    # Note
    page.locator("#input-note").fill("Investigated S1 alert")
    page.locator("#btn-add-note").click()
    page.wait_for_selector("text=Investigated S1 alert")
    
    # Export bundle
    # Just check if button exists
    expect(page.locator("#btn-export-bundle")).to_be_visible()

    assert not errors, f"Console errors: {errors}"
