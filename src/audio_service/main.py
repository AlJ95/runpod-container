from fastapi import FastAPI, UploadFile, File, HTTPException
from faster_whisper import WhisperModel
import os
import shutil
import logging
from typing import Dict, Any
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Whisper Service")

def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables"""
    config = {
        "model": os.getenv("WHISPER_MODEL", "large-v3"),
        "compute_type": os.getenv("WHISPER_COMPUTE_TYPE", "float16"),
        "host": os.getenv("AUDIO_SERVICE_HOST", "0.0.0.0"),
        "port": int(os.getenv("AUDIO_SERVICE_PORT", "6000")),
        "debug": os.getenv("DEBUG_MODE", "false").lower() == "true"
    }
    return config

# Load configuration
config = load_config()

# Initialize Whisper model
logger.info(f"Loading Whisper Model {config['model']}...")
try:
    model = WhisperModel(
        config["model"],
        device="cuda",
        compute_type=config["compute_type"]
    )
    logger.info("Whisper Model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load Whisper model: {str(e)}")
    raise

@app.post("/v1/audio/transcriptions")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribe audio file using Faster-Whisper

    Args:
        file: Audio file to transcribe

    Returns:
        Dict containing transcription text, language, and language probability
    """
    temp_filename = f"temp_{file.filename}"

    try:
        logger.info(f"Processing audio file: {file.filename}")

        # Save file temporarily
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Transcribe audio
        segments, info = model.transcribe(temp_filename, beam_size=5, vad_filter=True, vad_parameters=dict(min_silence_duration_ms=500))

        # Build full text
        full_text = "".join([segment.text for segment in segments])

        logger.info(f"Transcription completed for {file.filename}")

        return {
            "text": full_text.strip(),
            "language": info.language,
            "language_probability": info.language_probability
        }

    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Clean up temporary file
        if os.path.exists(temp_filename):
            try:
                os.remove(temp_filename)
                logger.debug(f"Removed temporary file: {temp_filename}")
            except Exception as e:
                logger.warning(f"Failed to remove temporary file: {str(e)}")

if __name__ == "__main__":
    logger.info(f"Starting Whisper Service on {config['host']}:{config['port']}")
    uvicorn.run(
        app,
        host=config["host"],
        port=config["port"],
        log_level="info" if not config["debug"] else "debug"
    )
