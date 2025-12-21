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


import pytest


@pytest.mark.skipif(os.getenv("RUN_BACKEND_TESTS") != "1", reason="Set RUN_BACKEND_TESTS=1 to run VibeVoice backend test")
def test_tts_vibevoice_service_starts():
    env = os.environ.copy()
    env["TTS_BACKEND"] = "vibevoice"
    env["TTS_SERVICE_HOST"] = "127.0.0.1"
    env["TTS_SERVICE_PORT"] = "15101"

    # default model is huge; allow override for testing
    env.setdefault("TTS_MODEL", "aoi-ot/VibeVoice-7B")

    proc = subprocess.Popen([sys.executable, "-m", "src.tts.service"], env=env)
    try:
        _wait_for_port("127.0.0.1", 15101, timeout_s=180)
        r = requests.get("http://127.0.0.1:15101/health", timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert data.get("backend") == "vibevoice"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
