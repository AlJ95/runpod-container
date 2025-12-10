#!/bin/bash
# Start TTS Service
set -e

echo ">>> [TTS] Starting VibeVoice TTS Service..."

# Set up VibeVoice directory structure
echo ">>> [TTS] Setting up VibeVoice directory structure..."
VIBEVOICE_SRC="src/tts_service/vibevoice"
VIBEVOICE_DEST="src/vibevoice_core"

# Check if VibeVoice source directory exists
if [ -d "$VIBEVOICE_SRC" ]; then
    echo ">>> [TTS] Found VibeVoice source directory: $VIBEVOICE_SRC"

    # Create destination directory if it doesn't exist
    mkdir -p "$VIBEVOICE_DEST"

    # Copy VibeVoice files (or create symlink)
    if [ -d "$VIBEVOICE_DEST" ]; then
        echo ">>> [TTS] Copying VibeVoice files to $VIBEVOICE_DEST..."
        cp -r "$VIBEVOICE_SRC"/* "$VIBEVOICE_DEST"/
    else
        echo "ERROR: Failed to create VibeVoice destination directory"
        exit 1
    fi
else
    echo "WARNING: VibeVoice source directory not found at $VIBEVOICE_SRC"
    echo "TTS service will fail to start without VibeVoice files"
fi

# Create voices directory if it doesn't exist
VOICES_DIR="voices"
if [ ! -d "$VOICES_DIR" ]; then
    echo ">>> [TTS] Creating voices directory..."
    mkdir -p "$VOICES_DIR"
fi

# Activate TTS environment
source .venv_tts/bin/activate

# Set PYTHONPATH to include vibevoice_core
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Start the service
echo ">>> [TTS] Executing service..."
exec python3 src/tts_service/main.py
