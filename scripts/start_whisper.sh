#!/bin/bash
# Start Whisper Service
set -e

echo ">>> [Whisper] Starting Whisper Service..."

# Activate unified environment
source .venv/bin/activate

# Set NVIDIA library paths for CTranslate2/Whisper
# We use the robust python script to handle both standard and namespace packages
echo ">>> [Whisper] Setting up LD_LIBRARY_PATH..."
export LD_LIBRARY_PATH=$(python3 -c 'import os; import nvidia.cublas.lib; import nvidia.cudnn.lib; import torch; 
def get_path(m): return os.path.dirname(m.__file__) if hasattr(m, "__file__") and m.__file__ else list(m.__path__)[0] if hasattr(m, "__path__") else ""; 
print(get_path(nvidia.cublas.lib) + ":" + get_path(nvidia.cudnn.lib) + ":" + os.path.dirname(torch.__file__) + "/lib")'):$LD_LIBRARY_PATH

# Start the service
echo ">>> [Whisper] Executing service..."
exec python3 src/audio_service/main.py
