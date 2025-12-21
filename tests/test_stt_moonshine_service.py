import os
import socket
import subprocess
import sys
import time

import requests


def _wait_for_port(host: str, port: int, timeout_s: float = 120.0) -> None:
    start = time.time()
    while time.time() - start < timeout_s:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            if s.connect_ex((host, port)) == 0:
                return
        time.sleep(1)
    raise TimeoutError(f"Service did not start on {host}:{port} within {timeout_s}s")


def test_stt_moonshine_service_starts():
    env = os.environ.copy()
    env["STT_BACKEND"] = "moonshine"
    env["AUDIO_SERVICE_HOST"] = "127.0.0.1"
    env["AUDIO_SERVICE_PORT"] = "16100"
    env.setdefault("STT_MODEL", "fidoriel/moonshine-tiny-de")

    proc = subprocess.Popen([sys.executable, "-m", "src.stt.service"], env=env)
    try:
        _wait_for_port("127.0.0.1", 16100, timeout_s=180)
        r = requests.get("http://127.0.0.1:16100/health", timeout=5)
        assert r.status_code == 200
        assert r.json().get("backend") == "moonshine"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
