"""Rebuild the demo database from seed files through the ingestion pipeline."""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

DB_PATH = BACKEND / "sentinelgraph.db"
SEED_DIR = ROOT / "data" / "seed"


def main():
    start = time.time()

    # remove existing db
    if DB_PATH.exists():
        DB_PATH.unlink()
        print("Removed existing database.")

    # create schema
    from schema import create_schema
    create_schema(DB_PATH)
    print("Schema created.")

    # generate seed data
    sys.path.insert(0, str(ROOT / "scripts"))
    from generate_seed import generate
    generate()
    print("Seed data generated.")

    # ingest through pipeline
    from ingestion import ingest_seed
    ingest_seed(DB_PATH, SEED_DIR)
    print("Seed data ingested.")

    elapsed = time.time() - start
    print(f"\nDatabase reset complete in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
