import sqlite3
import time
from pathlib import Path
from contextlib import contextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
