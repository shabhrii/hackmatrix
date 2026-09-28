import pytest
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from engine import Engine

@pytest.fixture
def db():
    db_path = BACKEND / "sentinelgraph.db"
    return db_path

@pytest.fixture
def engine(db):
    return Engine(db)

def test_engine_idempotent(engine, db):
    # Run once
    engine.run_rules()
    conn = sqlite3.connect(db)
    count1 = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
    
    # Run twice
    engine.run_rules()
    count2 = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
    
    assert count1 == count2
    
def test_no_duplicate_evidence(engine, db):
    conn = sqlite3.connect(db)
    # Check finding_evidence ledger for duplicates
    dups = conn.execute("""
        SELECT finding_id, event_id, COUNT(*) 
        FROM finding_evidence 
        GROUP BY finding_id, event_id 
        HAVING COUNT(*) > 1
    """).fetchall()
    assert len(dups) == 0

def test_golden_file_matches(engine, db):
    engine.run_rules()
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    
    golden_file = BACKEND / "tests" / "expected_alerts.json"
    with open(golden_file) as f:
        golden = json.load(f)
        
    for sc, data in golden.items():
        if data.get("alert_generated", False):
            # Check alert exists
            row = conn.execute("SELECT * FROM alerts WHERE scenario_label = ?", (sc,)).fetchone()
            assert row is not None, f"Expected alert for {sc}"
            
            if "score" in data:
                assert row["total_score"] == data["score"], f"Score mismatch for {sc}"
            if "confidence" in data:
                assert abs(row["confidence"] - data["confidence"]) < 0.01
            if "severity" in data:
                assert row["severity"] == data["severity"]
        else:
            row = conn.execute("SELECT * FROM alerts WHERE scenario_label = ?", (sc,)).fetchone()
            assert row is None, f"Did not expect alert for {sc}"

        # check S4 informational
        if sc == "S4":
            fnd = conn.execute("SELECT * FROM findings WHERE finding_id = 'FND-S4-R-02'").fetchone()
            if fnd:
                assert fnd["status"] == "informational"
        # check S5 manual review
        if sc == "S5":
            fnd = conn.execute("SELECT * FROM findings WHERE finding_id = 'FND-S5-R-03'").fetchone()
            if fnd:
                assert fnd["recommended_action"] == "manual_review"

