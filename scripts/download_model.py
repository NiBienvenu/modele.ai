"""Download the model set in `.env` (MODEL_NAME) into `models/`.

Usage:
    python scripts/download_model.py
    python scripts/download_model.py --model microsoft/phi-2   # other model, same folder logic
"""

import argparse
import dataclasses
import sys
from pathlib import Path

# Allow running the script without installing the project
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import get_settings  # noqa: E402
from inference.model_loader import download_model, is_model_ready  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", help="HuggingFace repo id (default: MODEL_NAME from .env)")
    args = parser.parse_args()

    settings = get_settings()
    model = settings.model
    if args.model:
        model = dataclasses.replace(model, name=args.model, path=settings.paths.models_dir / args.model)

    if is_model_ready(model.path):
        print(f"Already downloaded: {model.path}")
        return
    download_model(model)
    print(f"Model ready in {model.path}")


if __name__ == "__main__":
    main()
