import os
import sys
import time
import socket
import subprocess
from pathlib import Path

def get_lan_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def main():
    root_dir = Path(__file__).parent.parent.resolve()
    os.chdir(root_dir)

    lan_ip = get_lan_ip()
    print("=" * 65)
    print("  Smart Border CCTV - Development Server")
    print("=" * 65)
    print(f"  Dashboard (Web):  http://localhost:5173")
    print(f"  Backend HTTP:     http://localhost:8000")
    print(f"  Backend HTTPS:    https://{lan_ip}:8443")
    print(f"  Phone Camera URL: https://{lan_ip}:8443/phone?cam=cam_phone")
    print("=" * 65)
    print("\nStarting Backend Server...")

    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "backend.main"],
        cwd=root_dir
    )

    frontend_dir = root_dir / "frontend"
    frontend_proc = None
    if frontend_dir.exists() and (frontend_dir / "package.json").exists():
        print("Starting Frontend Vite Dev Server...")
        npm_cmd = "npm.cmd" if sys.platform.startswith("win") else "npm"
        frontend_proc = subprocess.Popen(
            [npm_cmd, "run", "dev"],
            cwd=frontend_dir
        )
    else:
        print("Frontend directory not set up yet. Run step 6 first.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping processes...")
        if backend_proc:
            backend_proc.terminate()
        if frontend_proc:
            frontend_proc.terminate()
        print("Stopped.")

if __name__ == "__main__":
    main()
