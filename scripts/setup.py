"""Cross-platform setup: installs backend and frontend dependencies."""
import subprocess
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"


def run(cmd, cwd=None, label=""):
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"  {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    print(f"{'=' * 60}")
    result = subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str))
    if result.returncode != 0:
        print(f"  FAILED (exit {result.returncode})")
        sys.exit(result.returncode)
    return result


def main():
    python = sys.executable

    # backend deps
    run(
        [python, "-m", "pip", "install", "-r", str(BACKEND / "requirements.txt")],
        cwd=str(BACKEND),
        label="Installing backend dependencies",
    )

    # frontend deps
    npm = "npm.cmd" if os.name == "nt" else "npm"
    run(
        [npm, "install"],
        cwd=str(FRONTEND),
        label="Installing frontend dependencies",
    )

    print("\nSetup complete.")


if __name__ == "__main__":
    main()
