import os
import io
import base64
import logging
from dataclasses import dataclass
from typing import Optional

import torch
import torchaudio

from src.tts.voice import get_voice_sample_path

logger = logging.getLogger(__name__)


@dataclass
class VibeVoiceConfig:
    model_name: str
    hf_token: Optional[str]


class VibeVoiceBackend:
    sample_rate: int = 24000

    def __init__(self, cfg: VibeVoiceConfig, device: str):
        # Import locally to avoid loading if unused
        # VibeVoice lives in external/vibevoice and is importable as package `vibevoice`.
        try:
            from vibevoice.modular.modeling_vibevoice_inference import (
                VibeVoiceForConditionalGenerationInference,
            )
            from vibevoice.processor.vibevoice_processor import VibeVoiceProcessor
        except ImportError:
            # Fallback: try importing from external/vibevoice directly
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'external'))
            from vibevoice.modular.modeling_vibevoice_inference import (
                VibeVoiceForConditionalGenerationInference,
            )
            from vibevoice.processor.vibevoice_processor import VibeVoiceProcessor

        self.device = device

        logger.info(f"[VibeVoice] Loading processor from {cfg.model_name}")
        self.processor = VibeVoiceProcessor.from_pretrained(cfg.model_name, token=cfg.hf_token)

        if device == "cuda":
            load_dtype = torch.bfloat16
            attn_impl = "flash_attention_2"
        else:
            load_dtype = torch.float32
            attn_impl = "sdpa"

        logger.info(f"[VibeVoice] Loading model with dtype={load_dtype}, attn={attn_impl}")

        try:
            self.model = VibeVoiceForConditionalGenerationInference.from_pretrained(
                cfg.model_name,
                torch_dtype=load_dtype,
                attn_implementation=attn_impl,
                device_map=device,
                token=cfg.hf_token,
            )
        except Exception as e:
            logger.warning(f"[VibeVoice] Failed to load with {attn_impl}, falling back to sdpa. Error: {e}")
            self.model = VibeVoiceForConditionalGenerationInference.from_pretrained(
                cfg.model_name,
                torch_dtype=load_dtype,
                attn_implementation="sdpa",
                device_map=device,
                token=cfg.hf_token,
            )

        self.model.eval()

    def synthesize_base64(self, text: str, voice: str = "default") -> str:
        voice_sample_path = get_voice_sample_path(voice)
        logger.info(f"[VibeVoice] Using voice sample: {voice_sample_path}")

        inputs = self.processor(
            text=[text],
            voice_samples=[[voice_sample_path]],
            padding=True,
            return_tensors="pt",
            return_attention_mask=True,
        )

        for k, v in inputs.items():
            if torch.is_tensor(v):
                inputs[k] = v.to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=None,
                cfg_scale=1.3,
                tokenizer=self.processor.tokenizer,
                generation_config={"do_sample": False},
                is_prefill=True,
            )

        if not hasattr(outputs, "speech_outputs") or outputs.speech_outputs is None:
            raise RuntimeError("VibeVoice generated no speech output")

        audio = outputs.speech_outputs[0].detach().cpu().to(torch.float32)
        if audio.dim() == 1:
            audio = audio.unsqueeze(0)

        buf = io.BytesIO()
        torchaudio.save(buf, audio, self.sample_rate, format="wav")
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")
