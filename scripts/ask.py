"""Ask one question to the model from the terminal, without the API.

Handy to check that the model, the GPU and the `.env` settings work.

Usage:
    python scripts/ask.py "Qu'est-ce qu'un décret ?"
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import get_settings  # noqa: E402
from inference.engine import LitGPTEngine  # noqa: E402
from inference.factory import default_generation_params  # noqa: E402


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    settings = get_settings()
    engine = LitGPTEngine(settings.model)
    result = engine.generate(" ".join(sys.argv[1:]), default_generation_params(settings))
    print(result.text)
    print(f"\n--- {result.tokens} tokens en {result.elapsed_time}s")


if __name__ == "__main__":
    main()
