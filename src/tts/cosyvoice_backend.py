import io
import base64
import logging
import os
from dataclasses import dataclass

import torchaudio

from src.tts.voice import get_voice_sample_path

logger = logging.getLogger(__name__)


@dataclass
class CosyVoiceConfig:
    # Either a local directory path containing cosyvoice3.yaml + weights,
    # or a HF repo id like FunAudioLLM/Fun-CosyVoice3-0.5B-2512
    model_dir: str


class CosyVoiceBackend:
    def __init__(self, cfg: CosyVoiceConfig):
        # Make CosyVoice repo importable
        import sys

        # new location after refactor
        sys.path.append("external/cosyvoice")
        sys.path.append("external/cosyvoice/third_party/Matcha-TTS")

        from cosyvoice.cli.cosyvoice import AutoModel

        model_dir = cfg.model_dir

        # CosyVoice upstream falls back to ModelScope if model_dir path does not exist.
        # We want HuggingFace, so if model_dir doesn't exist but looks like a HF repo id,
        # we download it to a local directory first.
        if not os.path.exists(model_dir) and "/" in model_dir and " " not in model_dir:
            from huggingface_hub import snapshot_download

            # Prefer persistent workspace storage on RunPod
            base_dir = "/workspace/models/cosyvoice" if os.path.isdir("/workspace") else "pretrained_models"
            local_dir = os.path.join(base_dir, model_dir.replace("/", "__"))

            logger.info(f"[CosyVoice] Downloading from HF: {model_dir} -> {local_dir}")
            snapshot_download(repo_id=model_dir, local_dir=local_dir)
            model_dir = local_dir

        logger.info(f"[CosyVoice] Loading AutoModel from '{model_dir}'")
        self.model = AutoModel(model_dir=model_dir)
        self.sample_rate = self.model.sample_rate

    def synthesize_base64(self, text: str, voice: str = "default") -> str:
        prompt_wav = get_voice_sample_path(voice)

        # Prompt text can be voice-specific
        prompt_text = None
        prompt_file = os.path.join(os.getenv("VOICES_DIR", "voices"), f"{voice}.prompt.txt")
        if voice and voice != "default" and os.path.exists(prompt_file):
            with open(prompt_file, "r", encoding="utf-8") as f:
                prompt_text = f.read().strip()
        if not prompt_text:
            prompt_text = os.getenv(
                "COSYVOICE_DEFAULT_PROMPT_TEXT",
                "You are a helpful assistant.<|endofprompt|>Hallo, hier spricht Jan.",
            )

        gen = self.model.inference_zero_shot(text, prompt_text, prompt_wav, stream=False)
        last = None
        for last in gen:
            pass
        if last is None or "tts_speech" not in last:
            raise RuntimeError("CosyVoice produced no output")

        audio = last["tts_speech"]
        if audio.dim() == 1:
            audio = audio.unsqueeze(0)

        buf = io.BytesIO()
        torchaudio.save(buf, audio.cpu(), self.sample_rate, format="wav")
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")
