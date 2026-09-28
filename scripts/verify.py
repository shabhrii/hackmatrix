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


GATES = {0: gate_cp0}


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
