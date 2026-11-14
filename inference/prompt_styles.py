"""Prompt formats for our own models.

LitGPT reads `prompt_style.yaml` in the model folder, for example:

    class_path: inference.prompt_styles.FrRnChat

and uses the class below to wrap every question before generation.
"""

from litgpt.prompts import PromptStyle


class FrRnChat(PromptStyle):
    """Format used to train the French / Kirundi model (modele_train/train.py)."""

    def apply(self, prompt: str, *, sys_prompt: str | None = None, **kwargs) -> str:
        return f"<|user|> {prompt} <|assistant|>"
