#!/bin/bash
# Python Environment Setup Script
# This script sets up separate virtual environments for TTS and Whisper services

set -e

echo ">>> Setting up Python environments with separate venvs for TTS and Whisper..."

# Create virtual environment for TTS service
echo ">>> Creating TTS virtual environment..."
uv venv .venv_tts

# Create virtual environment for Whisper service
echo ">>> Creating Whisper virtual environment..."
uv venv .venv_whisper

# Create virtual environment for vLLM service
echo ">>> Creating vLLM virtual environment..."
uv venv .venv_vllm

echo ">>> Installing TTS dependencies..."
# Activate TTS environment and install dependencies
source .venv_tts/bin/activate
uv pip install --upgrade pip --quiet
uv pip install -r requirements-tts.txt
deactivate

echo ">>> Installing Whisper dependencies..."
# Activate Whisper environment and install dependencies
source .venv_whisper/bin/activate
uv pip install --upgrade pip --quiet
uv pip install -r requirements-whisper.txt
deactivate

echo ">>> Installing vLLM dependencies..."
# Activate vLLM environment and install dependencies
source .venv_vllm/bin/activate
uv pip install --upgrade pip --quiet
uv pip install hf_transfer
uv pip install vllm==0.10.2 --torch-backend=auto
uv pip install nvidia-cublas-cu12 nvidia-cudnn-cu12 nvidia-cuda-nvrtc-cu12 nvidia-cuda-runtime-cu12
deactivate

echo ">>> Python environments setup completed successfully."
echo "TTS environment: .venv_tts"
echo "Whisper environment: .venv_whisper"
echo "vLLM environment: .venv_vllm"
