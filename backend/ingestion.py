"""Ingestion pipeline: loads CSV/JSON seed files into SQLite through validation and normalization."""
import csv
import json
import sqlite3
import re
from datetime import datetime, timezone
from pathlib import Path

ISO_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")


def parse_timestamp(val):
    if not val or not ISO_PATTERN.match(val):
        return None
    try:
        val = val.rstrip("Z")
        if "+" in val[10:]:
            val = val[:val.index("+", 10)]
        dt = datetime.fromisoformat(val).replace(tzinfo=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except (ValueError, TypeError):
        return None


def validate_required(row, fields, source_file):
    for field in fields:
        if field not in row or not row[field] or str(row[field]).strip() == "":
            return f"missing required field: {field}"
    return None


def validate_timestamp_fields(row, fields):
    for field in fields:
        val = row.get(field)
        if not val or val.strip() == "":
            continue
        normalized = parse_timestamp(val)
        if normalized is None:
            return f"invalid timestamp format in {field}"
        row[field] = normalized
    return None


def validate_amount(row):
    if "amount" in row:
        try:
            amt = float(row["amount"])
            if amt < 0:
                return "negative amount"
        except (ValueError, TypeError):
            return "invalid amount"
    return None


class Ingester:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(str(db_path))
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=OFF")
        self.known_employees = set()
        self.known_customers = set()
        self.known_accounts = set()
        self.known_event_ids = set()
        self._load_known_entities()

    def _load_known_entities(self):
        for table, col, target in [
            ("employees", "employee_id", self.known_employees),
            ("customers", "customer_id", self.known_customers),
            ("accounts", "account_id", self.known_accounts),
        ]:
            try:
                rows = self.conn.execute(f"SELECT {col} FROM {table}").fetchall()
                for r in rows:
                    target.add(r[0])
            except sqlite3.OperationalError:
                pass

        for table, col in [
            ("access_events", "event_id"),
            ("login_events", "event_id"),
            ("profile_changes", "change_id"),
        ]:
            try:
                rows = self.conn.execute(f"SELECT {col} FROM {table}").fetchall()
                for r in rows:
                    self.known_event_ids.add(r[0])
            except sqlite3.OperationalError:
                pass

    def quarantine(self, source_file, record, reason):
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.conn.execute(
            "INSERT INTO quarantine (source_file, record_json, reason, created_at) VALUES (?, ?, ?, ?)",
            (source_file, json.dumps(record, default=str), reason, now),
        )

    def log_batch(self, source_file, record_count, quarantined_count):
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.conn.execute(
            "INSERT INTO ingestion_batches (source_file, record_count, quarantined_count, started_at, completed_at) VALUES (?, ?, ?, ?, ?)",
            (source_file, record_count, quarantined_count, now, now),
        )

    def load_csv(self, filepath, table, required_fields, id_field, timestamp_fields=None, entity_refs=None):
        filepath = Path(filepath)
        if not filepath.exists():
            return 0, 0

        with open(filepath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        loaded = 0
        quarantined = 0

        for row in rows:
            # strip whitespace
            row = {k: (v.strip() if v else v) for k, v in row.items()}

            # required field validation
            err = validate_required(row, required_fields, filepath.name)
            if err:
                self.quarantine(filepath.name, row, err)
                quarantined += 1
                continue

            # timestamp normalization
            if timestamp_fields:
                err = validate_timestamp_fields(row, timestamp_fields)
                if err:
                    self.quarantine(filepath.name, row, err)
                    quarantined += 1
                    continue

            # amount validation
            err = validate_amount(row)
            if err:
                self.quarantine(filepath.name, row, err)
                quarantined += 1
                continue

            # entity reference validation
            if entity_refs:
                ref_err = None
                for ref_item in entity_refs:
                    if ref_item is None:
                        continue
                    field, known_set, label = ref_item
                    val = row.get(field, "")
                    if val and val.strip() != "" and val not in known_set:
                        ref_err = f"unknown entity reference: {label}={val}"
                        break
                if ref_err:
                    self.quarantine(filepath.name, row, ref_err)
                    quarantined += 1
                    continue

            # duplicate detection
            if id_field and id_field in row:
                id_val = row[id_field]
                if id_val in self.known_event_ids:
                    self.quarantine(filepath.name, row, f"duplicate event_id: {id_val}")
                    quarantined += 1
                    continue
                self.known_event_ids.add(id_val)

            # insert
            columns = list(row.keys())
            placeholders = ", ".join(["?"] * len(columns))
            col_names = ", ".join(columns)
            values = [row[c] for c in columns]

            try:
                self.conn.execute(
                    f"INSERT OR IGNORE INTO {table} ({col_names}) VALUES ({placeholders})",
                    values,
                )
                loaded += 1

                # track entity
                if table == "employees" and "employee_id" in row:
                    self.known_employees.add(row["employee_id"])
                elif table == "customers" and "customer_id" in row:
                    self.known_customers.add(row["customer_id"])
                elif table == "accounts" and "account_id" in row:
                    self.known_accounts.add(row["account_id"])

            except sqlite3.IntegrityError as e:
                self.quarantine(filepath.name, row, f"integrity error: {e}")
                quarantined += 1

        self.conn.commit()
        self.log_batch(filepath.name, loaded, quarantined)
        self.conn.commit()
        return loaded, quarantined

    def load_json(self, filepath, table, required_fields=None):
        filepath = Path(filepath)
        if not filepath.exists():
            return 0, 0

        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            data = [data]

        loaded = 0
        quarantined = 0

        for row in data:
            if required_fields:
                err = validate_required(row, required_fields, filepath.name)
                if err:
                    self.quarantine(filepath.name, row, err)
                    quarantined += 1
                    continue

            columns = list(row.keys())
            placeholders = ", ".join(["?"] * len(columns))
            col_names = ", ".join(columns)
            values = [row[c] for c in columns]

            try:
                self.conn.execute(
                    f"INSERT OR IGNORE INTO {table} ({col_names}) VALUES ({placeholders})",
                    values,
                )
                loaded += 1
            except sqlite3.IntegrityError as e:
                self.quarantine(filepath.name, row, f"integrity error: {e}")
                quarantined += 1

        self.conn.commit()
        self.log_batch(filepath.name, loaded, quarantined)
        self.conn.commit()
        return loaded, quarantined

    def close(self):
        self.conn.close()


def ingest_seed(db_path, seed_dir):
    """Load all seed data files in dependency order."""
    seed_dir = Path(seed_dir)
    ing = Ingester(db_path)

    # config first
    ing.load_json(seed_dir / "config.json", "config", ["key", "value"])

    # reference tables
    ing.load_csv(seed_dir / "branches.csv", "branches", ["branch_id", "name", "city"], None)
    ing.load_csv(seed_dir / "roles.csv", "roles", ["role_id", "name", "permission_set"], None)

    # entities in dependency order
    ing.load_csv(
        seed_dir / "employees.csv", "employees",
        ["employee_id", "name", "role_id", "branch_id"],
        "employee_id",
        timestamp_fields=["active_from", "active_to", "event_time", "ingested_at"],
    )

    ing.load_csv(
        seed_dir / "customers.csv", "customers",
        ["customer_id", "name", "segment", "branch_id"],
        "customer_id",
        timestamp_fields=["event_time", "ingested_at"],
    )

    ing.load_csv(
        seed_dir / "accounts.csv", "accounts",
        ["account_id", "customer_id", "account_type"],
        "account_id",
        timestamp_fields=["opened_at", "event_time", "ingested_at"],
        entity_refs=[("customer_id", ing.known_customers, "customer_id")],
    )

    ing.load_csv(
        seed_dir / "beneficiaries.csv", "beneficiaries",
        ["beneficiary_id", "account_id", "destination_account", "created_by"],
        "beneficiary_id",
        timestamp_fields=["created_at", "event_time", "ingested_at"],
        entity_refs=[("account_id", ing.known_accounts, "account_id")],
    )

    ing.load_csv(
        seed_dir / "transactions.csv", "transactions",
        ["txn_id", "source_account", "destination_account", "amount"],
        "txn_id",
        timestamp_fields=["timestamp", "event_time", "ingested_at"],
    )

    ing.load_csv(
        seed_dir / "access_events.csv", "access_events",
        ["event_id", "employee_id", "action"],
        "event_id",
        timestamp_fields=["timestamp", "event_time", "ingested_at"],
        entity_refs=[("employee_id", ing.known_employees, "employee_id")],
    )

    ing.load_csv(
        seed_dir / "profile_changes.csv", "profile_changes",
        ["change_id", "employee_id", "customer_id", "field"],
        "change_id",
        timestamp_fields=["timestamp", "event_time", "ingested_at"],
        entity_refs=[("employee_id", ing.known_employees, "employee_id")],
    )

    ing.load_csv(
        seed_dir / "login_events.csv", "login_events",
        ["event_id", "employee_id"],
        "event_id",
        timestamp_fields=["timestamp", "event_time", "ingested_at"],
        entity_refs=[("employee_id", ing.known_employees, "employee_id")],
    )

    # supporting tables
    ing.load_json(seed_dir / "case_assignments.json", "case_assignments", ["employee_id", "customer_id"])
    ing.load_json(seed_dir / "batch_jobs.json", "batch_jobs", ["job_id", "operator_id"])
    ing.load_json(seed_dir / "oncall_approvals.json", "oncall_approvals", ["ticket_id", "employee_id"])

    ing.close()


def ingest_bad_data(db_path, bad_dir):
    """Load bad data files to test quarantine handling."""
    bad_dir = Path(bad_dir)
    ing = Ingester(db_path)

    for f in sorted(bad_dir.glob("*.csv")):
        # determine table based on columns in the file
        with open(f, encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            headers = reader.fieldnames or []

        if "txn_id" in headers:
            ing.load_csv(f, "transactions", ["txn_id", "source_account", "destination_account", "amount"], "txn_id",
                         timestamp_fields=["timestamp"],
                         entity_refs=[("source_account", ing.known_accounts, "source_account")])
        elif "event_id" in headers and "employee_id" in headers and "customer_id" in headers:
            ing.load_csv(f, "access_events", ["event_id", "employee_id"], "event_id",
                         timestamp_fields=["timestamp"],
                         entity_refs=[("employee_id", ing.known_employees, "employee_id"),
                                      ("account_id", ing.known_accounts, "account_id") if "account_id" in headers else None])
        elif "event_id" in headers and "employee_id" in headers:
            # could be login or access
            if "result" in headers and "customer_id" not in headers:
                ing.load_csv(f, "login_events", ["event_id", "employee_id"], "event_id",
                             timestamp_fields=["timestamp"],
                             entity_refs=[("employee_id", ing.known_employees, "employee_id")])
            else:
                ing.load_csv(f, "access_events", ["event_id", "employee_id"], "event_id",
                             timestamp_fields=["timestamp"],
                             entity_refs=[("employee_id", ing.known_employees, "employee_id"),
                                          ("account_id", ing.known_accounts, "account_id") if "account_id" in headers else None])
        else:
            # unknown format, just try access_events
            ing.load_csv(f, "access_events", ["event_id", "employee_id"], "event_id",
                         timestamp_fields=["timestamp"])

    ing.close()
