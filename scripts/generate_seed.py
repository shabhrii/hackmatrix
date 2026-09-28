"""Deterministic seed data generator for SentinelGraph.

Seed value 42. Same seed produces identical output across runs.
Generates CSV/JSON files under data/seed/ for all entities and scenarios S1-S8.
"""
import csv
import json
import random
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import defaultdict

SEED = 42
ROOT = Path(__file__).resolve().parent.parent
SEED_DIR = ROOT / "data" / "seed"
BAD_DIR = SEED_DIR / "bad"

# base date for all events: 2026-09-15 in UTC
BASE_DATE = datetime(2026, 9, 15, tzinfo=timezone.utc)
INGESTED_AT = datetime(2026, 9, 16, 0, 0, 0, tzinfo=timezone.utc).isoformat()
SOURCE_ID = "seed-v1"

BRANCHES = [
    {"branch_id": "BR-001", "name": "Pune Main", "city": "Pune"},
    {"branch_id": "BR-002", "name": "Mumbai Central", "city": "Mumbai"},
    {"branch_id": "BR-003", "name": "Nashik Road", "city": "Nashik"},
    {"branch_id": "BR-004", "name": "Aurangabad Camp", "city": "Aurangabad"},
]

ROLES = [
    {"role_id": "ROLE-TEL", "name": "teller", "permission_set": json.dumps({
        "actions": ["view_customer", "view_account", "process_transaction"],
        "branch_scope": "own", "record_scope": ["customer", "account"]
    })},
    {"role_id": "ROLE-RM", "name": "relationship_manager", "permission_set": json.dumps({
        "actions": ["view_customer", "view_account", "modify_beneficiary", "process_transaction"],
        "branch_scope": "own", "record_scope": ["customer", "account", "beneficiary"]
    })},
    {"role_id": "ROLE-CS", "name": "customer_service", "permission_set": json.dumps({
        "actions": ["view_customer", "view_account", "update_profile"],
        "branch_scope": "own", "record_scope": ["customer", "account"]
    })},
    {"role_id": "ROLE-OPS", "name": "ops_batch_operator", "permission_set": json.dumps({
        "actions": ["view_customer", "view_account", "batch_retrieve"],
        "branch_scope": "all", "record_scope": ["customer", "account"]
    })},
    {"role_id": "ROLE-SEC", "name": "security_admin", "permission_set": json.dumps({
        "actions": ["view_customer", "view_account", "modify_access", "audit_review"],
        "branch_scope": "all", "record_scope": ["customer", "account", "employee", "audit"]
    })},
    {"role_id": "ROLE-MGR", "name": "branch_manager", "permission_set": json.dumps({
        "actions": ["view_customer", "view_account", "approve_transaction", "manage_employee"],
        "branch_scope": "own", "record_scope": ["customer", "account", "employee"]
    })},
]

# indian first/last names for realistic data
FIRST_NAMES = [
    "Aarav", "Aditi", "Amit", "Ananya", "Arjun", "Bhavna", "Chandan", "Deepa",
    "Esha", "Farhan", "Gauri", "Harsh", "Isha", "Jayesh", "Kavita", "Lakshmi",
    "Mohan", "Neha", "Omkar", "Pallavi", "Rahul", "Sangeeta", "Tanvi", "Uday",
    "Varun", "Wani", "Yash", "Zara", "Priya", "Rajesh", "Sunita", "Vikram",
    "Anil", "Bhagyashree", "Chandrakant", "Durga", "Ganesh", "Hemant", "Indira",
    "Jyoti", "Kiran", "Lalita", "Manish", "Nandini", "Prasad", "Rekha",
    "Sachin", "Suresh", "Tushar", "Uma", "Vivek", "Ashok", "Bala", "Chitra",
    "Devendra", "Ekta", "Fatima", "Girish", "Hema", "Irfan", "Janaki",
]
LAST_NAMES = [
    "Sharma", "Patel", "Desai", "Kulkarni", "Joshi", "Mehta", "Shah", "Patil",
    "Rao", "Reddy", "Nair", "Menon", "Gupta", "Singh", "Verma", "Bhat",
    "Kale", "More", "Pawar", "Jadhav", "Deshpande", "Gokhale", "Apte", "Bhatt",
    "Chauhan", "Dixit", "Iyer", "Kadam", "Mane", "Naik", "Sawant", "Thakur",
]


def fmt_ts(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def hash_short(val):
    return hashlib.sha256(val.encode()).hexdigest()[:12]


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def generate():
    rng = random.Random(SEED)

    # --- employees ---
    employees = []
    emp_by_role = defaultdict(list)
    emp_idx = 0

    # fixed scenario employees first
    scenario_employees = {
        "E-0417": {"name": "Sanjay Kulkarni", "role_id": "ROLE-TEL", "branch_id": "BR-001"},  # S1 teller, Pune branch
        "E-0880": {"name": "Leela Patil", "role_id": "ROLE-OPS", "branch_id": "BR-001"},  # S4 ops batch operator
        "E-0512": {"name": "Manoj Deshmukh", "role_id": "ROLE-CS", "branch_id": "BR-003"},  # S5 customer service
        "E-0233": {"name": "Ritu Sharma", "role_id": "ROLE-TEL", "branch_id": "BR-002"},  # S6 failed logins
    }

    # security admins for S7 (exactly 3, small peer group)
    sec_admins = {
        "E-0901": {"name": "Vikrant Naik", "role_id": "ROLE-SEC", "branch_id": "BR-001"},
        "E-0902": {"name": "Asha Bhosle", "role_id": "ROLE-SEC", "branch_id": "BR-002"},
        "E-0903": {"name": "Deepak Sawant", "role_id": "ROLE-SEC", "branch_id": "BR-003"},
    }

    # S8 customer service employee with valid assignment
    s8_employee = {
        "E-0601": {"name": "Pooja Kale", "role_id": "ROLE-CS", "branch_id": "BR-001"},
    }

    all_fixed = {**scenario_employees, **sec_admins, **s8_employee}

    for eid, info in all_fixed.items():
        emp = {
            "employee_id": eid,
            "name": info["name"],
            "role_id": info["role_id"],
            "branch_id": info["branch_id"],
            "manager_id": None,
            "active_from": fmt_ts(BASE_DATE - timedelta(days=365)),
            "active_to": None,
            "event_time": fmt_ts(BASE_DATE - timedelta(days=365)),
            "ingested_at": INGESTED_AT,
            "source_id": SOURCE_ID,
        }
        employees.append(emp)
        emp_by_role[info["role_id"]].append(eid)

    # fill remaining to reach ~60
    role_distribution = {
        "ROLE-TEL": 20,
        "ROLE-RM": 12,
        "ROLE-CS": 10,
        "ROLE-OPS": 6,
        "ROLE-MGR": 4,
    }
    used_names = set()
    for info in all_fixed.values():
        used_names.add(info["name"])

    bg_emp_idx = 1000
    for role_id, count in role_distribution.items():
        existing = len(emp_by_role[role_id])
        for i in range(max(0, count - existing)):
            bg_emp_idx += 1
            while True:
                fn = rng.choice(FIRST_NAMES)
                ln = rng.choice(LAST_NAMES)
                name = f"{fn} {ln}"
                if name not in used_names:
                    used_names.add(name)
                    break
            eid = f"E-{bg_emp_idx:04d}"
            branch = rng.choice(BRANCHES)
            emp = {
                "employee_id": eid,
                "name": name,
                "role_id": role_id,
                "branch_id": branch["branch_id"],
                "manager_id": None,
                "active_from": fmt_ts(BASE_DATE - timedelta(days=rng.randint(90, 730))),
                "active_to": None,
                "event_time": fmt_ts(BASE_DATE - timedelta(days=rng.randint(90, 730))),
                "ingested_at": INGESTED_AT,
                "source_id": SOURCE_ID,
            }
            employees.append(emp)
            emp_by_role[role_id].append(eid)

    # assign managers
    managers_by_branch = {}
    for emp in employees:
        if emp["role_id"] == "ROLE-MGR":
            managers_by_branch[emp["branch_id"]] = emp["employee_id"]
    for emp in employees:
        if emp["role_id"] != "ROLE-MGR" and emp["branch_id"] in managers_by_branch:
            emp["manager_id"] = managers_by_branch[emp["branch_id"]]

    # --- customers ---
    customers = []
    segments = ["retail", "sme", "premium", "corporate"]
    risk_bands = ["low", "standard", "elevated", "high"]

    # fixed customers
    fixed_customers = {
        "C-2210": {"name": "Ramesh Iyer", "segment": "retail", "branch_id": "BR-002", "risk_band": "standard"},  # S1 - Mumbai branch
    }

    # S5 out-of-branch customer
    fixed_customers["C-3310"] = {"name": "Arun Thakur", "segment": "sme", "branch_id": "BR-002", "risk_band": "standard"}

    # S7 customer
    fixed_customers["C-7701"] = {"name": "Meera Deshpande", "segment": "premium", "branch_id": "BR-003", "risk_band": "low"}

    # S8 out-of-branch customer with assignment
    fixed_customers["C-8801"] = {"name": "Sunil Gokhale", "segment": "retail", "branch_id": "BR-002", "risk_band": "standard"}

    for cid, info in fixed_customers.items():
        cust = {
            "customer_id": cid,
            "name": info["name"],
            "segment": info["segment"],
            "branch_id": info["branch_id"],
            "risk_band": info["risk_band"],
            "event_time": fmt_ts(BASE_DATE - timedelta(days=rng.randint(180, 1000))),
            "ingested_at": INGESTED_AT,
            "source_id": SOURCE_ID,
        }
        customers.append(cust)

    cust_used_names = {info["name"] for info in fixed_customers.values()}
    for i in range(400 - len(fixed_customers)):
        cid = f"C-{i+1:04d}"
        if cid in fixed_customers:
            cid = f"C-{4000+i:04d}"
        while True:
            fn = rng.choice(FIRST_NAMES)
            ln = rng.choice(LAST_NAMES)
            name = f"{fn} {ln}"
            if name not in cust_used_names:
                cust_used_names.add(name)
                break
        cust = {
            "customer_id": cid,
            "name": name,
            "segment": rng.choice(segments),
            "branch_id": rng.choice(BRANCHES)["branch_id"],
            "risk_band": rng.choices(risk_bands, weights=[40, 35, 15, 10])[0],
            "event_time": fmt_ts(BASE_DATE - timedelta(days=rng.randint(180, 1000))),
            "ingested_at": INGESTED_AT,
            "source_id": SOURCE_ID,
        }
        customers.append(cust)

    # --- accounts ---
    accounts = []
    account_types = ["savings", "current", "salary", "fixed_deposit"]

    # fixed accounts
    fixed_accounts = {
        "ACC-5031": {"customer_id": "C-2210", "account_type": "savings"},  # S2 source 1
        "ACC-5032": {"customer_id": "C-2210", "account_type": "current"},  # S2 source 2 (same owner)
        "ACC-9907": {"customer_id": "C-3310", "account_type": "savings"},  # S2 destination
        "ACC-6101": {"customer_id": "C-2210", "account_type": "current"},  # S3 circular
        "ACC-6102": {"customer_id": "C-3310", "account_type": "savings"},  # S3 circular
        "ACC-6103": {"customer_id": "C-7701", "account_type": "current"},  # S3 circular
    }

    # S1 account for C-2210
    fixed_accounts["ACC-2210"] = {"customer_id": "C-2210", "account_type": "savings"}

    for aid, info in fixed_accounts.items():
        acc = {
            "account_id": aid,
            "customer_id": info["customer_id"],
            "account_type": info["account_type"],
            "opened_at": fmt_ts(BASE_DATE - timedelta(days=rng.randint(90, 500))),
            "status": "active",
            "event_time": fmt_ts(BASE_DATE - timedelta(days=rng.randint(90, 500))),
            "ingested_at": INGESTED_AT,
            "source_id": SOURCE_ID,
        }
        accounts.append(acc)

    # background accounts (~600 total)
    customer_ids = [c["customer_id"] for c in customers]
    acc_idx = 0
    for i in range(600 - len(fixed_accounts)):
        acc_idx += 1
        aid = f"ACC-{acc_idx:04d}"
        while aid in fixed_accounts:
            acc_idx += 1
            aid = f"ACC-{acc_idx:04d}"
        acc = {
            "account_id": aid,
            "customer_id": rng.choice(customer_ids),
            "account_type": rng.choice(account_types),
            "opened_at": fmt_ts(BASE_DATE - timedelta(days=rng.randint(30, 800))),
            "status": "active",
            "event_time": fmt_ts(BASE_DATE - timedelta(days=rng.randint(30, 800))),
            "ingested_at": INGESTED_AT,
            "source_id": SOURCE_ID,
        }
        accounts.append(acc)

    all_account_ids = [a["account_id"] for a in accounts]

    # --- beneficiaries ---
    beneficiaries = []
    ben_idx = 0
    for i in range(200):
        ben_idx += 1
        bid = f"BEN-{ben_idx:04d}"
        src_acc = rng.choice(all_account_ids)
        dst_acc = rng.choice(all_account_ids)
        while dst_acc == src_acc:
            dst_acc = rng.choice(all_account_ids)
        creator = rng.choice(employees)["employee_id"]
        ben = {
            "beneficiary_id": bid,
            "account_id": src_acc,
            "destination_account": dst_acc,
            "created_at": fmt_ts(BASE_DATE - timedelta(days=rng.randint(1, 300))),
            "created_by": creator,
            "event_time": fmt_ts(BASE_DATE - timedelta(days=rng.randint(1, 300))),
            "ingested_at": INGESTED_AT,
            "source_id": SOURCE_ID,
        }
        beneficiaries.append(ben)

    # S3: ACC-6103 shares a beneficiary with ACC-6101
    beneficiaries.append({
        "beneficiary_id": "BEN-S3-01",
        "account_id": "ACC-6103",
        "destination_account": "ACC-6101",
        "created_at": fmt_ts(BASE_DATE - timedelta(days=60)),
        "created_by": employees[0]["employee_id"],
        "event_time": fmt_ts(BASE_DATE - timedelta(days=60)),
        "ingested_at": INGESTED_AT,
        "source_id": SOURCE_ID,
    })

    # --- background access events (~12,000) ---
    access_events = []
    access_idx = 0
    actions = ["view_customer", "view_account", "view_transaction", "update_profile", "process_transaction"]

    # background: business-hours skew, weekday skew
    for i in range(12000):
        access_idx += 1
        eid_prefix = f"A-BG-{access_idx:05d}"
        emp = rng.choice(employees)
        # business hours skew: 70% 9-17, 20% 17-21, 10% other
        r = rng.random()
        if r < 0.70:
            hour = rng.randint(9, 16)
        elif r < 0.90:
            hour = rng.randint(17, 20)
        else:
            hour = rng.randint(0, 8)

        # weekday skew: 85% weekday
        day_offset = rng.randint(0, 29)
        dt = BASE_DATE + timedelta(days=-day_offset, hours=hour, minutes=rng.randint(0, 59))
        if dt.weekday() >= 5 and rng.random() < 0.85:
            dt -= timedelta(days=dt.weekday() - 4)  # shift to friday

        cust = rng.choice(customers)
        cust_accounts = [a for a in accounts if a["customer_id"] == cust["customer_id"]]
        acc_id = cust_accounts[0]["account_id"] if cust_accounts else None

        # role-appropriate actions
        role_actions = {
            "ROLE-TEL": ["view_customer", "view_account", "process_transaction"],
            "ROLE-RM": ["view_customer", "view_account", "update_profile"],
            "ROLE-CS": ["view_customer", "view_account"],
            "ROLE-OPS": ["view_customer", "batch_retrieve"],
            "ROLE-SEC": ["view_customer", "audit_review"],
            "ROLE-MGR": ["view_customer", "view_account", "approve_transaction"],
        }
        emp_actions = role_actions.get(emp["role_id"], actions)

        ae = {
            "event_id": eid_prefix,
            "employee_id": emp["employee_id"],
            "customer_id": cust["customer_id"],
            "account_id": acc_id,
            "action": rng.choice(emp_actions),
            "timestamp": fmt_ts(dt),
            "result": "success",
            "device_id": f"DEV-{rng.randint(1, 20):03d}",
            "ip_hash": hash_short(f"ip-{rng.randint(1, 50)}"),
            "scenario_label": None,
            "event_time": fmt_ts(dt),
            "ingested_at": INGESTED_AT,
            "source_id": SOURCE_ID,
        }
        access_events.append(ae)

    # --- S1: insider beneficiary manipulation ---
    # E-0417 (Pune/BR-001) accesses C-2210 (Mumbai/BR-002) - no case assignment
    s1_time = BASE_DATE + timedelta(hours=14, minutes=2)
    access_events.append({
        "event_id": "A-19",
        "employee_id": "E-0417",
        "customer_id": "C-2210",
        "account_id": "ACC-2210",
        "action": "view_customer",
        "timestamp": fmt_ts(s1_time),
        "result": "success",
        "device_id": "DEV-011",
        "ip_hash": hash_short("ip-s1-0417"),
        "scenario_label": "S1",
        "event_time": fmt_ts(s1_time),
        "ingested_at": INGESTED_AT,
        "source_id": SOURCE_ID,
    })

    # boost E-0417's daily access volume to P99 of teller peers
    for i in range(45):
        t = s1_time - timedelta(hours=rng.randint(0, 7), minutes=rng.randint(0, 59))
        cust = rng.choice(customers)
        access_events.append({
            "event_id": f"A-S1-BURST-{i:03d}",
            "employee_id": "E-0417",
            "customer_id": cust["customer_id"],
            "account_id": None,
            "action": "view_customer",
            "timestamp": fmt_ts(t),
            "result": "success",
            "device_id": "DEV-011",
            "ip_hash": hash_short("ip-s1-0417"),
            "scenario_label": "S1",
            "event_time": fmt_ts(t),
            "ingested_at": INGESTED_AT,
            "source_id": SOURCE_ID,
        })

    # S1 profile/beneficiary change
    profile_changes = []
    s1_change_time = s1_time + timedelta(minutes=7)  # 14:09
    profile_changes.append({
        "change_id": "P-07",
        "employee_id": "E-0417",
        "customer_id": "C-2210",
        "field": "beneficiary",
        "old_value_hash": hash_short("old-ben-c2210"),
        "new_value_hash": hash_short("new-ben-acc9907"),
        "timestamp": fmt_ts(s1_change_time),
        "scenario_label": "S1",
        "event_time": fmt_ts(s1_change_time),
        "ingested_at": INGESTED_AT,
        "source_id": SOURCE_ID,
    })

    # background profile changes
    for i in range(100):
        dt = BASE_DATE + timedelta(days=-rng.randint(0, 29), hours=rng.randint(9, 16), minutes=rng.randint(0, 59))
        emp = rng.choice(employees)
        cust = rng.choice(customers)
        profile_changes.append({
            "change_id": f"P-BG-{i:04d}",
            "employee_id": emp["employee_id"],
            "customer_id": cust["customer_id"],
            "field": rng.choice(["address", "phone", "email", "nominee"]),
            "old_value_hash": hash_short(f"old-{i}"),
            "new_value_hash": hash_short(f"new-{i}"),
            "timestamp": fmt_ts(dt),
            "scenario_label": None,
            "event_time": fmt_ts(dt),
            "ingested_at": INGESTED_AT,
            "source_id": SOURCE_ID,
        })

    # --- transactions ---
    transactions = []

    # S1 transfer at 14:20 to new destination
    s1_txn_time = s1_time + timedelta(minutes=18)  # 14:20
    transactions.append({
        "txn_id": "T-88",
        "source_account": "ACC-2210",
        "destination_account": "ACC-9907",
        "amount": 850000.00,  # 8.5 lakh
        "currency": "INR",
        "timestamp": fmt_ts(s1_txn_time),
        "channel": "branch",
        "status": "completed",
        "scenario_label": "S1",
        "is_recurring": 0,
        "event_time": fmt_ts(s1_txn_time),
        "ingested_at": INGESTED_AT,
        "source_id": SOURCE_ID,
    })

    # S2: four near-threshold transfers
    s2_base = BASE_DATE + timedelta(days=1, hours=10)
    s2_txns = [
        ("T-S2-01", "ACC-5031", "ACC-9907", 740000.00, 0),
        ("T-S2-02", "ACC-5031", "ACC-9907", 810000.00, 4),
        ("T-S2-03", "ACC-5032", "ACC-9907", 920000.00, 10),
        ("T-S2-04", "ACC-5032", "ACC-9907", 960000.00, 16),
    ]
    for tid, src, dst, amt, hour_offset in s2_txns:
        transactions.append({
            "txn_id": tid,
            "source_account": src,
            "destination_account": dst,
            "amount": amt,
            "currency": "INR",
            "timestamp": fmt_ts(s2_base + timedelta(hours=hour_offset)),
            "channel": "online",
            "status": "completed",
            "scenario_label": "S2",
            "is_recurring": 0,
            "event_time": fmt_ts(s2_base + timedelta(hours=hour_offset)),
            "ingested_at": INGESTED_AT,
            "source_id": SOURCE_ID,
        })

    # S2b: decoy salary disbursement - 40 accounts, near threshold, tagged recurring
    s2b_base = BASE_DATE + timedelta(days=2, hours=9)
    for i in range(40):
        dst_acc = rng.choice(all_account_ids)
        amt = rng.randint(850000, 980000)
        transactions.append({
            "txn_id": f"T-S2B-{i:03d}",
            "source_account": "ACC-5031",
            "destination_account": dst_acc,
            "amount": float(amt),
            "currency": "INR",
            "timestamp": fmt_ts(s2b_base + timedelta(minutes=i * 2)),
            "channel": "batch",
            "status": "completed",
            "scenario_label": "S2b",
            "is_recurring": 1,
            "event_time": fmt_ts(s2b_base + timedelta(minutes=i * 2)),
            "ingested_at": INGESTED_AT,
            "source_id": SOURCE_ID,
        })

    # S3: circular flow ACC-6101 -> ACC-6102 -> ACC-6103 -> ACC-6101 within 48 hours
    s3_base = BASE_DATE + timedelta(days=3, hours=10)
    s3_txns = [
        ("T-S3-01", "ACC-6101", "ACC-6102", 1200000.00, 0),
        ("T-S3-02", "ACC-6102", "ACC-6103", 1160000.00, 12),
        ("T-S3-03", "ACC-6103", "ACC-6101", 1120000.00, 36),
    ]
    for tid, src, dst, amt, hour_offset in s3_txns:
        transactions.append({
            "txn_id": tid,
            "source_account": src,
            "destination_account": dst,
            "amount": amt,
            "currency": "INR",
            "timestamp": fmt_ts(s3_base + timedelta(hours=hour_offset)),
            "channel": "online",
            "status": "completed",
            "scenario_label": "S3",
            "is_recurring": 0,
            "event_time": fmt_ts(s3_base + timedelta(hours=hour_offset)),
            "ingested_at": INGESTED_AT,
            "source_id": SOURCE_ID,
        })

    # S5: transfer 3 hours after out-of-scope access (outside 60-min R-04 window)
    s5_time = BASE_DATE + timedelta(days=4, hours=11)
    access_events.append({
        "event_id": "A-S5-01",
        "employee_id": "E-0512",
        "customer_id": "C-3310",
        "account_id": "ACC-9907",
        "action": "view_customer",
        "timestamp": fmt_ts(s5_time),
        "result": "success",
        "device_id": "DEV-005",
        "ip_hash": hash_short("ip-s5-0512"),
        "scenario_label": "S5",
        "event_time": fmt_ts(s5_time),
        "ingested_at": INGESTED_AT,
        "source_id": SOURCE_ID,
    })
    transactions.append({
        "txn_id": "T-S5-01",
        "source_account": "ACC-9907",
        "destination_account": rng.choice(all_account_ids),
        "amount": 500000.00,
        "currency": "INR",
        "timestamp": fmt_ts(s5_time + timedelta(hours=3)),
        "channel": "online",
        "status": "completed",
        "scenario_label": "S5",
        "is_recurring": 0,
        "event_time": fmt_ts(s5_time + timedelta(hours=3)),
        "ingested_at": INGESTED_AT,
        "source_id": SOURCE_ID,
    })

    # --- S4: legitimate month-end batch ---
    s4_time = BASE_DATE + timedelta(days=5, hours=10)
    # 84 distinct customer record retrievals in 9 minutes
    s4_customers = rng.sample([c["customer_id"] for c in customers], min(84, len(customers)))
    for i, cid in enumerate(s4_customers):
        offset_seconds = int((9 * 60) * (i / len(s4_customers)))
        access_events.append({
            "event_id": f"A-S4-{i:03d}",
            "employee_id": "E-0880",
            "customer_id": cid,
            "account_id": None,
            "action": "batch_retrieve",
            "timestamp": fmt_ts(s4_time + timedelta(seconds=offset_seconds)),
            "result": "success",
            "device_id": "DEV-BATCH-01",
            "ip_hash": hash_short("ip-batch-0880"),
            "scenario_label": "S4",
            "event_time": fmt_ts(s4_time + timedelta(seconds=offset_seconds)),
            "ingested_at": INGESTED_AT,
            "source_id": SOURCE_ID,
        })

    # six ops peers with similar volume
    ops_peers = [e["employee_id"] for e in employees if e["role_id"] == "ROLE-OPS" and e["employee_id"] != "E-0880"]
    for peer_eid in ops_peers[:6]:
        peer_count = rng.randint(60, 90)
        for j in range(peer_count):
            dt = BASE_DATE + timedelta(days=-rng.choice([0, 30, 60, 90]), hours=rng.randint(9, 16), minutes=rng.randint(0, 59))
            cid = rng.choice([c["customer_id"] for c in customers])
            access_events.append({
                "event_id": f"A-S4-PEER-{peer_eid}-{j:03d}",
                "employee_id": peer_eid,
                "customer_id": cid,
                "account_id": None,
                "action": "batch_retrieve",
                "timestamp": fmt_ts(dt),
                "result": "success",
                "device_id": f"DEV-BATCH-{rng.randint(1, 5):02d}",
                "ip_hash": hash_short(f"ip-batch-{peer_eid}"),
                "scenario_label": None,
                "event_time": fmt_ts(dt),
                "ingested_at": INGESTED_AT,
                "source_id": SOURCE_ID,
            })

    # --- S6: failed logins ---
    s6_time = BASE_DATE + timedelta(days=6, hours=9, minutes=30)
    login_events = []
    # 7 failed logins across 2 devices in 11 minutes
    for i in range(7):
        login_events.append({
            "event_id": f"L-S6-{i:02d}",
            "employee_id": "E-0233",
            "timestamp": fmt_ts(s6_time + timedelta(minutes=int(11 * i / 7))),
            "result": "failed",
            "device_id": f"DEV-{(i % 2) + 1:03d}",
            "ip_hash": hash_short(f"ip-s6-dev{(i % 2) + 1}"),
            "scenario_label": "S6",
            "event_time": fmt_ts(s6_time + timedelta(minutes=int(11 * i / 7))),
            "ingested_at": INGESTED_AT,
            "source_id": SOURCE_ID,
        })
    # success from new device
    login_events.append({
        "event_id": "L-S6-07",
        "employee_id": "E-0233",
        "timestamp": fmt_ts(s6_time + timedelta(minutes=14)),
        "result": "success",
        "device_id": "DEV-003",
        "ip_hash": hash_short("ip-s6-dev3"),
        "scenario_label": "S6",
        "event_time": fmt_ts(s6_time + timedelta(minutes=14)),
        "ingested_at": INGESTED_AT,
        "source_id": SOURCE_ID,
    })

    # background logins
    for i in range(500):
        emp = rng.choice(employees)
        dt = BASE_DATE + timedelta(days=-rng.randint(0, 29), hours=rng.randint(7, 19), minutes=rng.randint(0, 59))
        login_events.append({
            "event_id": f"L-BG-{i:04d}",
            "employee_id": emp["employee_id"],
            "timestamp": fmt_ts(dt),
            "result": "success",
            "device_id": f"DEV-{rng.randint(1, 20):03d}",
            "ip_hash": hash_short(f"ip-bg-{rng.randint(1, 50)}"),
            "scenario_label": None,
            "event_time": fmt_ts(dt),
            "ingested_at": INGESTED_AT,
            "source_id": SOURCE_ID,
        })

    # --- S7: security admin after-hours with approved ticket ---
    s7_time = BASE_DATE + timedelta(days=7, hours=23, minutes=15)
    access_events.append({
        "event_id": "A-S7-01",
        "employee_id": "E-0901",
        "customer_id": "C-7701",
        "account_id": None,
        "action": "modify_access",
        "timestamp": fmt_ts(s7_time),
        "result": "success",
        "device_id": "DEV-SEC-01",
        "ip_hash": hash_short("ip-sec-0901"),
        "scenario_label": "S7",
        "event_time": fmt_ts(s7_time),
        "ingested_at": INGESTED_AT,
        "source_id": SOURCE_ID,
    })

    # --- S8: assigned access (customer_service accesses out-of-branch customer with valid assignment) ---
    s8_time = BASE_DATE + timedelta(days=8, hours=11, minutes=30)
    access_events.append({
        "event_id": "A-S8-01",
        "employee_id": "E-0601",
        "customer_id": "C-8801",
        "account_id": None,
        "action": "view_customer",
        "timestamp": fmt_ts(s8_time),
        "result": "success",
        "device_id": "DEV-009",
        "ip_hash": hash_short("ip-s8-0601"),
        "scenario_label": "S8",
        "event_time": fmt_ts(s8_time),
        "ingested_at": INGESTED_AT,
        "source_id": SOURCE_ID,
    })

    # --- background transactions (~6,000) ---
    for i in range(6000):
        src = rng.choice(all_account_ids)
        dst = rng.choice(all_account_ids)
        while dst == src:
            dst = rng.choice(all_account_ids)
        # realistic amounts: most small, some medium
        r = rng.random()
        if r < 0.5:
            amt = rng.randint(500, 50000)
        elif r < 0.8:
            amt = rng.randint(50000, 300000)
        elif r < 0.95:
            amt = rng.randint(300000, 800000)
        else:
            amt = rng.randint(800000, 3000000)

        dt = BASE_DATE + timedelta(days=-rng.randint(0, 29), hours=rng.randint(9, 17), minutes=rng.randint(0, 59))
        if dt.weekday() >= 5 and rng.random() < 0.80:
            dt -= timedelta(days=dt.weekday() - 4)

        transactions.append({
            "txn_id": f"T-BG-{i:05d}",
            "source_account": src,
            "destination_account": dst,
            "amount": float(amt),
            "currency": "INR",
            "timestamp": fmt_ts(dt),
            "channel": rng.choice(["branch", "online", "atm", "upi"]),
            "status": "completed",
            "scenario_label": None,
            "is_recurring": 1 if rng.random() < 0.1 else 0,
            "event_time": fmt_ts(dt),
            "ingested_at": INGESTED_AT,
            "source_id": SOURCE_ID,
        })

    # --- supporting tables ---

    # case_assignments: S8 has valid assignment
    case_assignments = [{
        "employee_id": "E-0601",
        "customer_id": "C-8801",
        "valid_from": fmt_ts(BASE_DATE),
        "valid_to": fmt_ts(BASE_DATE + timedelta(days=30)),
        "source_id": SOURCE_ID,
    }]

    # batch_jobs: S4 approved job
    batch_jobs = [{
        "job_id": "JOB-ME-0930",
        "operator_id": "E-0880",
        "approved": 1,
        "window_start": fmt_ts(BASE_DATE + timedelta(days=5, hours=9)),
        "window_end": fmt_ts(BASE_DATE + timedelta(days=5, hours=18)),
        "source_id": SOURCE_ID,
    }]

    # oncall_approvals: S7 approved ticket
    oncall_approvals = [{
        "ticket_id": "TKT-4471",
        "employee_id": "E-0901",
        "window_start": fmt_ts(BASE_DATE + timedelta(days=7, hours=22)),
        "window_end": fmt_ts(BASE_DATE + timedelta(days=8, hours=6)),
        "source_id": SOURCE_ID,
    }]

    # config
    config = [
        {"key": "attention_threshold", "value": "1000000"},
        {"key": "splitting_min_transfers", "value": "3"},
        {"key": "splitting_time_window_hours", "value": "24"},
        {"key": "splitting_pct_low", "value": "0.70"},
        {"key": "splitting_pct_high", "value": "0.99"},
        {"key": "circular_max_length", "value": "5"},
        {"key": "circular_time_window_hours", "value": "72"},
        {"key": "peer_min_group_size", "value": "5"},
        {"key": "failed_login_threshold", "value": "5"},
        {"key": "failed_login_window_minutes", "value": "15"},
        {"key": "excessive_retrieval_threshold", "value": "50"},
        {"key": "excessive_retrieval_window_minutes", "value": "10"},
        {"key": "action_to_transaction_window_minutes", "value": "60"},
    ]

    # --- write files ---
    write_csv(SEED_DIR / "branches.csv", BRANCHES, ["branch_id", "name", "city"])
    write_csv(SEED_DIR / "roles.csv", ROLES, ["role_id", "name", "permission_set"])
    write_csv(SEED_DIR / "employees.csv", employees, [
        "employee_id", "name", "role_id", "branch_id", "manager_id",
        "active_from", "active_to", "event_time", "ingested_at", "source_id"
    ])
    write_csv(SEED_DIR / "customers.csv", customers, [
        "customer_id", "name", "segment", "branch_id", "risk_band",
        "event_time", "ingested_at", "source_id"
    ])
    write_csv(SEED_DIR / "accounts.csv", accounts, [
        "account_id", "customer_id", "account_type", "opened_at", "status",
        "event_time", "ingested_at", "source_id"
    ])
    write_csv(SEED_DIR / "beneficiaries.csv", beneficiaries, [
        "beneficiary_id", "account_id", "destination_account", "created_at", "created_by",
        "event_time", "ingested_at", "source_id"
    ])
    write_csv(SEED_DIR / "transactions.csv", transactions, [
        "txn_id", "source_account", "destination_account", "amount", "currency",
        "timestamp", "channel", "status", "scenario_label", "is_recurring",
        "event_time", "ingested_at", "source_id"
    ])
    write_csv(SEED_DIR / "access_events.csv", access_events, [
        "event_id", "employee_id", "customer_id", "account_id", "action",
        "timestamp", "result", "device_id", "ip_hash", "scenario_label",
        "event_time", "ingested_at", "source_id"
    ])
    write_csv(SEED_DIR / "profile_changes.csv", profile_changes, [
        "change_id", "employee_id", "customer_id", "field",
        "old_value_hash", "new_value_hash", "timestamp", "scenario_label",
        "event_time", "ingested_at", "source_id"
    ])
    write_csv(SEED_DIR / "login_events.csv", login_events, [
        "event_id", "employee_id", "timestamp", "result", "device_id", "ip_hash",
        "scenario_label", "event_time", "ingested_at", "source_id"
    ])
    write_json(SEED_DIR / "case_assignments.json", case_assignments)
    write_json(SEED_DIR / "batch_jobs.json", batch_jobs)
    write_json(SEED_DIR / "oncall_approvals.json", oncall_approvals)
    write_json(SEED_DIR / "config.json", config)

    # --- bad data for quarantine testing ---
    bad_records = [
        {"file": "missing_id.csv", "content": "event_id,employee_id,timestamp\n,E-0417,2026-09-15T10:00:00Z\n", "reason": "missing required field: event_id"},
        {"file": "invalid_timestamp.csv", "content": "event_id,employee_id,timestamp\nBAD-TS-01,E-0417,not-a-date\n", "reason": "invalid timestamp format"},
        {"file": "negative_amount.csv", "content": "txn_id,source_account,destination_account,amount,currency,timestamp\nBAD-AMT-01,ACC-0001,ACC-0002,-5000,INR,2026-09-15T10:00:00Z\n", "reason": "negative amount"},
        {"file": "unknown_entity.csv", "content": "event_id,employee_id,customer_id,timestamp\nBAD-ENT-01,E-9999,C-9999,2026-09-15T10:00:00Z\n", "reason": "unknown entity reference"},
        {"file": "duplicate_event.csv", "content": "event_id,employee_id,timestamp\nA-19,E-0417,2026-09-15T14:02:00Z\n", "reason": "duplicate event_id"},
        {"file": "ambiguous_account.csv", "content": "event_id,employee_id,account_id,timestamp\nBAD-AMB-01,E-0417,ACC-AMBIGUOUS,2026-09-15T10:00:00Z\n", "reason": "unknown entity reference: account_id=ACC-AMBIGUOUS"},
    ]
    for rec in bad_records:
        (BAD_DIR / rec["file"]).parent.mkdir(parents=True, exist_ok=True)
        with open(BAD_DIR / rec["file"], "w", encoding="utf-8") as f:
            f.write(rec["content"])

    write_json(BAD_DIR / "expected_quarantine.json", [
        {"file": r["file"], "reason": r["reason"]} for r in bad_records
    ])

    # --- golden file for test assertions ---
    golden = {
        "S1": {
            "rules_triggered": ["R-03", "R-04"],
            "severity": "high",
            "score": 87,
            "confidence": 0.87,
            "evidence_count": 3,
            "evidence_ids": ["A-19", "P-07", "T-88"],
            "alert_generated": True,
        },
        "S2": {
            "rules_triggered": ["R-05"],
            "severity": "medium",
            "alert_generated": True,
        },
        "S2b": {
            "rules_triggered": [],
            "r05_triggered": False,
            "alert_generated": False,
        },
        "S3": {
            "rules_triggered": ["R-06"],
            "severity": "medium",
            "alert_generated": True,
        },
        "S4": {
            "rules_triggered": ["R-02"],
            "r02_status": "informational",
            "alert_generated": False,
            "monitored": True,
            "monitored_reasons": ["batch_operator_role", "approved_job", "expected_shift", "peer_baseline"],
        },
        "S5": {
            "rules_triggered": ["R-03"],
            "r03_severity": "medium",
            "r04_status": "insufficient_evidence",
            "severity": "medium",
            "recommended_action": "manual_review",
            "never_high": True,
            "alert_generated": True,
        },
        "S6": {
            "rules_triggered": ["R-01"],
            "alert_generated": True,
        },
        "S7": {
            "r07_status": "insufficient_evidence",
            "r08_status": "suppressed",
            "alert_generated": False,
        },
        "S8": {
            "r03_triggered": False,
            "alert_generated": False,
        },
    }
    tests_dir = ROOT / "backend" / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    write_json(tests_dir / "expected_alerts.json", golden)

    # print summary
    print(f"Seed data generated with seed={SEED}")
    print(f"  Branches: {len(BRANCHES)}")
    print(f"  Roles: {len(ROLES)}")
    print(f"  Employees: {len(employees)}")
    print(f"  Customers: {len(customers)}")
    print(f"  Accounts: {len(accounts)}")
    print(f"  Beneficiaries: {len(beneficiaries)}")
    print(f"  Transactions: {len(transactions)}")
    print(f"  Access events: {len(access_events)}")
    print(f"  Profile changes: {len(profile_changes)}")
    print(f"  Login events: {len(login_events)}")
    print(f"  Bad records: {len(bad_records)}")


if __name__ == "__main__":
    generate()
