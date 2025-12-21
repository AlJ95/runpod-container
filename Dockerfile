# AI Inference Server Dockerfile
# Multi-stage build for optimized container

# Base stage - System setup
FROM nvidia/cuda:12.1.1-base-ubuntu22.04 as base

# Install system dependencies
COPY scripts/system_deps.sh /tmp/system_deps.sh
RUN chmod +x /tmp/system_deps.sh && \
    /tmp/system_deps.sh && \
    rm /tmp/system_deps.sh

# Python stage - Environment setup
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

# Set working directory
WORKDIR /app

# Copy all files
COPY . .

# Create voices directory + external
RUN mkdir -p voices external

# Build-time clone of CosyVoice (includes Matcha-TTS submodule)
RUN rm -rf external/cosyvoice && \
    git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git external/cosyvoice

# Install Python, uv, and build dependencies
RUN apt-get update -qq && \
    apt-get install -y -qq python3 python3-pip \
    pkg-config \
    build-essential \
    cmake \
    git \
    libavdevice-dev \
    libavfilter-dev \
    libavformat-dev \
    libavcodec-dev \
    libswresample-dev \
    libswscale-dev \
    libavutil-dev && \
    pip install uv

# Set up Python environment
RUN chmod +x scripts/setup.sh && \
    ./scripts/setup.sh

# Make scripts executable
RUN chmod +x scripts/*.sh

# Set environment variables
ENV PYTHONPATH=/app:/app/src:/app/external/cosyvoice:/app/external/cosyvoice/third_party/Matcha-TTS:/app/external/vibevoice
ENV PATH=/app/.venv/bin:$PATH

# Expose ports
EXPOSE 8000 6000 5000

# Entrypoint
ENTRYPOINT ["./scripts/entrypoint.sh"]
