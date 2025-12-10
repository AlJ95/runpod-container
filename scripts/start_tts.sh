#!/bin/bash
# Start TTS Service
set -e

echo ">>> [TTS] Starting VibeVoice TTS Service..."

# Create voices directory if it doesn't exist
VOICES_DIR="voices"
if [ ! -d "$VOICES_DIR" ]; then
    echo ">>> [TTS] Creating voices directory..."
    mkdir -p "$VOICES_DIR"
fi

# Activate unified environment
source .venv/bin/activate

# Set PYTHONPATH to include src/tts_service so 'vibevoice' can be imported directly
# We also keep $(pwd)/src for other potential imports
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src:$(pwd)/src/tts_service"

# Start the service
echo ">>> [TTS] Executing service..."
exec python3 src/tts_service/main.py
