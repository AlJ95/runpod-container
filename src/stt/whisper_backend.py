import logging
from dataclasses import dataclass
from typing import Any, Dict

logger = logging.getLogger(__name__)


@dataclass
class WhisperConfig:
    model_name: str
    compute_type: str


class WhisperBackend:
    def __init__(self, cfg: WhisperConfig):
        import torch
        from faster_whisper import WhisperModel

        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(
            f"[STT:whisper] Loading Faster-Whisper model '{cfg.model_name}' (device={device}, compute_type={cfg.compute_type})"
        )
        self.model = WhisperModel(cfg.model_name, device=device, compute_type=cfg.compute_type)

    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        segments, info = self.model.transcribe(
            audio_path,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )
        text = "".join([s.text for s in segments]).strip()
        return {
            "text": text,
            "language": getattr(info, "language", None),
            "language_probability": getattr(info, "language_probability", None),
        }
