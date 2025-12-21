#!/bin/bash
# Unified Python Environment Setup Script
# Sets up a single virtual environment for all services

set -e

echo ">>> Setting up unified Python environment..."

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo ">>> Creating virtual environment (.venv)..."
    uv venv .venv
else
    echo ">>> Virtual environment (.venv) already exists."
fi

# Activate environment
source .venv/bin/activate

echo ">>> Installing dependencies from requirements.txt..."
uv pip install --upgrade pip --quiet

# Install main project deps + CosyVoice runtime deps (CosyVoice is vendored under external/cosyvoice)
# Using a unified env keeps all services in one runtime.
#
# IMPORTANT:
# We do NOT install external/cosyvoice/requirements.txt directly, because it pins
# torch/torchaudio to versions that conflict with vLLM.
uv pip install -r requirements.txt -r requirements.cosyvoice.txt

# Install openai-whisper without pulling in its (conflicting) dependency constraints.
# We rely on torch/triton chosen by vLLM.
uv pip install --no-deps openai-whisper==20231117

echo ">>> Setup completed successfully."
echo "Environment: .venv"
