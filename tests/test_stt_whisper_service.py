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


@pytest.mark.skipif(os.getenv("RUN_BACKEND_TESTS") != "1", reason="Set RUN_BACKEND_TESTS=1 to run Whisper backend test")
def test_stt_whisper_service_starts():
    env = os.environ.copy()
    env["STT_BACKEND"] = "whisper"
    env["AUDIO_SERVICE_HOST"] = "127.0.0.1"
    env["AUDIO_SERVICE_PORT"] = "16101"

    # Use a small model by default for test runtime.
    # You can override to large-v3 via env when you really want to test it.
    env.setdefault("WHISPER_MODEL", "tiny")
    # cpu-friendly default
    env.setdefault("WHISPER_COMPUTE_TYPE", "int8")

    proc = subprocess.Popen([sys.executable, "-m", "src.stt.service"], env=env)
    try:
        _wait_for_port("127.0.0.1", 16101, timeout_s=180)
        r = requests.get("http://127.0.0.1:16101/health", timeout=5)
        assert r.status_code == 200
        assert r.json().get("backend") == "whisper"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
