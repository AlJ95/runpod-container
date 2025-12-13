import os
import io
import base64
import logging
import torch
import torchaudio
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import uvicorn

# Import VibeVoice modules directly
from vibevoice.modular.modeling_vibevoice_inference import VibeVoiceForConditionalGenerationInference
from vibevoice.processor.vibevoice_processor import VibeVoiceProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="VibeVoice TTS Service")

# --- Configuration ---
MODEL_NAME = os.getenv("MODEL_NAME", "microsoft/VibeVoice-7B")
DEFAULT_LANGUAGE = os.getenv("LANGUAGE", "en")
HF_TOKEN = os.getenv("HF_TOKEN", None)
TTS_SERVICE_HOST = os.getenv("TTS_SERVICE_HOST", "0.0.0.0")
TTS_SERVICE_PORT = int(os.getenv("TTS_SERVICE_PORT", "5000"))
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

# --- Device ---
device = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Using device: {device}")

# --- Load Model at Startup ---
logger.info(f"[VibeVoice] Loading model '{MODEL_NAME}' on {device}...")

def load_model(model_name: str, hf_token: Optional[str] = None, device: str = "cuda"):
    """Load VibeVoice model with proper configuration"""
    try:
        logger.info(f"Loading processor from {model_name}")
        processor = VibeVoiceProcessor.from_pretrained(model_name, token=hf_token)

        # Determine dtype and attention implementation
        if device == "cuda":
            load_dtype = torch.bfloat16
            attn_impl = "flash_attention_2"
        else:
            load_dtype = torch.float32
            attn_impl = "sdpa"

        logger.info(f"Loading model with dtype={load_dtype}, attn={attn_impl}")

        # Try with flash attention first, fallback to sdpa if needed
        try:
            model = VibeVoiceForConditionalGenerationInference.from_pretrained(
                model_name,
                torch_dtype=load_dtype,
                attn_implementation=attn_impl,
                device_map=device,
                token=hf_token
            )
        except Exception as e:
            logger.warning(f"Warning: Failed to load with {attn_impl}, falling back to sdpa. Error: {e}")
            model = VibeVoiceForConditionalGenerationInference.from_pretrained(
                model_name,
                torch_dtype=load_dtype,
                attn_implementation="sdpa",
                device_map=device,
                token=hf_token
            )

        model.eval()
        return model, processor

    except Exception as e:
        logger.error(f"Failed to load VibeVoice model: {str(e)}")
        raise RuntimeError(f"VibeVoice model loading failed: {str(e)}")

# Load model and processor
try:
    model, processor = load_model(model_name=MODEL_NAME, hf_token=HF_TOKEN, device=device)
    logger.info("VibeVoice model loaded successfully")
except Exception as e:
    logger.error(f"Fatal error during VibeVoice initialization: {str(e)}")
    raise

# Default voice configuration
DEFAULT_VOICE_PATH = "voices/de-jan_man.wav"
VOICES_DIR = "voices"

def get_voice_sample_path(voice_name: str = "default") -> str:
    """
    Get path to voice sample file with fallback logic
    """
    # Try specific voice first
    if voice_name != "default":
        voice_path = os.path.join(VOICES_DIR, f"{voice_name}.wav")
        if os.path.exists(voice_path):
            return voice_path

    # Fallback to default voice
    if os.path.exists(DEFAULT_VOICE_PATH):
        return DEFAULT_VOICE_PATH

    # Try to find any voice in directory
    if os.path.exists(VOICES_DIR):
        wav_files = [f for f in os.listdir(VOICES_DIR) if f.endswith('.wav')]
        if wav_files:
            return os.path.join(VOICES_DIR, wav_files[0])

    raise RuntimeError(f"No voice samples found. Expected voice files in {VOICES_DIR}/")

def synthesize_speech(text: str, language: str = DEFAULT_LANGUAGE, voice_name: str = "default") -> str:
    """
    Generate speech audio from text and return base64-encoded WAV.

    Args:
        text: Text to synthesize
        language: Language code (en, de, zh, etc.)
        voice_name: Voice reference name

    Returns:
        Base64-encoded WAV audio
    """
    try:
        # Get voice sample path
        voice_sample_path = get_voice_sample_path(voice_name)
        logger.info(f"Using voice sample: {voice_sample_path}")

        # Prepare inputs
        inputs = processor(
            text=[text],
            voice_samples=[[voice_sample_path]],
            padding=True,
            return_tensors="pt",
            return_attention_mask=True,
        )

        # Move tensors to device
        for k, v in inputs.items():
            if torch.is_tensor(v):
                inputs[k] = v.to(device)

        # Generate speech
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=None,  # Auto
                cfg_scale=1.3,
                tokenizer=processor.tokenizer,
                generation_config={'do_sample': False},
                is_prefill=True
            )

        # Extract and process audio
        if not hasattr(outputs, 'speech_outputs') or outputs.speech_outputs is None:
            raise RuntimeError("Model generated no speech output.")

        audio = outputs.speech_outputs[0]

        # Ensure it's CPU float32
        audio = audio.detach().cpu().to(torch.float32)

        # Ensure [channels, samples] format for torchaudio.save
        if audio.dim() == 1:
            audio = audio.unsqueeze(0)  # [1, samples]

        # Save to bytes buffer
        buf = io.BytesIO()
        # Sample rate is 24000 according to VibeVoice specs
        torchaudio.save(buf, audio, 24000, format="wav")
        buf.seek(0)

        # Return base64-encoded audio
        return base64.b64encode(buf.read()).decode("utf-8")

    except Exception as e:
        logger.error(f"Speech synthesis failed: {str(e)}")
        raise RuntimeError(f"Speech synthesis failed: {str(e)}")

@app.post("/v1/tts")
async def text_to_speech_endpoint(
    text: str,
    voice: str = "default",
    language: Optional[str] = None
):
    """
    Text-to-Speech endpoint

    Args:
        text: Text to convert to speech
        voice: Voice reference name (default, or filename without .wav)
        language: Optional language code

    Returns:
        JSON with base64-encoded audio and metadata
    """
    try:
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")

        # Use provided language or default
        lang = language if language else DEFAULT_LANGUAGE

        # Generate speech
        audio_b64 = synthesize_speech(text.strip(), language=lang, voice_name=voice)

        return JSONResponse(content={
            "language": lang,
            "audio_base64": audio_b64,
            "sample_rate": 24000,
            "format": "wav"
        })

    except Exception as e:
        logger.error(f"TTS endpoint error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"TTS generation failed: {str(e)}"
        )

@app.get("/v1/voices")
async def list_voices_endpoint():
    """List available voice references"""
    try:
        if not os.path.exists(VOICES_DIR):
            return JSONResponse(content={"voices": []})

        voices = []
        for filename in os.listdir(VOICES_DIR):
            if filename.endswith('.wav'):
                voice_name = filename[:-4]  # Remove .wav extension
                voices.append(voice_name)

        # Add default voice if it exists
        if os.path.exists(DEFAULT_VOICE_PATH) and "de-jan_man" not in voices:
            voices.insert(0, "de-jan_man")

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
        "device": str(device),
        "voices_available": os.path.exists(VOICES_DIR),
        "default_voice": os.path.exists(DEFAULT_VOICE_PATH)
    })

if __name__ == "__main__":
    logger.info(f"Starting VibeVoice TTS Service on {TTS_SERVICE_HOST}:{TTS_SERVICE_PORT}")
    logger.info(f"Model: {MODEL_NAME}")
    logger.info(f"Default voice: {DEFAULT_VOICE_PATH}")
    logger.info(f"Voices directory: {VOICES_DIR}")

    uvicorn.run(
        app,
        host=TTS_SERVICE_HOST,
        port=TTS_SERVICE_PORT,
        log_level="info" if not DEBUG_MODE else "debug"
    )
