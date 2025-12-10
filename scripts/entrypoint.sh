#!/bin/bash
# Main Entrypoint Script
# This script orchestrates the startup of all services with dual venv support

set -e

# Load configuration from environment files
if [ -f "config/vllm_config.env" ]; then
    source config/vllm_config.env
fi

if [ -f "config/services.env" ]; then
    source config/services.env
fi

# Set default values if not set
MODEL_NAME=${MODEL_NAME:-"openai/gpt-oss-20b"}
HOST=${HOST:-"0.0.0.0"}
PORT=${PORT:-8000}
GPU_MEMORY_UTILIZATION=${GPU_MEMORY_UTILIZATION:-0.65}
ASYNC_SCHEDULING=${ASYNC_SCHEDULING:-true}
TTS_SERVICE_PORT=${TTS_SERVICE_PORT:-5000}

# Set up VibeVoice directory structure
echo ">>> Setting up VibeVoice directory structure..."
VIBEVOICE_SRC="vibevoice"
VIBEVOICE_DEST="src/vibevoice_core"

# Check if VibeVoice source directory exists
if [ -d "$VIBEVOICE_SRC" ]; then
    echo "Found VibeVoice source directory: $VIBEVOICE_SRC"

    # Create destination directory if it doesn't exist
    mkdir -p "$VIBEVOICE_DEST"

    # Copy VibeVoice files (or create symlink)
    if [ -d "$VIBEVOICE_DEST" ]; then
        echo "Copying VibeVoice files to $VIBEVOICE_DEST..."
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
    echo "Creating voices directory..."
    mkdir -p "$VOICES_DIR"
fi

# Set NVIDIA library paths for CTranslate2/Whisper
export LD_LIBRARY_PATH=$(python3 -c 'import os; import nvidia.cublas.lib; import nvidia.cudnn.lib; print(os.path.dirname(nvidia.cublas.lib.__file__) + ":" + os.path.dirname(nvidia.cudnn.lib.__file__))'):$LD_LIBRARY_PATH

# Set PYTHONPATH to include vibevoice_core
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Enable HF transfer
export HF_HUB_ENABLE_HF_TRANSFER=1

# Check for HF_TOKEN
[ -z "$HF_TOKEN" ] && echo "WARNING: HF_TOKEN is not set."

echo ">>> Starting AI Inference Services with dual venv approach..."

# Start Whisper Service in background (using Audio/TTS venv)
echo ">>> Starting Whisper Service (Port $AUDIO_SERVICE_PORT)..."
source .venv_audio_tts/bin/activate
python3 src/audio_service/main.py &
WHISPER_PID=$!
echo "Whisper Service PID: $WHISPER_PID"
deactivate

# Start TTS Service in background (using Audio/TTS venv)
echo ">>> Starting VibeVoice TTS Service (Port $TTS_SERVICE_PORT)..."
source .venv_audio_tts/bin/activate
python3 src/tts_service/main.py &
TTS_PID=$!
echo "TTS Service PID: $TTS_PID"
deactivate

# Wait for services to initialize
echo ">>> Waiting 10 seconds for services initialization..."
sleep 10

# Check if both background services are still running
if ! kill -0 $WHISPER_PID 2>/dev/null; then
    echo "ERROR: Whisper Service failed to start"
    exit 1
fi

if ! kill -0 $TTS_PID 2>/dev/null; then
    echo "ERROR: TTS Service failed to start"
    exit 1
fi

# Start vLLM Service in foreground (using vLLM venv)
echo ">>> Starting vLLM Service (Port $PORT)..."
source .venv_vllm/bin/activate

# Build vLLM command
VLLM_CMD="vllm serve $MODEL_NAME"
VLLM_CMD+=" --host $HOST"
VLLM_CMD+=" --port $PORT"
VLLM_CMD+=" --gpu-memory-utilization $GPU_MEMORY_UTILIZATION"

if [ "$ASYNC_SCHEDULING" = "true" ]; then
    VLLM_CMD+=" --async-scheduling"
fi

echo "vLLM Command: $VLLM_CMD"
echo "VRAM Allocation: ${GPU_MEMORY_UTILIZATION} (leaving room for Whisper and VibeVoice)"

# Execute vLLM (this will run in foreground)
exec $VLLM_CMD
