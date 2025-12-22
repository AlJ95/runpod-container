import os
import re
import shlex
import subprocess
from urllib.parse import urlparse


def _download_gguf_to_workspace(url: str) -> str:
    """Download a GGUF file given a HF resolve URL.

    We keep this logic inside the runner (no separate download module), as requested.
    """
    from huggingface_hub import hf_hub_download

    # Example:
    # https://huggingface.co/unsloth/Qwen3-0.6B-GGUF/resolve/main/Qwen3-0.6B-UD-Q6_K_XL.gguf
    m = re.match(r"https?://huggingface\.co/([^/]+/[^/]+)/resolve/([^/]+)/(.+)", url)
    if not m:
        raise ValueError(
            "GGUF_MODEL_URL must be a HuggingFace resolve URL like: "
            "https://huggingface.co/<repo>/resolve/<rev>/<filename>.gguf"
        )

    repo_id, revision, filename = m.group(1), m.group(2), m.group(3)

    base_dir = "/workspace/models/gguf" if os.path.isdir("/workspace") else "models/gguf"
    os.makedirs(base_dir, exist_ok=True)

    local_path = hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        revision=revision,
        local_dir=base_dir,
        local_dir_use_symlinks=False,
    )
    return local_path


def main() -> None:
    host = os.getenv("HOST", "0.0.0.0")
    port = os.getenv("PORT", "8000")
    gpu_mem = os.getenv("GPU_MEMORY_UTILIZATION", "0.65")
    async_sched = os.getenv("ASYNC_SCHEDULING", "true").lower() == "true"

    vllm_model = os.getenv("VLLM_MODEL", "openai/gpt-oss-20b")
    gguf_url = os.getenv("GGUF_MODEL_URL", "").strip()

    # tokenizer can be specified via VLLM_TOKENIZER (preferred) or TOKENIZER_MODEL (legacy)
    tokenizer = os.getenv("VLLM_TOKENIZER") or os.getenv("TOKENIZER_MODEL")

    extra_args = os.getenv("EXTRA_VLLM_ARGS", "")

    if gguf_url:
        vllm_model = _download_gguf_to_workspace(gguf_url)

    cmd = ["vllm", "serve", vllm_model, "--host", host, "--port", str(port), "--gpu-memory-utilization", str(gpu_mem)]

    if tokenizer:
        cmd += ["--tokenizer", tokenizer]

    if async_sched:
        cmd += ["--async-scheduling"]

    if extra_args:
        cmd += shlex.split(extra_args)

    # Exec as foreground process
    os.execvp(cmd[0], cmd)


if __name__ == "__main__":
    main()
