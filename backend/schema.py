"""SQLite schema for SentinelGraph. All tables from Architecture section 4 plus supporting tables."""
import sqlite3
from pathlib import Path

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS roles (
    role_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    permission_set TEXT NOT NULL  -- JSON: list of allowed actions and scopes
);

CREATE TABLE IF NOT EXISTS branches (
    branch_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    city TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS employees (
    employee_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role_id TEXT NOT NULL REFERENCES roles(role_id),
    branch_id TEXT NOT NULL REFERENCES branches(branch_id),
    manager_id TEXT REFERENCES employees(employee_id),
    active_from TEXT NOT NULL,
    active_to TEXT,
    event_time TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    source_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    segment TEXT NOT NULL,
    branch_id TEXT NOT NULL REFERENCES branches(branch_id),
    risk_band TEXT NOT NULL DEFAULT 'standard',
    event_time TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    source_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS accounts (
    account_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    account_type TEXT NOT NULL,
    opened_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    event_time TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    source_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS beneficiaries (
    beneficiary_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(account_id),
    destination_account TEXT NOT NULL,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL REFERENCES employees(employee_id),
    event_time TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    source_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    txn_id TEXT PRIMARY KEY,
    source_account TEXT NOT NULL REFERENCES accounts(account_id),
    destination_account TEXT NOT NULL,
    amount REAL NOT NULL,
    currency TEXT NOT NULL DEFAULT 'INR',
    timestamp TEXT NOT NULL,
    channel TEXT NOT NULL DEFAULT 'branch',
    status TEXT NOT NULL DEFAULT 'completed',
    scenario_label TEXT,
    is_recurring INTEGER NOT NULL DEFAULT 0,
    event_time TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    source_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS access_events (
    event_id TEXT PRIMARY KEY,
    employee_id TEXT NOT NULL REFERENCES employees(employee_id),
    customer_id TEXT REFERENCES customers(customer_id),
    account_id TEXT REFERENCES accounts(account_id),
    action TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    result TEXT NOT NULL DEFAULT 'success',
    device_id TEXT,
    ip_hash TEXT,
    scenario_label TEXT,
    event_time TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    source_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS profile_changes (
    change_id TEXT PRIMARY KEY,
    employee_id TEXT NOT NULL REFERENCES employees(employee_id),
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    field TEXT NOT NULL,
    old_value_hash TEXT,
    new_value_hash TEXT,
    timestamp TEXT NOT NULL,
    scenario_label TEXT,
    event_time TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    source_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS login_events (
    event_id TEXT PRIMARY KEY,
    employee_id TEXT NOT NULL REFERENCES employees(employee_id),
    timestamp TEXT NOT NULL,
    result TEXT NOT NULL,
    device_id TEXT,
    ip_hash TEXT,
    scenario_label TEXT,
    event_time TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    source_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS findings (
    finding_id TEXT PRIMARY KEY,
    rule_id TEXT NOT NULL,
    rule_version TEXT NOT NULL DEFAULT '1.0',
    severity TEXT NOT NULL,
    confidence REAL NOT NULL,
    status TEXT NOT NULL,  -- triggered, not_triggered, insufficient_evidence
    employee_id TEXT,
    account_id TEXT,
    customer_id TEXT,
    explanation TEXT,
    explanation_facts TEXT,  -- JSON
    derived_facts TEXT,      -- JSON
    thresholds TEXT,         -- JSON
    recommended_action TEXT,
    score_breakdown TEXT,    -- JSON: line items
    total_score INTEGER,
    created_at TEXT NOT NULL,
    event_time TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    source_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS finding_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    finding_id TEXT NOT NULL REFERENCES findings(finding_id),
    event_id TEXT NOT NULL,
    event_type TEXT NOT NULL,  -- access, transaction, profile_change, login
    relationship_type TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
    alert_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    severity TEXT NOT NULL,
    confidence REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',  -- new, investigating, dismissed, escalated
    owner_id TEXT,
    employee_id TEXT,
    account_id TEXT,
    customer_id TEXT,
    destination_account TEXT,
    rule_ids TEXT NOT NULL,  -- JSON array
    evidence_count INTEGER NOT NULL DEFAULT 0,
    evidence_types TEXT,     -- JSON array of distinct types
    score_breakdown TEXT,    -- JSON
    total_score INTEGER NOT NULL DEFAULT 0,
    explanation TEXT,
    explanation_facts TEXT,  -- JSON
    recommended_action TEXT,
    dismiss_reason TEXT,
    time_window_start TEXT,
    time_window_end TEXT,
    scenario_label TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alert_findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id TEXT NOT NULL REFERENCES alerts(alert_id),
    finding_id TEXT NOT NULL REFERENCES findings(finding_id)
);

CREATE TABLE IF NOT EXISTS cases (
    case_id TEXT PRIMARY KEY,
    alert_id TEXT REFERENCES alerts(alert_id),
    owner_id TEXT,
    status TEXT NOT NULL DEFAULT 'open',  -- open, investigating, resolved, dismissed, escalated
    dismiss_reason TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS case_notes (
    note_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(case_id),
    author_id TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor_id TEXT NOT NULL,
    action TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    before_status TEXT,
    after_status TEXT,
    rule_version TEXT,
    timestamp TEXT NOT NULL,
    metadata_json TEXT
);

-- supporting tables for rule suppressions
CREATE TABLE IF NOT EXISTS case_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id TEXT NOT NULL REFERENCES employees(employee_id),
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    valid_from TEXT NOT NULL,
    valid_to TEXT NOT NULL,
    source_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS batch_jobs (
    job_id TEXT PRIMARY KEY,
    operator_id TEXT NOT NULL REFERENCES employees(employee_id),
    approved INTEGER NOT NULL DEFAULT 0,
    window_start TEXT NOT NULL,
    window_end TEXT NOT NULL,
    source_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS oncall_approvals (
    ticket_id TEXT PRIMARY KEY,
    employee_id TEXT NOT NULL REFERENCES employees(employee_id),
    window_start TEXT NOT NULL,
    window_end TEXT NOT NULL,
    source_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS quarantine (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT NOT NULL,
    record_json TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ingestion_batches (
    batch_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT NOT NULL,
    record_count INTEGER NOT NULL DEFAULT 0,
    quarantined_count INTEGER NOT NULL DEFAULT 0,
    started_at TEXT NOT NULL,
    completed_at TEXT
);

-- indexes for common queries
CREATE INDEX IF NOT EXISTS idx_access_employee ON access_events(employee_id);
CREATE INDEX IF NOT EXISTS idx_access_customer ON access_events(customer_id);
CREATE INDEX IF NOT EXISTS idx_access_timestamp ON access_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_txn_source ON transactions(source_account);
CREATE INDEX IF NOT EXISTS idx_txn_dest ON transactions(destination_account);
CREATE INDEX IF NOT EXISTS idx_txn_timestamp ON transactions(timestamp);
CREATE INDEX IF NOT EXISTS idx_login_employee ON login_events(employee_id);
CREATE INDEX IF NOT EXISTS idx_profile_employee ON profile_changes(employee_id);
CREATE INDEX IF NOT EXISTS idx_findings_rule ON findings(rule_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_audit_target ON audit_log(target_type, target_id);
"""


def create_schema(db_path: Path):
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA)
    conn.close()


if __name__ == "__main__":
    db = Path(__file__).parent / "sentinelgraph.db"
    if db.exists():
        db.unlink()
    create_schema(db)
    print(f"Schema created at {db}")
