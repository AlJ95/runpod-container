from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
import os
import sys
import logging
import tempfile
import shutil
from typing import Dict, Any, Optional
import uvicorn
import torch
import importlib.util

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="VibeVoice TTS Service")

def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables"""
    config = {
        "host": os.getenv("TTS_SERVICE_HOST", "0.0.0.0"),
        "port": int(os.getenv("TTS_SERVICE_PORT", "5000")),
        "debug": os.getenv("DEBUG_MODE", "false").lower() == "true",
        "model_path": os.getenv("VIBEVOICE_MODEL_PATH", "vibevoice/models/1.5B"),
        "voices_dir": os.getenv("VIBEVOICE_VOICES_DIR", "voices"),
        "device": "cuda" if torch.cuda.is_available() else "cpu"
    }
    return config

# Load configuration
config = load_config()

def load_vibevoice_model() -> Any:
    """Dynamically load VibeVoice model from vibevoice_core"""
    try:
        # Add vibevoice_core to Python path if not already there
        vibevoice_path = os.path.join(os.path.dirname(__file__), "..", "vibevoice_core")
        if vibevoice_path not in sys.path:
            sys.path.append(vibevoice_path)

        # Import VibeVoice modules
        vibevoice_module = importlib.import_module("vibevoice")
        model_module = importlib.import_module("vibevoice.model")

        logger.info(f"Loading VibeVoice model from {config['model_path']}...")
        logger.info(f"Using device: {config['device']}")

        # Load model (this is a simplified example - adjust based on actual VibeVoice API)
        model = model_module.VibeVoiceModel(
            model_path=config["model_path"],
            device=config["device"]
        )

        logger.info("VibeVoice model loaded successfully")
        return model

    except Exception as e:
        logger.error(f"Failed to load VibeVoice model: {str(e)}")
        raise RuntimeError(f"VibeVoice model loading failed: {str(e)}")

def load_voice_reference(voice_name: str) -> Optional[str]:
    """Load voice reference audio file"""
    voice_path = os.path.join(config["voices_dir"], f"{voice_name}.wav")
    if os.path.exists(voice_path):
        return voice_path
    return None

# Initialize VibeVoice model
try:
    vibevoice_model = load_vibevoice_model()
except Exception as e:
    logger.error(f"Fatal error during VibeVoice initialization: {str(e)}")
    raise

@app.post("/v1/tts")
async def text_to_speech(
    text: str,
    voice: str = "default",
    speaker_id: Optional[int] = None,
    language: Optional[str] = None
):
    """
    Convert text to speech using VibeVoice

    Args:
        text: Text to convert to speech
        voice: Voice reference name
        speaker_id: Optional speaker ID
        language: Optional language code

    Returns:
        Audio file in WAV format
    """
    try:
        logger.info(f"Processing TTS request: text_length={len(text)}, voice={voice}")

        # Load voice reference
        voice_ref_path = load_voice_reference(voice)
        if voice_ref_path is None:
            raise HTTPException(
                status_code=400,
                detail=f"Voice reference not found: {voice}"
            )

        # Create temporary output file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            output_path = temp_audio.name

        try:
            # Generate speech (simplified - adjust based on actual VibeVoice API)
            audio_data = vibevoice_model.generate(
                text=text,
                voice_reference=voice_ref_path,
                speaker_id=speaker_id,
                language=language,
                output_path=output_path
            )

            logger.info(f"TTS generation completed for text: {text[:50]}...")

            # Return audio file
            return FileResponse(
                output_path,
                media_type="audio/wav",
                filename=f"tts_output_{voice}.wav"
            )

        except Exception as e:
            # Clean up temp file if generation fails
            if os.path.exists(output_path):
                os.remove(output_path)
            raise

    except Exception as e:
        logger.error(f"TTS generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"TTS generation failed: {str(e)}"
        )

@app.get("/v1/voices")
async def list_voices():
    """List available voice references"""
    try:
        if not os.path.exists(config["voices_dir"]):
            return JSONResponse(content={"voices": []})

        voices = []
        for filename in os.listdir(config["voices_dir"]):
            if filename.endswith(".wav"):
                voice_name = filename[:-4]  # Remove .wav extension
                voices.append(voice_name)

        return JSONResponse(content={"voices": sorted(voices)})

    except Exception as e:
        logger.error(f"Failed to list voices: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list voices: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(content={
        "status": "healthy",
        "service": "tts",
        "model_loaded": True,
        "device": config["device"],
        "voices_available": os.path.exists(config["voices_dir"])
    })

if __name__ == "__main__":
    logger.info(f"Starting VibeVoice TTS Service on {config['host']}:{config['port']}")
    logger.info(f"Model path: {config['model_path']}")
    logger.info(f"Voices directory: {config['voices_dir']}")

    uvicorn.run(
        app,
        host=config["host"],
        port=config["port"],
        log_level="info" if not config["debug"] else "debug"
    )
