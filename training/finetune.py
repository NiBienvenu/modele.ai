"""Fine-tune the model of `.env` on your own documents dataset.

This is a thin layer over LitGPT's fine-tuning scripts: it fills the paths
from the platform settings (models/, datasets/, checkpoints/) and keeps
every LitGPT option available.

Methods:
    lora   -> light training, small GPU memory (recommended to start)
    qlora  -> LoRA on a 4-bit model (bnb.nf4), for small GPUs
    full   -> trains all weights, needs a lot of GPU memory

Usage:
    python -m training.finetune --method lora --dataset datasets/exemple_instructions.json --name juridique-v1
    python -m training.finetune --method qlora --dataset datasets/lois.json --name lois-v1 --epochs 3

The result lands in checkpoints/<name>/final. To use it for inference,
set MODEL_PATH to that folder (after `litgpt merge_lora` for LoRA/QLoRA).
"""

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path

from config.logging_setup import setup_logging
from config.settings import Settings, get_settings

logger = logging.getLogger(__name__)

METHODS = ("lora", "qlora", "full")


@dataclass(frozen=True)
class FinetuneRequest:
    """Everything needed to start one fine-tuning run."""

    method: str
    dataset: Path
    name: str
    epochs: int
    val_split_fraction: float


def build_data_module(request: FinetuneRequest):
    """Instruction dataset in JSON: [{"instruction": ..., "input": ..., "output": ...}]."""
    from litgpt.data import JSON

    return JSON(json_path=request.dataset, val_split_fraction=request.val_split_fraction)


def build_train_args(request: FinetuneRequest):
    from litgpt.args import TrainArgs

    return TrainArgs(
        save_interval=1000,
        log_interval=1,
        global_batch_size=16,
        micro_batch_size=1,
        lr_warmup_steps=10,
        epochs=request.epochs,
    )


def run_finetune(request: FinetuneRequest, settings: Settings) -> Path:
    """Start the LitGPT fine-tuning and return the output folder."""
    out_dir = settings.paths.checkpoints_dir / request.name
    common = dict(
        checkpoint_dir=settings.model.path,
        out_dir=out_dir,
        data=build_data_module(request),
        train=build_train_args(request),
    )
    logger.info("Fine-tuning (%s) %s on %s -> %s", request.method, settings.model.path, request.dataset, out_dir)

    if request.method == "full":
        from litgpt.finetune.full import setup

        setup(**common)
    else:
        from litgpt.finetune.lora import setup

        quantize = "bnb.nf4" if request.method == "qlora" else None
        precision = "bf16-true" if request.method == "qlora" else None
        setup(**common, quantize=quantize, precision=precision)
    return out_dir


def parse_args() -> FinetuneRequest:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--method", choices=METHODS, default="lora")
    parser.add_argument("--dataset", type=Path, required=True, help="JSON file of instruction/output pairs")
    parser.add_argument("--name", required=True, help="Name of the run, used as folder in checkpoints/")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--val-split-fraction", type=float, default=0.1)
    args = parser.parse_args()
    return FinetuneRequest(args.method, args.dataset, args.name, args.epochs, args.val_split_fraction)


def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level, settings.paths.logs_dir, "training.log")
    out_dir = run_finetune(parse_args(), settings)
    logger.info("Done. Weights saved in %s", out_dir)


if __name__ == "__main__":
    main()
