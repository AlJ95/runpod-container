#!/bin/bash
set -e

echo ">>> Setting up unified Python environment..."

# 1. Create and activate venv
if [ ! -d ".venv" ]; then
    uv venv .venv
fi
source .venv/bin/activate

# 2. Upgrade pip
uv pip install --upgrade pip --quiet

# 3. PRE-INSTALL TORCH (Critical Fix)
# flash-attn requires torch to be present to build its wheels
echo ">>> Pre-installing torch and setuptools..."
uv pip install torch setuptools wheel

# 4. Install the rest of the requirements
echo ">>> Installing remaining dependencies..."
# uv will skip torch since it's already satisfied
uv pip install -r requirements.txt -r requirements.cosyvoice.txt


# Install VibeVoice package in development mode
if [ -d "external/vibevoice" ]; then
    echo ">>> Installing VibeVoice package..."
    uv pip install -e external/vibevoice
else
    echo "ERROR: VibeVoice directory not found at external/vibevoice"
    exit 1
fi

# Install openai-whisper without pulling in its (conflicting) dependency constraints.
# We rely on torch/triton chosen by vLLM.
uv pip install --no-deps openai-whisper==20231117

echo ">>> Setup completed successfully."
echo "Environment: .venv"
