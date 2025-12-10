#!/bin/bash
# Python Environment Setup Script
# This script sets up separate virtual environments for each service

set -e

echo ">>> Setting up Python environments with dual venv approach..."

# Create virtual environment for vLLM service
echo ">>> Creating vLLM virtual environment..."
uv venv .venv_vllm

# Create virtual environment for Audio & TTS services
echo ">>> Creating Audio/TTS virtual environment..."
uv venv .venv_audio_tts

echo ">>> Installing vLLM dependencies..."
# Activate vLLM environment and install dependencies
source .venv_vllm/bin/activate
uv pip install --upgrade pip --quiet
uv pip install hf_transfer
uv pip install vllm==0.10.2 --torch-backend=auto
uv pip install nvidia-cublas-cu12 nvidia-cudnn-cu12 nvidia-cuda-nvrtc-cu12 nvidia-cuda-runtime-cu12

echo ">>> Installing Audio & TTS dependencies..."
# Deactivate and activate Audio/TTS environment
deactivate
source .venv_audio_tts/bin/activate
uv pip install --upgrade pip --quiet

# Install Faster-Whisper and API dependencies
uv pip install faster-whisper==0.10.0 fastapi uvicorn python-multipart

# Install VibeVoice TTS dependencies
uv pip install vector-quantize-pytorch==1.12.0 vocos==0.1.0

# Install NVIDIA CUDA libraries for Audio/TTS
uv pip install nvidia-cublas-cu12 nvidia-cudnn-cu12 nvidia-cuda-nvrtc-cu12 nvidia-cuda-runtime-cu12

echo ">>> Python environments setup completed successfully."
echo "vLLM environment: .venv_vllm"
echo "Audio/TTS environment: .venv_audio_tts"
