"""Find, download and load a model with LitGPT.

This is the only file of the platform that knows how LitGPT loads weights.
If one day we support several models or another engine, only this file
(and engine.py) need to change.
"""

import logging
from pathlib import Path

from config.settings import ModelSettings

logger = logging.getLogger(__name__)

# File created by LitGPT when HuggingFace weights are converted
LITGPT_WEIGHTS_FILE = "lit_model.pth"


def is_model_ready(model_path: Path) -> bool:
    """True if the folder holds converted LitGPT weights."""
    return (model_path / LITGPT_WEIGHTS_FILE).is_file()


def download_model(settings: ModelSettings) -> None:
    """Download MODEL_NAME from HuggingFace and convert it to the LitGPT format.

    LitGPT saves into <checkpoint_dir>/<org>/<name>, so we pass the parent
    folder that matches MODEL_PATH.
    """
    from litgpt.scripts.download import download_from_hub

    checkpoint_dir = _download_root_for(settings)
    logger.info("Downloading %s into %s", settings.name, checkpoint_dir)
    download_from_hub(repo_id=settings.name, access_token=settings.hf_token, checkpoint_dir=checkpoint_dir)


def _download_root_for(settings: ModelSettings) -> Path:
    """MODEL_PATH = <root>/<org>/<name>  ->  return <root>."""
    parts_in_name = len(Path(settings.name).parts)
    root = settings.path
    for _ in range(parts_in_name):
        root = root.parent
    if root / settings.name != settings.path:
        raise ValueError(
            f"Cannot auto-download: MODEL_PATH ({settings.path}) must end with MODEL_NAME ({settings.name}). "
            "Download the model manually or empty MODEL_PATH."
        )
    return root


def ensure_model_available(settings: ModelSettings) -> None:
    """Make sure the weights are on disk, downloading them if allowed."""
    if is_model_ready(settings.path):
        return
    if not settings.auto_download:
        raise FileNotFoundError(
            f"No LitGPT weights in {settings.path}. Run `python scripts/download_model.py` or set AUTO_DOWNLOAD=true."
        )
    download_model(settings)


def load_llm(settings: ModelSettings):
    """Load the model on the configured device and return a `litgpt.LLM`."""
    from litgpt import LLM

    ensure_model_available(settings)
    logger.info("Loading model from %s (device=%s, quantize=%s)", settings.path, settings.device, settings.quantize)

    # distribute=None lets us choose device, precision and quantization ourselves
    llm = LLM.load(str(settings.path), tokenizer_dir=settings.tokenizer_path, distribute=None)
    llm.distribute(
        accelerator=settings.device,
        devices=settings.devices,
        precision=settings.precision,
        quantize=settings.quantize,
        # Several GPUs: split the layers across them so bigger models fit
        generate_strategy="sequential" if settings.devices > 1 else None,
    )
    return llm
