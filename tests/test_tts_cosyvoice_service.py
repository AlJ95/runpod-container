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


def test_tts_cosyvoice_service_starts():
    # This test starts the service process and checks /health.
    # It assumes the CosyVoice model is either already present locally
    # OR can be downloaded from HF (may take long on first run).

    env = os.environ.copy()
    env["TTS_BACKEND"] = "cosyvoice"
    env["TTS_SERVICE_HOST"] = "127.0.0.1"
    env["TTS_SERVICE_PORT"] = "15100"

    # Allow either local model dir or HF repo id
    env.setdefault("COSYVOICE_MODEL_DIR", "pretrained_models/Fun-CosyVoice3-0.5B")

    # Prompt setup (expects voices/jan_ref_mix.wav to exist in repo)
    env.setdefault(
        "COSYVOICE_DEFAULT_PROMPT_TEXT",
        "You are a helpful assistant.<|endofprompt|>Hallo, hier spricht Jan. Als Data Scientist beschäftige ich mich täglich mit AI, Machine Learning und effizientem Information Retrieval.",
    )

    proc = subprocess.Popen([sys.executable, "-m", "src.tts.service"], env=env)
    try:
        _wait_for_port("127.0.0.1", 15100, timeout_s=180)
        r = requests.get("http://127.0.0.1:15100/health", timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert data.get("backend") == "cosyvoice"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
