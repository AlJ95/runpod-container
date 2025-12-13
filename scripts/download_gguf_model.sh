#!/bin/bash
# GGUF Model Download Script
# Downloads GGUF models from Huggingface to workspace for persistent storage

set -e

# Create workspace models directory if it doesn't exist
WORKSPACE_GGUF_DIR="/workspace/models/gguf"
mkdir -p "$WORKSPACE_GGUF_DIR"

# Check if model URL is provided
if [ -z "$1" ]; then
    echo "ERROR: No GGUF model URL provided"
    echo "Usage: $0 <model-url>"
    exit 1
fi

# Extract model name from URL
MODEL_URL="$1"
MODEL_NAME=$(basename "$MODEL_URL")
LOCAL_PATH="$WORKSPACE_GGUF_DIR/$MODEL_NAME"

# Check if model already exists
if [ -f "$LOCAL_PATH" ]; then
    echo ">>> [GGUF] Model already exists: $LOCAL_PATH"
    echo "$LOCAL_PATH"
    exit 0
fi

# Download with progress
echo ">>> [GGUF] Downloading model from $MODEL_URL"
echo ">>> [GGUF] This may take a while depending on model size..."

# Use curl with progress bar
curl -L -o "$LOCAL_PATH" "$MODEL_URL" --progress-bar

# Verify download
if [ ! -f "$LOCAL_PATH" ] || [ ! -s "$LOCAL_PATH" ]; then
    echo "ERROR: GGUF model download failed"
    echo "File not found or empty: $LOCAL_PATH"
    exit 1
fi

# Get file size for verification
FILE_SIZE=$(du -h "$LOCAL_PATH" | cut -f1)
echo ">>> [GGUF] Model downloaded successfully: $LOCAL_PATH ($FILE_SIZE)"
echo "$LOCAL_PATH"
