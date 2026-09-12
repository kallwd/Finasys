from __future__ import annotations

from datetime import datetime

import finlab


if __name__ == "__main__":
    print(f"[{datetime.now().isoformat(timespec='seconds')}] Starting FinLab browser login", flush=True)
    finlab.login()
    print(f"[{datetime.now().isoformat(timespec='seconds')}] FinLab login completed", flush=True)
