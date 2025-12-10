#!/bin/bash
# Start vLLM Service
set -e

echo ">>> [vLLM] Starting vLLM Service..."

# Activate vLLM environment
source .venv_vllm/bin/activate

# Build vLLM command
VLLM_CMD="vllm serve $MODEL_NAME"
VLLM_CMD+=" --host $HOST"
VLLM_CMD+=" --port $PORT"
VLLM_CMD+=" --gpu-memory-utilization $GPU_MEMORY_UTILIZATION"

if [ "$ASYNC_SCHEDULING" = "true" ]; then
    VLLM_CMD+=" --async-scheduling"
fi

echo ">>> [vLLM] Command: $VLLM_CMD"
echo ">>> [vLLM] VRAM Allocation: ${GPU_MEMORY_UTILIZATION}"

# Execute vLLM
exec $VLLM_CMD
