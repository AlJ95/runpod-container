import logging
import os
from typing import Optional

import torch
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from src.tts.cosyvoice_backend import CosyVoiceBackend, CosyVoiceConfig
from src.tts.vibevoice_backend import VibeVoiceBackend, VibeVoiceConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TTS Service")

TTS_BACKEND = os.getenv("TTS_BACKEND", "vibevoice").lower()
DEFAULT_LANGUAGE = os.getenv("LANGUAGE", "en")
HF_TOKEN = os.getenv("HF_TOKEN")

# VibeVoice model name
TTS_MODEL = os.getenv("TTS_MODEL", "aoi-ot/VibeVoice-7B")

# CosyVoice: can be either local dir or HF repo id
COSYVOICE_MODEL_DIR = os.getenv("COSYVOICE_MODEL_DIR", "pretrained_models/Fun-CosyVoice3-0.5B")


def _load_backend():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"[TTS] device={device} backend={TTS_BACKEND}")

    if TTS_BACKEND == "vibevoice":
        return (
            VibeVoiceBackend(VibeVoiceConfig(model_name=TTS_MODEL, hf_token=HF_TOKEN), device=device),
            device,
        )

    if TTS_BACKEND == "cosyvoice":
        # note: CosyVoiceBackend may download from HF if COSYVOICE_MODEL_DIR looks like a repo id
        return (CosyVoiceBackend(CosyVoiceConfig(model_dir=COSYVOICE_MODEL_DIR)), device)

    raise RuntimeError(f"Unknown TTS_BACKEND={TTS_BACKEND}")


try:
    backend, device = _load_backend()
except Exception as e:
    logger.error(f"Fatal error during TTS initialization: {e}")
    raise


@app.post("/v1/tts")
async def tts_endpoint(text: str, voice: str = "default", language: Optional[str] = None):
    try:
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")

        lang = language or DEFAULT_LANGUAGE
        audio_b64 = backend.synthesize_base64(text.strip(), voice=voice)
        sample_rate = getattr(backend, "sample_rate", 24000)

        return JSONResponse(
            content={
                "language": lang,
                "audio_base64": audio_b64,
                "sample_rate": sample_rate,
                "format": "wav",
                "backend": TTS_BACKEND,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("TTS endpoint error")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "tts",
            "backend": TTS_BACKEND,
            "device": str(device),
        }
    )


def main():
    import uvicorn

    host = os.getenv("TTS_SERVICE_HOST", "0.0.0.0")
    port = int(os.getenv("TTS_SERVICE_PORT", "5000"))
    debug = os.getenv("DEBUG_MODE", "false").lower() == "true"

    logger.info(f"Starting TTS service on {host}:{port} backend={TTS_BACKEND}")
    uvicorn.run(app, host=host, port=port, log_level="debug" if debug else "info")


if __name__ == "__main__":
    main()
