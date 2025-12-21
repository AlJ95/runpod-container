import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class MoonshineConfig:
    model_name: str
    device: Optional[str] = None


class MoonshineBackend:
    def __init__(self, cfg: MoonshineConfig):
        import torch
        from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq

        self.device = cfg.device or ("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"[STT:moonshine] Loading processor/model '{cfg.model_name}' on {self.device}")

        self.processor = AutoProcessor.from_pretrained(cfg.model_name)
        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(cfg.model_name)
        self.model.to(self.device)
        self.model.eval()

    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        import torch
        import librosa

        audio_input, _ = librosa.load(audio_path, sr=16000)
        inputs = self.processor(audio_input, sampling_rate=16000, return_tensors="pt")
        inputs = {k: v.to(self.device) if torch.is_tensor(v) else v for k, v in inputs.items()}

        with torch.no_grad():
            generated_ids = self.model.generate(**inputs)

        text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
        return {
            "text": text,
            "language": "de",
            "language_probability": 1.0,
        }
