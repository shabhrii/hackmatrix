"""Verification gate runner. Usage: python scripts/verify.py --cp N"""
import argparse
import subprocess
import sys
import os
import time
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"


def run(cmd, cwd=None, capture=False):
    result = subprocess.run(
        cmd, cwd=cwd, shell=isinstance(cmd, str),
        capture_output=capture, text=capture,
    )
    return result


def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}" + (f" -- {detail}" if detail else ""))
    return condition


def gate_cp0():
    print("\n--- CP0: Bootstrap and lock ---\n")
    python = sys.executable
    npm = "npm.cmd" if os.name == "nt" else "npm"
    ok = True

    # setup.py runs
    r = run([python, str(ROOT / "scripts" / "setup.py")], capture=True)
    ok &= check("setup.py succeeds", r.returncode == 0, r.stderr[-200:] if r.returncode != 0 else "")

    # backend health
    import socket
    def find_free_port():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    port = find_free_port()
    proc = subprocess.Popen(
        [python, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=str(BACKEND),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    time.sleep(3)
    health_ok = False
    try:
        resp = urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=5)
        health_ok = resp.status == 200
    except Exception:
        pass
    finally:
        proc.terminate()
        proc.wait()
    ok &= check("/health returns 200", health_ok)

    # frontend builds
    r = run([npm, "run", "build"], cwd=str(FRONTEND), capture=True)
    ok &= check("frontend builds", r.returncode == 0, r.stderr[-200:] if r.returncode != 0 else "")

    # key files exist
    for f in ["DECISIONS.md", "DEBUG_LOG.md", "README.md", ".gitignore", ".gitattributes"]:
        ok &= check(f"{f} exists", (ROOT / f).exists())

    for f in ["FIN-04-SentinelGraph.md", "Architecture.md", "Delivery-Phases.md", "Detection-Rules.md", "Product-Design-Specification.md"]:
        ok &= check(f"docs/{f} exists", (ROOT / "docs" / f).exists())

    return ok


def gate_cp1():
    print("\n--- CP1: Schema and deterministic seed ---\n")
    import csv
    import hashlib
    import json
    python = sys.executable
    ok = True
    seed_dir = ROOT / "data" / "seed"

    # run generator twice, compare hashes
    run([python, str(ROOT / "scripts" / "generate_seed.py")], capture=True)
    hashes_1 = {}
    for f in seed_dir.glob("*.csv"):
        hashes_1[f.name] = hashlib.sha256(f.read_bytes()).hexdigest()
    for f in seed_dir.glob("*.json"):
        hashes_1[f.name] = hashlib.sha256(f.read_bytes()).hexdigest()

    run([python, str(ROOT / "scripts" / "generate_seed.py")], capture=True)
    deterministic = True
    for f in seed_dir.glob("*.csv"):
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        if hashes_1.get(f.name) != h:
            deterministic = False
    for f in seed_dir.glob("*.json"):
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        if hashes_1.get(f.name) != h:
            deterministic = False
    ok &= check("deterministic generation (identical hashes)", deterministic)

    # check row counts
    def csv_rows(filename):
        with open(seed_dir / filename, encoding="utf-8") as f:
            return list(csv.DictReader(f))

    employees = csv_rows("employees.csv")
    ok &= check(f"employees ~60 (got {len(employees)})", 40 <= len(employees) <= 80)

    customers = csv_rows("customers.csv")
    ok &= check(f"customers ~400 (got {len(customers)})", 350 <= len(customers) <= 450)

    accs = csv_rows("accounts.csv")
    ok &= check(f"accounts ~600 (got {len(accs)})", 550 <= len(accs) <= 650)

    txns = csv_rows("transactions.csv")
    ok &= check(f"transactions ~6000+ (got {len(txns)})", len(txns) >= 5500)

    access = csv_rows("access_events.csv")
    ok &= check(f"access events ~12000+ (got {len(access)})", len(access) >= 11000)

    # check all 8 scenarios present
    all_labels = set()
    for row in access:
        if row.get("scenario_label"):
            all_labels.add(row["scenario_label"])
    for row in txns:
        if row.get("scenario_label"):
            all_labels.add(row["scenario_label"])
    logins = csv_rows("login_events.csv")
    for row in logins:
        if row.get("scenario_label"):
            all_labels.add(row["scenario_label"])
    changes = csv_rows("profile_changes.csv")
    for row in changes:
        if row.get("scenario_label"):
            all_labels.add(row["scenario_label"])

    for s in ["S1", "S2", "S2b", "S3", "S4", "S5", "S6", "S7", "S8"]:
        ok &= check(f"scenario {s} present", s in all_labels)

    # check specific IDs exist
    access_by_id = {r["event_id"]: r for r in access}
    ok &= check("A-19 exists", "A-19" in access_by_id)
    if "A-19" in access_by_id:
        ok &= check("A-19 timestamp is 14:02", "T14:02:" in access_by_id["A-19"]["timestamp"])
        ok &= check("A-19 employee is E-0417", access_by_id["A-19"]["employee_id"] == "E-0417")
        ok &= check("A-19 customer is C-2210", access_by_id["A-19"]["customer_id"] == "C-2210")

    change_by_id = {r["change_id"]: r for r in changes}
    ok &= check("P-07 exists", "P-07" in change_by_id)

    txn_by_id = {r["txn_id"]: r for r in txns}
    ok &= check("T-88 exists", "T-88" in txn_by_id)
    if "T-88" in txn_by_id:
        ok &= check("T-88 destination is ACC-9907", txn_by_id["T-88"]["destination_account"] == "ACC-9907")

    emp_by_id = {r["employee_id"]: r for r in employees}
    ok &= check("E-0417 exists", "E-0417" in emp_by_id)
    ok &= check("E-0880 exists", "E-0880" in emp_by_id)

    cust_by_id = {r["customer_id"]: r for r in customers}
    ok &= check("C-2210 exists", "C-2210" in cust_by_id)

    acc_by_id = {r["account_id"]: r for r in accs}
    ok &= check("ACC-9907 exists", "ACC-9907" in acc_by_id)

    # check supporting data
    with open(seed_dir / "batch_jobs.json", encoding="utf-8") as f:
        batch_jobs = json.load(f)
    ok &= check("JOB-ME-0930 exists", any(j["job_id"] == "JOB-ME-0930" for j in batch_jobs))

    with open(seed_dir / "oncall_approvals.json", encoding="utf-8") as f:
        oncall = json.load(f)
    ok &= check("TKT-4471 exists", any(t["ticket_id"] == "TKT-4471" for t in oncall))

    # golden file exists
    ok &= check("expected_alerts.json exists", (ROOT / "backend" / "tests" / "expected_alerts.json").exists())

    # bad data exists
    bad_dir = seed_dir / "bad"
    ok &= check("bad data directory exists", bad_dir.exists())
    bad_files = list(bad_dir.glob("*.csv"))
    ok &= check(f"bad data files exist (got {len(bad_files)})", len(bad_files) >= 5)

    # schema can be created
    sys.path.insert(0, str(BACKEND))
    from schema import create_schema
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        create_schema(tmp_path)
        ok &= check("schema creates without error", True)
    except Exception as e:
        ok &= check("schema creates without error", False, str(e))
    finally:
        tmp_path.unlink(missing_ok=True)

    return ok


def gate_cp2():
    print("\n--- CP2: Ingestion and normalization ---\n")
    import time as _time
    import json
    python = sys.executable
    ok = True

    # reset_demo.py should rebuild from scratch
    start = _time.time()
    r = run([python, str(ROOT / "scripts" / "reset_demo.py")], capture=True)
    elapsed = _time.time() - start
    ok &= check("reset_demo.py succeeds", r.returncode == 0, r.stderr[-200:] if r.returncode != 0 else "")
    ok &= check(f"reset under 10s ({elapsed:.1f}s)", elapsed < 10)

    # check zero quarantined records from good data
    import sqlite3
    db_path = BACKEND / "sentinelgraph.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    q_count = conn.execute("SELECT COUNT(*) FROM quarantine").fetchone()[0]
    ok &= check(f"zero quarantined from good data (got {q_count})", q_count == 0)

    # check data was actually loaded
    emp_count = conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
    ok &= check(f"employees loaded ({emp_count})", emp_count > 40)

    txn_count = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    ok &= check(f"transactions loaded ({txn_count})", txn_count > 5000)

    access_count = conn.execute("SELECT COUNT(*) FROM access_events").fetchone()[0]
    ok &= check(f"access events loaded ({access_count})", access_count > 11000)

    config_count = conn.execute("SELECT COUNT(*) FROM config").fetchone()[0]
    ok &= check(f"config loaded ({config_count})", config_count > 0)

    batch_count = conn.execute("SELECT COUNT(*) FROM batch_jobs").fetchone()[0]
    ok &= check(f"batch_jobs loaded ({batch_count})", batch_count > 0)

    # check provenance retained
    row = conn.execute("SELECT source_id, ingested_at FROM access_events LIMIT 1").fetchone()
    ok &= check("provenance: source_id present", row["source_id"] is not None and row["source_id"] != "")
    ok &= check("provenance: ingested_at present", row["ingested_at"] is not None and row["ingested_at"] != "")

    conn.close()

    # now load bad data and check quarantine
    sys.path.insert(0, str(BACKEND))
    from ingestion import ingest_bad_data
    bad_dir = ROOT / "data" / "seed" / "bad"
    ingest_bad_data(db_path, bad_dir)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    q_rows = conn.execute("SELECT * FROM quarantine").fetchall()
    bad_reasons = [r["reason"] for r in q_rows]
    ok &= check(f"bad data quarantined ({len(q_rows)} records)", len(q_rows) >= 5)

    # verify expected quarantine reasons
    with open(bad_dir / "expected_quarantine.json", encoding="utf-8") as f:
        expected = json.load(f)
    for exp in expected:
        found = any(exp["reason"] in r for r in bad_reasons)
        ok &= check(f"quarantine reason: {exp['reason']}", found)

    # pipeline did not crash
    ok &= check("pipeline did not crash on bad data", True)

    conn.close()
    return ok


def gate_cp3():
    print("\n--- CP3: Graph and feature layer ---\n")
    import sys
    sys.path.insert(0, str(BACKEND))
    from engine import Engine
    db_path = BACKEND / "sentinelgraph.db"
    
    ok = True
    try:
        eng = Engine(db_path)
        
        # S1 shortest path
        path = eng.shortest_evidence_path("E-0417", "T-88")
        ok &= check("shortest path from E-0417 to T-88", path == ["A-19", "P-07", "T-88"], str(path))
        
        # Peer percentile for E-0417 (S1)
        p1 = eng.peer_percentile("E-0417")
        ok &= check(f"E-0417 peer percentile is >= 99 (got {p1})", isinstance(p1, (int, float)) and p1 >= 99)
        
        # S4 operator inside peer baseline
        p4 = eng.peer_percentile("E-0880")
        ok &= check(f"S4 operator E-0880 inside baseline (got {p4})", isinstance(p4, (int, float)) and p4 <= 98)
        
        # Small peer group
        p7 = eng.peer_percentile("E-0901")
        ok &= check(f"small peer group returns 'unavailable' (got {p7})", p7 == "unavailable")
        
    except Exception as e:
        ok &= check("CP3 logic executed", False, str(e))
        
    return ok


def gate_cp4():
    print("\n--- CP4: Rule engine, ledger, scoring ---\n")
    import sys
    ok = True
    
    r = run([sys.executable, "-m", "pytest", str(ROOT / "backend" / "tests" / "test_engine.py")], capture=True)
    ok &= check("pytest reproduces testing matrix and golden file", r.returncode == 0, r.stderr[-200:] if r.returncode != 0 else r.stdout[-200:])
    return ok


GATES = {0: gate_cp0, 1: gate_cp1, 2: gate_cp2, 3: gate_cp3, 4: gate_cp4}


def main():
    parser = argparse.ArgumentParser(description="SentinelGraph verification gates")
    parser.add_argument("--cp", type=int, required=True, help="Checkpoint number to verify")
    args = parser.parse_args()

    target = args.cp
    all_ok = True
    for cp in range(target + 1):
        gate = GATES.get(cp)
        if gate is None:
            print(f"\n--- CP{cp}: gate not yet implemented ---\n")
            continue
        passed = gate()
        all_ok &= passed
        if passed:
            print(f"\n  CP{cp} PASSED\n")
        else:
            print(f"\n  CP{cp} FAILED\n")
            sys.exit(1)

    if all_ok:
        print(f"\nAll gates through CP{target} passed.")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
