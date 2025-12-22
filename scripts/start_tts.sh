#!/bin/bash
set -e

source .venv/bin/activate

# Ensure external libs are importable - src first, then external packages
export PYTHONPATH="$(pwd)/src:$(pwd)/external:$(pwd)/external/cosyvoice:$(pwd)/external/cosyvoice/third_party/Matcha-TTS:${PYTHONPATH}"

# Start TTS service
exec python3 -m src.tts.service
