import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "backend"))
from main import app

client = TestClient(app)

def test_api_me():
    res = client.get("/me", headers={"x-user-role": "analyst"})
    assert res.status_code == 200
    assert res.json()["role"] == "analyst"
    
def test_reset_demo():
    res = client.post("/demo/reset", headers={"x-user-role": "admin"})
    assert res.status_code in (200, 201)

def test_s1_flow_end_to_end():
    # 1. reset demo
    client.post("/demo/reset", headers={"x-user-role": "admin"})
    
    # 2. Get alerts
    res = client.get("/alerts")
    assert res.status_code == 200
    alerts = res.json()
    assert len(alerts) > 0
    s1_alert = next((a for a in alerts if a.get("scenario_label") == "S1" or a.get("alert_id") == "ALT-S1"), None)
    assert s1_alert is not None
    alert_id = s1_alert["alert_id"]
    
    # 3. Get alert evidence
    res = client.get(f"/alerts/{alert_id}/evidence")
    assert res.status_code == 200
    evidence = res.json()
    assert len(evidence) == 3
    
    # 4. Create case
    res = client.post("/cases", json={"alert_id": alert_id})
    assert res.status_code in (200, 201)
    case_id = res.json()["case_id"]
    
    # 5. Assign case
    res = client.patch(f"/cases/{case_id}", json={"owner_id": "U-001"})
    assert res.status_code == 200
    
    # 6. Add note
    res = client.post(f"/cases/{case_id}/notes", json={"body": "Investigating S1"})
    assert res.status_code in (200, 201)
    
    # 7. Escalate case
    res = client.patch(f"/cases/{case_id}", json={"status": "escalated"})
    assert res.status_code == 200
    export_preview = res.json()
    assert "export" in export_preview
    
    # 8. Export JSON
    res = client.get(f"/cases/{case_id}/export?format=json")
    assert res.status_code == 200
    exp_json = res.json()
    assert "synthetic" in str(exp_json).lower()
    
    # 9. Export Markdown
    res = client.get(f"/cases/{case_id}/export?format=md")
    assert res.status_code == 200
    assert "synthetic" in res.text.lower()

def test_dismiss_requires_reason():
    res = client.post("/cases", json={"alert_id": "ALT-S3"})
    case_id = res.json()["case_id"]
    
    # Invalid dismiss (no reason)
    res = client.patch(f"/cases/{case_id}", json={"status": "dismissed"})
    assert res.status_code == 400
    
    # Invalid dismiss (bad reason)
    res = client.patch(f"/cases/{case_id}", json={"status": "dismissed", "reason": "just because"})
    assert res.status_code == 400
    
    # Valid dismiss
    res = client.patch(f"/cases/{case_id}", json={"status": "dismissed", "reason": "legitimate batch"})
    assert res.status_code == 200

def test_endpoints_exist():
    client.get("/graph").status_code
    client.get("/timeline").status_code
    client.get("/metrics/rule-performance").status_code
    client.get("/rules").status_code
    client.get("/monitored").status_code
    client.get("/alerts/ALT-S1").status_code

def test_role_checks():
    res = client.post("/demo/reset", headers={"x-user-role": "analyst"})
    # Analyst cannot reset
    assert res.status_code == 403
