#!/bin/bash
# System Dependencies Installation Script
# This script installs all required system-level dependencies

set -e
export DEBIAN_FRONTEND=noninteractive

echo ">>> Installing system dependencies..."

# Update package lists
apt-get update -qq

# Install required packages
RUN apt-get update && apt-get install -y \
    ffmpeg libsndfile1 git \
    python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

echo ">>> System dependencies installed successfully."
