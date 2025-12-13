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

# Ensure TTS service gets the correct model name
# Use TTS_MODEL_NAME if set, otherwise fall back to MODEL_NAME
export MODEL_NAME=${TTS_MODEL_NAME:-${MODEL_NAME:-"microsoft/VibeVoice-7B"}}

# Set PYTHONPATH to include src/tts_service so 'vibevoice' can be imported directly
# We also keep $(pwd)/src for other potential imports
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src:$(pwd)/src/tts_service"

# Set NVIDIA library paths (Robust check)
echo ">>> [TTS] Setting up LD_LIBRARY_PATH..."
export LD_LIBRARY_PATH=$(python3 -c 'import os; import nvidia.cublas.lib; import nvidia.cudnn.lib; import torch;
def get_path(m): return os.path.dirname(m.__file__) if hasattr(m, "__file__") and m.__file__ else list(m.__path__)[0] if hasattr(m, "__path__") else "";
print(get_path(nvidia.cublas.lib) + ":" + get_path(nvidia.cudnn.lib) + ":" + os.path.dirname(torch.__file__) + "/lib")'):$LD_LIBRARY_PATH

# Start the service
echo ">>> [TTS] Executing service..."
echo ">>> [TTS] Using model: $MODEL_NAME"
exec python3 src/tts_service/main.py
