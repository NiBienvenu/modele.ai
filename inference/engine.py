"""Inference engine: turns a prompt into an answer.

`InferenceEngine` is the contract used by the rest of the platform.
`LitGPTEngine` is the real implementation on top of LitGPT.
Tests (or a future second engine) can provide another implementation.
"""

import logging
import time
from typing import Protocol

from config.settings import ModelSettings
from inference.model_loader import load_llm
from inference.schemas import GenerationParams, GenerationResult

logger = logging.getLogger(__name__)


class InferenceEngine(Protocol):
    """Anything able to load a model and generate text."""

    def load(self) -> None: ...

    def generate(self, prompt: str, params: GenerationParams) -> GenerationResult: ...


class LitGPTEngine:
    """Engine backed by `litgpt.LLM`. Not thread-safe: call it from one thread only."""

    def __init__(self, settings: ModelSettings) -> None:
        self._settings = settings
        self._llm = None  # Loaded lazily by load(), heavy object

    @property
    def is_loaded(self) -> bool:
        return self._llm is not None

    def load(self) -> None:
        """Load the weights in memory (can take a while the first time)."""
        if not self.is_loaded:
            self._llm = load_llm(self._settings)

    def generate(self, prompt: str, params: GenerationParams) -> GenerationResult:
        """Generate an answer and measure its cost."""
        self.load()
        start = time.perf_counter()
        token_ids = self._llm.generate(
            prompt,
            sys_prompt=params.system_prompt,
            max_new_tokens=params.max_new_tokens,
            temperature=params.temperature,
            top_k=params.top_k,
            top_p=params.top_p,
            return_as_token_ids=True,  # Lets us count tokens before decoding
        )
        elapsed = time.perf_counter() - start
        text = self._llm.preprocessor.decode(token_ids).strip()
        logger.info("Generated %d tokens in %.2fs", token_ids.numel(), elapsed)
        return GenerationResult(text=text, tokens=int(token_ids.numel()), elapsed_time=round(elapsed, 3))
