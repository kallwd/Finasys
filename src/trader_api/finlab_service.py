from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from threading import Lock


_login_lock = Lock()
_login_process: subprocess.Popen | None = None


def finlab_status() -> dict[str, str | bool]:
    try:
        import finlab
        from finlab import auth

        session = auth.get_session()
        return {
            "installed": True,
            "version": finlab.__version__,
            "credentials_saved": bool(session),
            "status": "已保存登入憑證" if session else "尚未登入",
        }
    except (ImportError, OSError, ValueError):
        return {
            "installed": False,
            "version": "",
            "credentials_saved": False,
            "status": "FinLab 尚未安裝或憑證無法讀取",
        }


def start_finlab_login(project_root: Path) -> dict[str, str | bool]:
    global _login_process
    with _login_lock:
        if _login_process is not None and _login_process.poll() is None:
            return {"started": False, "message": "FinLab 登入視窗已經在等待操作。"}

        runtime = project_root / ".runtime"
        runtime.mkdir(parents=True, exist_ok=True)
        log_path = runtime / "finlab-login.log"
        helper = project_root / "src" / "trader_api" / "finlab_login.py"
        log_file = log_path.open("a", encoding="utf-8")
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        _login_process = subprocess.Popen(
            [sys.executable, str(helper)],
            cwd=project_root,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            creationflags=flags,
        )
        log_file.close()
        return {
            "started": True,
            "message": "已開啟 FinLab 官方瀏覽器登入流程；完成後回到本頁按重新整理。",
        }
