#!/bin/bash
# Main Entrypoint Script
# This script orchestrates the startup of all services by calling their respective start scripts

set -e

# Load configuration from environment files
if [ -f "config/vllm_config.env" ]; then
    # Source the file to evaluate the ${VAR:-default} syntax properly
    source config/vllm_config.env
fi

if [ -f "config/services.env" ]; then
    # Source the file to evaluate the ${VAR:-default} syntax properly
    source config/services.env
fi

# Set default values if not set
export HOST=${HOST:-"0.0.0.0"}
export PORT=${PORT:-8000}
export GPU_MEMORY_UTILIZATION=${GPU_MEMORY_UTILIZATION:-0.65}
export ASYNC_SCHEDULING=${ASYNC_SCHEDULING:-true}
export TTS_SERVICE_PORT=${TTS_SERVICE_PORT:-5000}
export AUDIO_SERVICE_PORT=${AUDIO_SERVICE_PORT:-6000}

# Export model variables for each service using the unified naming convention
export TTS_MODEL=${TTS_MODEL:-"aoi-ot/VibeVoice-7B"}
export VLLM_MODEL=${VLLM_MODEL:-"openai/gpt-oss-20b"}
export SST_MODEL=${SST_MODEL:-"large-v3"}

# Handle GGUF model download if specified
if [ -n "$GGUF_MODEL_URL" ]; then
    echo ">>> [GGUF] Dynamic GGUF model download enabled"
    echo ">>> [GGUF] Downloading model from: $GGUF_MODEL_URL"

    # Download the GGUF model
    MODEL_PATH=$(bash scripts/download_gguf_model.sh "$GGUF_MODEL_URL")
    export VLLM_MODEL="$MODEL_PATH"

    # Check if tokenizer is specified
    if [ -n "$TOKENIZER_MODEL" ]; then
        echo ">>> [GGUF] Using tokenizer: $TOKENIZER_MODEL"
        export VLLM_TOKENIZER="$TOKENIZER_MODEL"
    else
        echo "WARNING: GGUF model specified but no TOKENIZER_MODEL set"
        echo "Please set TOKENIZER_MODEL to the base model of your GGUF model"
    fi

    echo ">>> [GGUF] Configuration complete"
    echo ">>> [GGUF] Model path: $VLLM_MODEL"
fi

# Enable HF transfer globally
export HF_HUB_ENABLE_HF_TRANSFER=1

# Check for HF_TOKEN
[ -z "$HF_TOKEN" ] && echo "WARNING: HF_TOKEN is not set."

echo ">>> Starting AI Inference Services (Unified Environment)..."

# Start Whisper Service in background
bash scripts/start_whisper.sh &
WHISPER_PID=$!
echo "Whisper Service PID: $WHISPER_PID"

# Start TTS Service in background
bash scripts/start_tts.sh &
TTS_PID=$!
echo "TTS Service PID: $TTS_PID"

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

# Start vLLM Service in foreground
# We use exec to replace the shell process
exec bash scripts/start_vllm.sh
