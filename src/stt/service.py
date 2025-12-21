import logging
import os
import shutil
from typing import Any, Dict

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from src.stt.moonshine_backend import MoonshineBackend, MoonshineConfig
from src.stt.whisper_backend import WhisperBackend, WhisperConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="STT Service")

STT_BACKEND = os.getenv("STT_BACKEND", "whisper").lower()

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "large-v3")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "float16")

STT_MODEL = os.getenv("STT_MODEL", "fidoriel/moonshine-tiny-de")


def _load_backend():
    if STT_BACKEND == "whisper":
        return WhisperBackend(WhisperConfig(model_name=WHISPER_MODEL, compute_type=WHISPER_COMPUTE_TYPE))
    if STT_BACKEND == "moonshine":
        return MoonshineBackend(MoonshineConfig(model_name=STT_MODEL))
    raise RuntimeError(f"Unknown STT_BACKEND={STT_BACKEND}")


try:
    backend = _load_backend()
except Exception as e:
    logger.error(f"Fatal error during STT initialization: {e}")
    raise


@app.post("/v1/audio/transcriptions")
async def transcribe_audio(file: UploadFile = File(...)) -> Dict[str, Any]:
    temp_filename = f"temp_{file.filename}"

    try:
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = backend.transcribe(temp_filename)
        return result

    except Exception as e:
        logger.exception("STT failed")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(temp_filename):
            try:
                os.remove(temp_filename)
            except Exception:
                pass


@app.get("/health")
async def health():
    return JSONResponse(content={"status": "healthy", "service": "stt", "backend": STT_BACKEND})


def main():
    import uvicorn

    host = os.getenv("AUDIO_SERVICE_HOST", "0.0.0.0")
    port = int(os.getenv("AUDIO_SERVICE_PORT", "6000"))
    debug = os.getenv("DEBUG_MODE", "false").lower() == "true"

    logger.info(f"Starting STT service on {host}:{port} backend={STT_BACKEND}")
    uvicorn.run(app, host=host, port=port, log_level="debug" if debug else "info")


if __name__ == "__main__":
    main()
