import socket
import threading
import time

import httpx
import uvicorn

from trader_api.main import app


def _available_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def test_real_loopback_http_server() -> None:
    port = _available_loopback_port()
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=port,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    try:
        deadline = time.monotonic() + 10
        while not server.started and time.monotonic() < deadline:
            time.sleep(0.05)

        assert server.started
        response = httpx.get(f"http://127.0.0.1:{port}/health", timeout=2)
        assert response.status_code == 200
        assert response.json()["trading_enabled"] is False
    finally:
        server.should_exit = True
        thread.join(timeout=5)
