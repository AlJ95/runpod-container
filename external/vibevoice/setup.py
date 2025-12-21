from setuptools import setup, find_packages

setup(
    name="vibevoice",
    version="0.1.0",
    description="VibeVoice TTS Model",
    packages=find_packages(),
    install_requires=[
        "torch",
        "transformers>=4.41.0",
        "diffusers>=0.27.0",
        "soundfile",
        "librosa",
        "accelerate",
    ],
    python_requires=">=3.8",
)
