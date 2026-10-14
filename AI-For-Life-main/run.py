# -*- coding: utf-8 -*-
"""
AI-For-Life Launcher
- Chạy uvicorn server
- Tự mở browser tới http://localhost:8000/
- Bấm Ctrl+C để tắt server sạch sẽ

Khi đóng gói thành .exe với PyInstaller (--onefile), code sẽ được
giải nén vào thư mục tạm `_MEIPASS`. Launcher này tự động:
  1. Copy data/, src/, ui.html, .env, nguoidung.txt ra thư mục persistent
     cạnh file .exe (chỉ copy lần đầu / khi thiếu)
  2. cd vào thư mục đó
  3. Chạy uvicorn
"""
import os
import sys
import time
import shutil
import socket
import threading
import webbrowser
import tempfile
from pathlib import Path

# Force UTF-8 cho stdout/stderr trên Windows
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["PYTHONUTF8"] = "1"
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


# Khi chạy từ .exe (PyInstaller --onefile), sys._MEIPASS là thư mục tạm
# chứa toàn bộ source. Khi chạy từ .py thì BASE_DIR là thư mục gốc project.
if getattr(sys, "frozen", False):
    MEIPASS = sys._MEIPASS
    EXE_DIR = os.path.dirname(sys.executable)
else:
    MEIPASS = os.path.dirname(os.path.abspath(__file__))
    EXE_DIR = MEIPASS

# Thư mục làm việc: nơi chứa data/ + src/ + ui.html...
# - Source mode: chính project root
# - Frozen mode: cạnh .exe (copy từ _MEIPASS nếu chưa có)
WORK_DIR = EXE_DIR if getattr(sys, "frozen", False) else MEIPASS


def _setup_frozen_workdir():
    """Copy data/ + src/ + ui.html + .env từ _MEIPASS ra thư mục cạnh .exe
    nếu chưa tồn tại (để uvicorn + pandas.load_dataset tìm thấy file)."""
    if not getattr(sys, "frozen", False):
        return
    needed = ["data", "src", "ui.html", ".env", "nguoidung.txt"]
    for name in needed:
        src = os.path.join(MEIPASS, name)
        dst = os.path.join(WORK_DIR, name)
        if not os.path.exists(dst) and os.path.exists(src):
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
            print(f"[OK] Copied {name} -> {WORK_DIR}")


_setup_frozen_workdir()
os.chdir(WORK_DIR)
# Đảm bảo cwd nằm trong sys.path để import 'src' và 'main' hoạt động
if WORK_DIR not in sys.path:
    sys.path.insert(0, WORK_DIR)
print(f"[OK] Working dir: {os.getcwd()}")

HOST = "127.0.0.1"
PORT = int(os.environ.get("PORT", "8000"))


def wait_for_server(host: str, port: int, timeout: float = 60.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False


def open_browser_when_ready(host: str, port: int):
    if wait_for_server(host, port, timeout=90):
        url = f"http://{host}:{port}/"
        try:
            webbrowser.open(url)
            print(f"[OK] Browser opened: {url}")
        except Exception as e:
            print(f"[WARN] Cannot open browser: {e}")
    else:
        print("[ERROR] Server did not start within 90s.")


def main():
    import uvicorn

    print("=" * 50)
    print(" AI-For-Life Travel Assistant")
    print("=" * 50)
    print(f" Working dir : {os.getcwd()}")
    print(f" Server URL  : http://{HOST}:{PORT}/")
    print(" Press Ctrl+C to stop.")
    print("=" * 50)

    threading.Thread(
        target=open_browser_when_ready, args=(HOST, PORT), daemon=True
    ).start()

    try:
        uvicorn.run(
            "main:app",
            host=HOST,
            port=PORT,
            log_level="info",
            access_log=False,
        )
    except KeyboardInterrupt:
        print("\n[OK] Server stopped by user.")


if __name__ == "__main__":
    main()
