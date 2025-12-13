#!/bin/bash
# Start vLLM Service
set -e

echo ">>> [vLLM] Starting vLLM Service..."

# Activate unified environment
source .venv/bin/activate

# Set NVIDIA library paths (Robust check)
echo ">>> [vLLM] Setting up LD_LIBRARY_PATH..."
export LD_LIBRARY_PATH=$(python3 -c 'import os; import nvidia.cublas.lib; import nvidia.cudnn.lib; import torch;
def get_path(m): return os.path.dirname(m.__file__) if hasattr(m, "__file__") and m.__file__ else list(m.__path__)[0] if hasattr(m, "__path__") else "";
print(get_path(nvidia.cublas.lib) + ":" + get_path(nvidia.cudnn.lib) + ":" + os.path.dirname(torch.__file__) + "/lib")'):$LD_LIBRARY_PATH

# Build vLLM command using VLLM_MODEL directly
VLLM_CMD="vllm serve $VLLM_MODEL"
echo ">>> [vLLM] Using model: $VLLM_MODEL"
VLLM_CMD+=" --host $HOST"
VLLM_CMD+=" --port $PORT"
VLLM_CMD+=" --gpu-memory-utilization $GPU_MEMORY_UTILIZATION"
VLLM_CMD+="${EXTRA_VLLM_ARGS}"

if [ "$ASYNC_SCHEDULING" = "true" ]; then
    VLLM_CMD+=" --async-scheduling"
fi

echo ">>> [vLLM] Command: $VLLM_CMD"
echo ">>> [vLLM] VRAM Allocation: ${GPU_MEMORY_UTILIZATION}"

# Execute vLLM
exec $VLLM_CMD
