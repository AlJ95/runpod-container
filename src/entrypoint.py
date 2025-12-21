import os
import signal
import subprocess
import sys
import time


def _start(name: str, cmd: list[str]) -> subprocess.Popen:
    print(f">>> Starting {name}: {' '.join(cmd)}", flush=True)
    return subprocess.Popen(cmd)


def main() -> None:
    # Start STT and TTS in background
    stt = _start("STT", [sys.executable, "-m", "src.stt.service"])
    tts = _start("TTS", [sys.executable, "-m", "src.tts.service"])

    # Give them a moment
    time.sleep(2)

    # If either dies early, fail fast
    if stt.poll() is not None:
        raise SystemExit(f"STT exited early with code {stt.returncode}")
    if tts.poll() is not None:
        raise SystemExit(f"TTS exited early with code {tts.returncode}")

    # Run vLLM in foreground (this replaces this process)
    os.execvp(sys.executable, [sys.executable, "-m", "src.llm.vllm_runner"])


if __name__ == "__main__":
    main()
