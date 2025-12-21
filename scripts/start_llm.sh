#!/bin/bash
set -e

source .venv/bin/activate

exec python3 -m src.llm.vllm_runner
