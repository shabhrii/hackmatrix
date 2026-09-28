"""Cross-platform dev server launcher. Starts backend and frontend, waits for health."""
import subprocess
import sys
import os
import time
import json
import socket
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
PORTS_FILE = ROOT / ".ports.json"


def find_free_port(start=8000):
    for port in range(start, start + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("no free port found")


def wait_for_health(url, timeout=30):
    import urllib.request
    import urllib.error
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = urllib.request.urlopen(url, timeout=2)
            if resp.status == 200:
                return True
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(0.5)
    return False


def main():
    python = sys.executable
    npm = "npm.cmd" if os.name == "nt" else "npm"

    backend_port = find_free_port(8000)
    frontend_port = find_free_port(5173)

    ports = {"backend": backend_port, "frontend": frontend_port}
    PORTS_FILE.write_text(json.dumps(ports))

    print(f"Backend  : http://127.0.0.1:{backend_port}")
    print(f"Frontend : http://127.0.0.1:{frontend_port}")

    backend_proc = subprocess.Popen(
        [python, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(backend_port), "--reload"],
        cwd=str(BACKEND),
    )

    frontend_proc = subprocess.Popen(
        [npm, "run", "dev", "--", "--port", str(frontend_port)],
        cwd=str(FRONTEND),
    )

    if wait_for_health(f"http://127.0.0.1:{backend_port}/health"):
        print(f"\nBackend healthy at http://127.0.0.1:{backend_port}")
    else:
        print("\nBackend did not become healthy in time")

    print(f"Frontend dev server at http://127.0.0.1:{frontend_port}")
    print("\nPress Ctrl+C to stop both servers.\n")

    try:
        backend_proc.wait()
    except KeyboardInterrupt:
        backend_proc.terminate()
        frontend_proc.terminate()


if __name__ == "__main__":
    main()
