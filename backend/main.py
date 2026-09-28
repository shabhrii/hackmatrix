import sqlite3
import time
from pathlib import Path
from contextlib import contextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from typing import Optional, List, Dict
import json
import uuid

DB_PATH = Path(__file__).parent / "sentinelgraph.db"
DEMO_USERS = {
    "analyst": {"user_id": "U-001", "name": "Priya Sharma", "role": "analyst"},
    "supervisor": {"user_id": "U-002", "name": "Rajesh Menon", "role": "supervisor"},
    "admin": {"user_id": "U-003", "name": "Kavita Desai", "role": "admin"},
}

app = FastAPI(title="SentinelGraph", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@contextmanager
def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
    finally:
        conn.close()


@app.middleware("http")
async def inject_user(request: Request, call_next):
    role = request.headers.get("x-user-role", "analyst")
    user = DEMO_USERS.get(role, DEMO_USERS["analyst"])
    request.state.user = user
    response = await call_next(request)
    return response


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": time.time()}


@app.get("/me")
def me(request: Request):
    return request.state.user

from pydantic import BaseModel

def log_audit(conn, actor_id, action, target_type, target_id, meta):
    conn.execute('''
        INSERT INTO audit_log (actor_id, action, target_type, target_id, timestamp, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (actor_id, action, target_type, target_id, str(time.time()), json.dumps(meta)))

@app.post("/demo/reset")
def reset_demo(request: Request):
    if request.state.user["role"] != "admin":
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Admin only")
        
    import subprocess
    import sys
    ROOT = Path(__file__).parent.parent
    subprocess.run([sys.executable, str(ROOT / "scripts" / "reset_demo.py")], check=True)
    subprocess.run([sys.executable, "-m", "pytest", str(ROOT / "backend" / "tests" / "test_engine.py")])
    return {"status": "ok"}

@app.get("/alerts")
def get_alerts():
    with get_db() as conn:
        alerts = conn.execute("SELECT * FROM alerts").fetchall()
        return [dict(a) for a in alerts]

@app.get("/alerts/{alert_id}")
def get_alert(alert_id: str):
    with get_db() as conn:
        alert = conn.execute("SELECT * FROM alerts WHERE alert_id = ?", (alert_id,)).fetchone()
        return dict(alert) if alert else {}

@app.get("/alerts/{alert_id}/evidence")
def get_alert_evidence(alert_id: str):
    with get_db() as conn:
        evs = conn.execute('''
            SELECT fe.* FROM finding_evidence fe
            JOIN alert_findings af ON fe.finding_id = af.finding_id
            WHERE af.alert_id = ?
            GROUP BY fe.event_id
        ''', (alert_id,)).fetchall()
        return [dict(e) for e in evs]

class CaseCreate(BaseModel):
    alert_id: str

@app.post("/cases")
def create_case(case: CaseCreate, request: Request):
    case_id = f"CASE-{uuid.uuid4().hex[:8]}"
    with get_db() as conn:
        conn.execute("INSERT INTO cases (case_id, owner_id, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                     (case_id, request.state.user["user_id"], "new", str(time.time()), str(time.time())))
        log_audit(conn, request.state.user["user_id"], "create_case", "case", case_id, {"alert_id": case.alert_id})
        conn.commit()
    return {"case_id": case_id}

class CaseUpdate(BaseModel):
    owner_id: Optional[str] = None
    status: Optional[str] = None
    reason: Optional[str] = None

@app.patch("/cases/{case_id}")
def update_case(case_id: str, case: CaseUpdate, request: Request):
    from fastapi import HTTPException
    with get_db() as conn:
        updates = []
        params = []
        if case.owner_id:
            updates.append("owner_id = ?")
            params.append(case.owner_id)
        if case.status:
            if case.status == "dismissed":
                valid_reasons = ["legitimate batch", "approved access", "duplicate", "insufficient evidence"]
                if case.reason not in valid_reasons:
                    raise HTTPException(status_code=400, detail="Invalid dismiss reason")
            updates.append("status = ?")
            params.append(case.status)
        
        if updates:
            updates.append("updated_at = ?")
            params.append(str(time.time()))
            params.append(case_id)
            conn.execute(f"UPDATE cases SET {', '.join(updates)} WHERE case_id = ?", params)
            log_audit(conn, request.state.user["user_id"], "update_case", "case", case_id, case.dict())
            conn.commit()
            
        if case.status == "escalated":
            return {"status": "escalated", "export": "Preview of export"}
    return {"status": "ok"}

class NoteCreate(BaseModel):
    body: str

@app.post("/cases/{case_id}/notes")
def create_note(case_id: str, note: NoteCreate, request: Request):
    with get_db() as conn:
        conn.execute("INSERT INTO case_notes (note_id, case_id, author_id, body, created_at) VALUES (?, ?, ?, ?, ?)",
                     (str(uuid.uuid4()), case_id, request.state.user["user_id"], note.body, str(time.time())))
        log_audit(conn, request.state.user["user_id"], "add_note", "case", case_id, {})
        conn.commit()
    return {"status": "ok"}

@app.get("/cases/{case_id}/export")
def export_case(case_id: str, format: str = "json"):
    header = "This data is synthetic."
    if format == "md":
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(f"# Case Export\n\n{header}\n\nCase ID: {case_id}\n")
    return {"header": header, "case_id": case_id, "notes": [], "events": []}

@app.get("/graph")
def graph_query(): return {}

@app.get("/timeline")
def timeline_query(): return []

@app.get("/metrics/rule-performance")
def rule_performance(): return {}

@app.get("/rules")
def get_rules(): return {}

@app.get("/monitored")
def get_monitored(): return []
