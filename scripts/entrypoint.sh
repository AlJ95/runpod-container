#!/bin/bash
# Unified entrypoint
set -e

# Load grouped configuration
if [ -f "config/config.env" ]; then
  source config/config.env
fi

export HF_HUB_ENABLE_HF_TRANSFER=1

# Warn about HF_TOKEN
[ -z "$HF_TOKEN" ] && echo "WARNING: HF_TOKEN is not set."

# Ensure external libs are importable
export PYTHONPATH="${PYTHONPATH}:$(pwd)/external/cosyvoice:$(pwd)/external/cosyvoice/third_party/Matcha-TTS:$(pwd)/external/vibevoice"

echo ">>> Starting services (STT + TTS background, LLM foreground)..."

# Start STT in background
echo ">>> Starting STT service..."
bash scripts/start_stt.sh &

# Start TTS in background
echo ">>> Starting TTS service..."
bash scripts/start_tts.sh &

# Give them a moment to start
sleep 2

# Start LLM in foreground
echo ">>> Starting LLM service..."
exec bash scripts/start_llm.sh
