# AI Inference Server for RunPod

Multi-Model AI Inference Server designed to run on RunPod with multiple RTX GPUs. This server provides LLM (vLLM), STT (Faster-Whisper), and future TTS (VibeVoice) services in a single Docker container.

## Features

- **vLLM Service**: High-performance LLM inference with GPU acceleration
- **Faster-Whisper Service**: Speech-to-text transcription with FastAPI interface
- **VRAM Management**: Intelligent GPU memory allocation between services
- **Containerized**: Ready-to-deploy Docker container
- **Configurable**: Environment-based configuration for easy customization

## Architecture

```
ai-inference-server/
├── config/                 # Configuration files
│   ├── vllm_config.env     # vLLM server parameters
│   └── services.env        # Service ports and settings
├── scripts/                # Installation and startup scripts
│   ├── system_deps.sh      # System dependencies
│   ├── setup.sh            # Python environment
│   └── entrypoint.sh       # Main entrypoint
├── src/                    # Application code
│   ├── audio_service/      # Faster-Whisper FastAPI service
│   │   ├── __init__.py
│   │   └── main.py
│   └── tts_service/        # Future VibeVoice integration
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container configuration
└── README.md               # This file
```

## Services

### 1. vLLM Service (Port 8000)
- **Model**: OpenAI GPT-OSS-20B (configurable)
- **GPU Memory**: 85% utilization (leaves 15% for other services)
- **API**: OpenAI-compatible REST API
- **Features**: Async scheduling, tensor parallelism

### 2. Audio Service (Port 6000)
- **Model**: Faster-Whisper Large-v3
- **Compute Type**: float16
- **API**: Custom REST API at `/v1/audio/transcriptions`
- **Features**: Automatic language detection, beam search

### 3. TTS Service (VibeVoice - Port 5000)
- **Model**: VibeVoice 1.5B custom framework
- **API**: REST API at `/v1/tts` for text-to-speech
- **Features**: Voice cloning, multi-speaker support, language detection
- **VRAM**: 4-6 GB allocation with FlashAttention

## Setup and Deployment

### Prerequisites
- Docker with NVIDIA Container Toolkit
- NVIDIA GPUs with CUDA 12.1 support
- RunPod account with RTX GPU instances

### Configuration

Edit the configuration files before building:

1. **vLLM Configuration** (`config/vllm_config.env`):
   ```env
   MODEL_NAME="openai/gpt-oss-20b"
   HOST="0.0.0.0"
   PORT=8000
   GPU_MEMORY_UTILIZATION=0.65  # Reduced for VibeVoice compatibility
   ```

2. **Services Configuration** (`config/services.env`):
   ```env
   AUDIO_SERVICE_PORT=6000
   WHISPER_MODEL="large-v3"
   WHISPER_COMPUTE_TYPE="float16"
   TTS_SERVICE_PORT=5000
   VIBEVOICE_MODEL_PATH="vibevoice/models/1.5B"
   VIBEVOICE_VOICES_DIR="voices"
   ```

### Dual Virtual Environment Setup

**Important**: This project uses separate virtual environments to resolve dependency conflicts:

- `.venv_vllm/` - For vLLM service (requires newer tokenizers)
- `.venv_audio_tts/` - For Whisper + TTS services (requires older tokenizers)

**Setup Instructions**:
```bash
# Use the provided setup script
./scripts/setup.sh

# This will create both environments and install dependencies separately
```

**Do NOT** install all dependencies in a single environment - use the provided script.

### VibeVoice Setup (Required)

1. **Clone VibeVoice Repository**:
   ```bash
   git clone https://github.com/your-repo/vibevoice.git
   ```

2. **Place VibeVoice Files**:
   - Ensure the `vibevoice/` directory is in your project root
   - The entrypoint script will automatically copy files to `src/vibevoice_core/`

3. **Voice References**:
   - Create a `voices/` directory in your project root
   - Add `.wav` files for voice references (e.g., `default.wav`, `female.wav`)

### Building the Container

```bash
docker build -t ai-inference-server .
```

### Running the Container

```bash
docker run --gpus all \
           -p 8000:8000 \
           -p 6000:6000 \
           -e HF_TOKEN=your_huggingface_token \
           ai-inference-server
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HF_TOKEN` | Hugging Face API token | (required) |
| `MODEL_NAME` | vLLM model name | `openai/gpt-oss-20b` |
| `GPU_MEMORY_UTILIZATION` | vLLM GPU memory usage | `0.85` |
| `AUDIO_SERVICE_PORT` | Whisper service port | `6000` |
| `WHISPER_MODEL` | Whisper model name | `large-v3` |

## API Endpoints

### vLLM Service
- **Base URL**: `http://localhost:8000`
- **OpenAI Compatible**: Use standard OpenAI API clients

### Audio Service
- **POST** `/v1/audio/transcriptions`
  - **Content-Type**: `multipart/form-data`
  - **Parameter**: `file` (audio file)
  - **Response**:
    ```json
    {
      "text": "transcribed text",
      "language": "en",
      "language_probability": 0.99
    }
    ```

### TTS Service
- **POST** `/v1/tts`
  - **Content-Type**: `application/json`
  - **Parameters**:
    ```json
    {
      "text": "Hello world",
      "voice": "default",
      "speaker_id": 1,
      "language": "en"
    }
    ```
  - **Response**: Audio file in WAV format

- **GET** `/v1/voices`
  - **Response**:
    ```json
    {
      "voices": ["default", "female", "male"]
    }
    ```

- **GET** `/health`
  - **Response**:
    ```json
    {
      "status": "healthy",
      "service": "tts",
      "model_loaded": true,
      "device": "cuda",
      "voices_available": true
    }
    ```

## VRAM Management

The server implements intelligent VRAM allocation for stable multi-service operation:

| Service | VRAM Allocation | Method |
|---------|-----------------|--------|
| vLLM | 65-70% | `--gpu-memory-utilization 0.65` |
| Whisper | 2-4 GB | Dynamic allocation |
| VibeVoice | 4-6 GB | Fixed allocation with FlashAttention |
| Buffer | 1-2 GB | Safety margin for CUDA operations |

**Total**: ~90-95% VRAM utilization with proper service isolation

**Key Changes**:
- Reduced vLLM allocation from 85% to 65% to prevent OOM crashes
- VibeVoice 1.5B model requires dedicated VRAM with FlashAttention overhead
- Whisper uses dynamic allocation based on available resources

## Development

### Running Services Locally

1. Install system dependencies:
   ```bash
   ./scripts/system_deps.sh
   ```

2. Set up Python environment:
   ```bash
   ./scripts/setup.sh
   ```

3. Start services:
   ```bash
   ./scripts/entrypoint.sh
   ```

### Testing

- **vLLM**: Test with OpenAI API clients
- **Audio Service**: Use `curl` to test transcription:
  ```bash
  curl -X POST -F "file=@test.wav" http://localhost:6000/v1/audio/transcriptions
  ```

## Future Enhancements

- VibeVoice TTS integration
- Multi-GPU support
- Load balancing
- Monitoring and metrics
- Authentication and rate limiting

## Troubleshooting

- **CUDA Errors**: Ensure NVIDIA drivers and Container Toolkit are properly installed
- **Memory Issues**: Adjust `GPU_MEMORY_UTILIZATION` in `vllm_config.env`
- **Port Conflicts**: Check exposed ports and firewall settings

## License

MIT License - See LICENSE file for details

## GGUF Model Support

### Quick Start
```bash
docker run --gpus all \
           -e GGUF_MODEL_URL="https://huggingface.co/unsloth/gpt-oss-20b-GGUF/resolve/main/gpt-oss-20b-Q6_K.gguf" \
           -e TOKENIZER_MODEL="unsloth/gpt-oss-20b" \
           ai-inference-server
```

### Configuration
- `GGUF_MODEL_URL`: Hugging Face GGUF model URL
- `TOKENIZER_MODEL`: Base model for tokenizer (required)

### Features
- Automatic download to `/workspace/models/gguf/`
- Model caching for fast subsequent starts
- Works with unsloth GGUF models
- Persistent storage in workspace

⚠️ **Required**: Always set `TOKENIZER_MODEL` when using GGUF models
