#!/bin/bash
set -e

source .venv/bin/activate

# Ensure external libs are importable
export PYTHONPATH="${PYTHONPATH}:$(pwd)/external/cosyvoice:$(pwd)/external/cosyvoice/third_party/Matcha-TTS:$(pwd)/external/vibevoice"

# Start TTS service
exec python3 -m src.tts.service
