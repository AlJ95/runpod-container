import os

VOICES_DIR = os.getenv("VOICES_DIR", "voices")
DEFAULT_VOICE_PATH = os.getenv("DEFAULT_VOICE_PATH", os.path.join(VOICES_DIR, "de-jan_man.wav"))


def get_voice_sample_path(voice_name: str = "default") -> str:
    """Resolve a voice reference name to an existing .wav file path."""
    if voice_name and voice_name != "default":
        voice_path = os.path.join(VOICES_DIR, f"{voice_name}.wav")
        if os.path.exists(voice_path):
            return voice_path

    if os.path.exists(DEFAULT_VOICE_PATH):
        return DEFAULT_VOICE_PATH

    if os.path.exists(VOICES_DIR):
        wav_files = [f for f in os.listdir(VOICES_DIR) if f.endswith(".wav")]
        if wav_files:
            return os.path.join(VOICES_DIR, wav_files[0])

    raise RuntimeError(f"No voice samples found. Expected .wav files in {VOICES_DIR}/")
