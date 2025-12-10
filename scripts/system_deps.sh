#!/bin/bash
# System Dependencies Installation Script
# This script installs all required system-level dependencies

set -e
export DEBIAN_FRONTEND=noninteractive

echo ">>> Installing system dependencies..."

# Update package lists
apt-get update -qq

# Install required packages
apt-get install -y -qq \
    ffmpeg \
    git \
    libsndfile1 \
    curl \
    ca-certificates \
    pkg-config \
    build-essential \
    cmake \
    libavdevice-dev \
    libavfilter-dev \
    libavformat-dev \
    libavcodec-dev \
    libswresample-dev \
    libswscale-dev \
    libavutil-dev

echo ">>> System dependencies installed successfully."
