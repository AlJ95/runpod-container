#!/bin/bash
set -e

source .venv/bin/activate

# Start STT service
exec python3 -m src.stt.service
