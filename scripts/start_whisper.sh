#!/bin/bash
# Start Whisper Service
set -e

echo ">>> [Whisper] Starting Whisper Service..."

# Activate Whisper environment
source .venv_whisper/bin/activate

# Start the service
echo ">>> [Whisper] Executing service..."
exec python3 src/audio_service/main.py
