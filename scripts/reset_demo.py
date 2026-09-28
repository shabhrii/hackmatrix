"""Rebuild the demo database from seed files through the ingestion pipeline."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

DB_PATH = BACKEND / "sentinelgraph.db"


def main():
    # remove existing db
    if DB_PATH.exists():
        DB_PATH.unlink()
        print("Removed existing database.")

    print("Database reset complete. (Ingestion pipeline will be added at CP2)")


if __name__ == "__main__":
    main()
